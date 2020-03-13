import click
import configparser
import datetime
import enum
import logging
import logging.config
import mega
import multiprocessing
import os
import queue
import threading
import time
import typing
import uuid

from megadloader import (
    suppress_errors,
    threadlocal,
    MEGA_API_KEY,
)
from megadloader.db import Db, configure_db
from megadloader.models import File, Url, UrlStatus

MegaHandle = int


@click.command()
@click.option('--processor-id')
@click.option('--config', default='app.ini', type=click.Path(exists=True, dir_okay=False))
@click.option('--app-name', default='main')
def cli(processor_id, config, app_name):
    logging.config.fileConfig(config)

    if processor_id is None:
        processor_id = str(uuid.uuid4())

    parser = configparser.ConfigParser()
    parser.read(config)

    settings = parser[f'app:{app_name}']
    destination = settings['destination']

    configure_db(settings)

    processor = DownloadProcessor(destination, processor_id)

    try:
        processor.run()
    except KeyboardInterrupt:
        pass


class NodeWrapper:
    def __init__(
        self, node_id: uuid.UUID, path: str, file_node: mega.MegaNode,
        file_model: File,
    ):
        self.node_id = node_id
        self.path = path
        self.file_model = file_model
        self.file_node = file_node


class ProcessorStatus(enum.Enum):
    IDLE = 'idle'
    REAPING = 'reaping'
    SCANNING = 'scanning'
    INDEXING = 'indexing'
    DOWNLOADING = 'downloading'


def set_processor_status(status):
    def wrapper(func):
        def inner(self, *args, **kwargs):
            self.status = status

            try:
                return func(self, *args, **kwargs)
            finally:
                self.status = ProcessorStatus.IDLE

        return inner

    return wrapper


class DownloadProcessor(multiprocessing.Process):
        super().__init__(name='DownloadQueueProcessor', daemon=False)

        self.api = mega.MegaApi('vIJE2YwK')
        self.destination = destination
        self.event = threading.Event()
        self.log = logging.getLogger('processor')
        self.status = ProcessorStatus.IDLE
        self.processor_id = processor_id
        self._updates = queue.Queue()

        self.current_file_id = None
        self._files: typing.List[NodeWrapper] = []

    @property
    @threadlocal
    def db(self):
        return Db()

    def get_files(self) -> typing.List[NodeWrapper]:
        return self._files

    def run(self):
        self.status = ProcessorStatus.SCANNING

        self._clean_broken_transfers()
        self._verify_files()

        self.status = ProcessorStatus.IDLE

        while not self.event.is_set():
            try:
                did_work = self._loop()
                if not did_work:
                    self.log.info('sleeping ... ')
                    time.sleep(.1)
                    continue

            except Exception:
                self.log.error(f"PROCESSOR ERROR:")
                time.sleep(1)

        self.db.dispose()

    @set_processor_status(ProcessorStatus.REAPING)
    def _clean_broken_transfers(self):
        self.log.info('start cleaning broken transfers')

        for root, dirname, files in os.walk(self.destination):
            for file in files:
                if file.endswith('.mega'):
                    if file.startswith('.getxfer.'):
                        os.unlink(os.path.join(root, file))

        self.log.info('cleaning done')

    @set_processor_status(ProcessorStatus.SCANNING)
    def _verify_files(self):
        self.log.info('verifying files')

        for url in self.db.get_urls():
            done = True

            for file in url.files:
                full_path = os.path.join(self.destination, file.path)
                if os.path.exists(full_path):
                    continue

                print(f'--- resetting file {file.path}')
                self.db.reset_file(file)
                done = False

            if not done:
                print(f'--- resetting url {url.url} ---')
                self.db.update_url(url, self.processor_id, UrlStatus.idle)

        self.log.info('done verifying files')

    def _loop(self):
        self.log.info('looping through files')

        if self._files:
            file = self._files.pop(0)
            self.current_file_id = file.file_model.id
            self._download_file(file)
            file.current_file_id = None

            if not self._files:
                self.db.update_url(
                    self.current_url, self.processor_id, UrlStatus.done,
                )
                self.current_url = None
            return True

        self.current_url = self.db.get_next_url()
        if self.current_url:
            self._process_url(self.current_url)
            return True

        return False

    def stop(self):
        listener = LogListener('logout')
        self.api.logout(listener)
        listener.wait()

        self.event.set()

    def _handle_listener_error(self, url_model, listener):
        if listener.error is not None:
            self.log.warning(f'got an error: {listener.error}')

            self.db.update_url(
                url_model, self.processor_id, UrlStatus.error,
                str(listener.error),
            )
            return True

        return False

    @set_processor_status(ProcessorStatus.INDEXING)
    @suppress_errors
    def _process_url(self, url_model):
        self.log.info('processing url ...')
        self.db.update_url(url_model, self.processor_id, UrlStatus.processing)

        processor = UrlProcessor(self.api)
        results = processor.process(url_model.url)
        for fname, node in results:
            self._process_file_node(url_model, node, fname)

    def _process_file_node(self, url_model, node: mega.MegaNode, fname):
        if url_model.category:
            fname = os.path.join(url_model.category, fname)
        fname = os.path.join(self.destination, fname)

        file_model = self.db.create_file(url_model, node, fname)
        wrapper = NodeWrapper(uuid.uuid4(), fname, node, file_model)
        self._files.append(wrapper)

    @set_processor_status(ProcessorStatus.DOWNLOADING)
    @suppress_errors
    def _download_file(self, wrapper: NodeWrapper):
        if wrapper.file_model.is_finished:
            self.log.info(f'finished with {wrapper.file_model.path}')
            return

        self.db.mark_file_status(wrapper.file_model.id, True)

        file_listener = DbFileListener(wrapper.file_model.id, self)
        downloader = FileNodeDownloader(self.api)
        downloader.download(wrapper.path, wrapper.file_node, file_listener)

        file_listener.wait()

        self.db.mark_file_status(wrapper.file_model.id, False)
        self.log.info('done downloading file')


