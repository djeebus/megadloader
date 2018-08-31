import enum

import mega
import os
import threading
import time
import typing
import uuid

from megadloader import suppress_errors, threadlocal
from megadloader.db import Db
from megadloader.models import File, Url, UrlStatus

MegaHandle = int


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


def set_status(status):
    def wrapper(func):
        def inner(self, *args, **kwargs):
            self.status = status

            try:
                return func(self, *args, **kwargs)
            finally:
                self.status = ProcessorStatus.IDLE

        return inner

    return wrapper


class DownloadProcessor(threading.Thread):
    def __init__(self, destination, processor_id):
        super().__init__(name='DownloadQueueProcessor', daemon=False)

        self.api = mega.MegaApi('vIJE2YwK')
        self.destination = destination
        self.event = threading.Event()
        self.status = ProcessorStatus.IDLE
        self.processor_id = processor_id

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
                    time.sleep(.1)
            except Exception as e:
                print(f"PROCESSOR ERROR: {e}")
                time.sleep(1)

        self.db.dispose()

    @set_status(ProcessorStatus.REAPING)
    def _clean_broken_transfers(self):
        for root, dir, files in os.walk(self.destination):
            for file in files:
                if file.endswith('.mega'):
                    if file.startswith('.getxfer.'):
                        os.unlink(os.path.join(root, file))

    @set_status(ProcessorStatus.SCANNING)
    def _verify_files(self):
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

    def _loop(self):
        if self._files:
            file = self._files.pop(0)
            file.current_file_id = file.file_model.id
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

    @set_status(ProcessorStatus.INDEXING)
    @suppress_errors
    def _process_url(self, url_model):
        self.db.update_url(url_model, self.processor_id, UrlStatus.processing)

        listener = LogListener(f'loginToFolder("{url_model.url}")')
        self.api.loginToFolder(url_model.url, listener)
        listener.wait()

        if listener.error is not None:
            self.db.update_url(
                url_model, self.processor_id, UrlStatus.error,
                str(listener.error),
            )
            return

        listener = LogListener('fetch nodes')
        self.api.fetchNodes(listener)
        listener.wait()

        root_node = self.api.getRootNode()

        dirs = (url_model.category,) if url_model.category else tuple()
        self._find_files(url_model, root_node, *dirs)

    @set_status(ProcessorStatus.DOWNLOADING)
    @suppress_errors
    def _download_file(self, wrapper: NodeWrapper):
        if wrapper.file_model.is_finished:
            print(f'finished with {wrapper.file_model.path}')
            return

        fpath = os.path.dirname(wrapper.path)
        os.makedirs(fpath, exist_ok=True)

        file_listener = FileListener(wrapper.file_model.id, self)

        self.db.mark_file_status(wrapper.file_model, True)

        self.api.startDownload(
            wrapper.file_node, localPath=wrapper.path, listener=file_listener,
        )
        file_listener.wait()

        self.db.mark_file_status(wrapper.file_model, False)

    def _find_files(self, url_model: Url, node, *directories):
        curdir = node.getName()

        lists: mega.MegaChildrenLists = self.api.getFileFolderChildren(node)

        files: mega.MegaNodeList = lists.getFileList()
        for index in range(files.size()):
            file_node: mega.MegaNode = files.get(index)
            fname = os.path.join(
                self.destination,
                *directories,
                curdir,
                file_node.getName(),
            )

            file_model = self.db.create_file(url_model, file_node, fname)
            wrapper = NodeWrapper(uuid.uuid4(), fname, file_node, file_model)
            self._files.append(wrapper)

        folders: mega.MegaNodeList = lists.getFolderList()
        for index in range(folders.size()):
            folder: mega.MegaNode = folders.get(index)
            self._find_files(url_model, folder, *directories, curdir)


class FileListener(mega.MegaTransferListener):
    def __init__(
        self, file_model_id, queue: DownloadProcessor,
    ):
        self._vars = threading.local()
        self.file_model_id = file_model_id

        self.event = threading.Event()
        self.queue = queue

        super().__init__()

    @property
    @threadlocal
    def db(self):
        return Db()

    @property
    @threadlocal
    def file_model(self):
        return self.db.get_file(self.file_model_id)

    def _update(self, transfer: typing.Optional[mega.MegaTransfer]):
        self.db.update_file_node(self.file_model, transfer)

    @suppress_errors
    def onTransferStart(
        self, api: mega.MegaApi,
        transfer: mega.MegaTransfer,
    ):
        self._update(transfer)

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

    def wait(self):
        self.event.wait()


class LogListener(mega.MegaRequestListener):
    def __init__(self, prefix):
        super().__init__()

        self.prefix = prefix
        self.event = threading.Event()
        self.error: mega.MegaError = None

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