SECONDS_IN_MINUTE = 60
MINUTES_IN_HOUR = 60
HOURS_IN_DAY = 24
SECONDS_IN_HOUR = MINUTES_IN_HOUR * SECONDS_IN_MINUTE
SECONDS_IN_DAY = HOURS_IN_DAY * SECONDS_IN_HOUR


def _format_delta(diff: datetime.timedelta):
    diff = int(diff.total_seconds())
    d, remainder = divmod(diff, SECONDS_IN_DAY)
    h, remainder = divmod(diff, SECONDS_IN_HOUR)
    m, s = divmod(remainder, SECONDS_IN_MINUTE)

    if d > 0:
        return f'{d}d {h}h {m}m {s}s'

    if h > 0:
        return f'{h}h {m}m {s}s'

    if m > 0:
        return f'{m}m {s}s'

    return str(s) + 's'


class ProgressTimer:
    def __init__(self, total):
        self.total = total
        self._completed = 0
        self._start = time.time()

    def progress(self, completed):
        if completed == 0:
            return

        self._completed = completed

        elapsed = time.time() - self._start
        elapsed_per = elapsed / self._completed
        total_time = elapsed_per * self.total
        remaining_time = total_time - elapsed

        total = datetime.timedelta(seconds=total_time)
        elapsed = datetime.timedelta(seconds=elapsed)
        remaining = datetime.timedelta(seconds=remaining_time)
        progress = map(_format_delta, (elapsed, remaining, total))
        progress = ' / '.join(progress)

        click.echo(f'{self._completed}/{self.total} ({progress})')


class FileListener(mega.MegaTransferListener):
    def __init__(self):
        self._vars = threading.local()
        self.transfer_info = None
        self.event = threading.Event()

        super().__init__()

    def _update(self, transfer: typing.Optional[mega.MegaTransfer]):
        self.transfer_info = transfer

    @suppress_errors
    def onTransferStart(
        self, api: mega.MegaApi,
        transfer: mega.MegaTransfer,
    ):
        self.transfer_info = transfer

    @suppress_errors
    def onTransferFinish(
        self, api: mega.MegaApi,
        transfer: mega.MegaTransfer, error: mega.MegaError,
    ):
        self._update(transfer)
        self.event.set()

    @suppress_errors
    def onTransferUpdate(self, api: mega.MegaApi, transfer: mega.MegaTransfer):
        self._update(transfer)

    @suppress_errors
    def onTransferTemporaryError(
        self, api: mega.MegaApi, transfer: mega.MegaTransfer,
        error: mega.MegaError,
    ):
        pass

    @suppress_errors
    def onTransferData(
        self, api: mega.MegaApi, transfer: mega.MegaTransfer,
        buffer: str, size: int,
    ) -> bool:
        return True

    def wait(self, timeout):
        return self.event.wait(timeout)


class LogListener(mega.MegaRequestListener):
    def __init__(self, prefix):
        super().__init__()

        self.prefix = prefix
        self.event = threading.Event()
        self.error: typing.Optional[mega.MegaError] = None

    def onRequestStart(self, api: mega.MegaApi, request: mega.MegaRequest):
        print(f'{self.prefix} onRequestStart: {request}')

    def onRequestFinish(
        self, api: mega.MegaApi, request: mega.MegaRequest, e: mega.MegaError,
    ):
        print(f'{self.prefix} onRequestFinish {request} {e}')
        if e and e.getValue() != e.API_OK:
            self.error = e
        self.event.set()

    def onRequestTemporaryError(
        self, api: mega.MegaApi,
        request: mega.MegaRequest,
        error: mega.MegaError,
    ):
        print(f'{self.prefix} onRequestTemporaryError {request} {error}')

    def onRequestUpdate(self, api: mega.MegaApi, request: mega.MegaRequest):
        print(f'{self.prefix} onRequestUpdate {request}')

    def wait(self):
        self.event.wait()


class PublicFolderListener(LogListener):
    public_node = None

    @suppress_errors
    def onRequestFinish(
        self, api: mega.MegaApi, request: mega.MegaRequest, e: mega.MegaError,
    ):
        if e is None or e.getValue() == e.API_OK:
            self.public_node = request.getPublicMegaNode()

        super().onRequestFinish(api, request, e)


class UrlProcessor:
    def __init__(self, api: mega.MegaApi):
        self.api = api

    def _is_file(self, url: str):
        index = url.index('#')
        if index == -1:
            return False

        return url[index + 1] != 'F'

    def _handle_listener_error(self, url, listener):
        if listener.error is not None:
            raise Exception(url, str(listener.error))

    def process(self, url) -> list:
        directories = tuple()

        if self._is_file(url):
            yield self._process_file(url, directories)
        else:
            yield from self._process_folder(url)

    def _process_file(self, url, directories):
        listener = PublicFolderListener(
            f'getPublicNode("{url}")',
        )
        self.api.getPublicNode(url, listener)
        listener.wait()
        self._handle_listener_error(url, listener)

        return self._process_file_node(listener.public_node, directories)

    def _process_file_node(self, node, directories):
        fname = os.path.join(
            *directories,
            node.getName(),
        )
        return fname, node

    def _process_folder(self, url):
        listener = LogListener(f'loginToFolder("{url}")')
        self.api.loginToFolder(url, listener)
        listener.wait()
        self._handle_listener_error(url, listener)

        listener = LogListener('fetch nodes')
        self.api.fetchNodes(listener)
        listener.wait()
        self._handle_listener_error(url, listener)

        dir_node = self.api.getRootNode()

        yield from self._process_folder_node(dir_node, [])

    def _process_folder_node(self, dir_node, directories):
        directories = [*directories, dir_node.getName()]

        lists: mega.MegaChildrenLists = \
            self.api.getFileFolderChildren(dir_node)

        files: mega.MegaNodeList = lists.getFileList()
        for index in range(files.size()):
            file_node: mega.MegaNode = files.get(index)
            yield self._process_file_node(file_node, directories)

        folders: mega.MegaNodeList = lists.getFolderList()
        for index in range(folders.size()):
            folder: mega.MegaNode = folders.get(index)
            yield from self._process_folder_node(folder, directories)


class FileNodeDownloader:
    def __init__(self, api):
        self.api = api

    def download(self, fname, file_node, listener: mega.MegaTransferListener):
        os.makedirs(
            os.path.dirname(fname),
            exist_ok=True,
        )

        print(f'downloading {fname}')
        self.api.startDownload(file_node, localPath=fname, listener=listener)
        print(f'\tdone')
