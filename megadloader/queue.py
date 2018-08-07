import mega
import os
import threading
import time

from megadloader import suppress_errors


class DownloadQueue(threading.Thread):
    def __init__(self, destination):
        super().__init__(name='DownloadQueueProcessor', daemon=False)

        self.api = mega.MegaApi('vIJE2YwK')
        self.destination = destination
        self.event = threading.Event()
        self.urls = []
        self.status = 'idle'
        self.files = []

    def enqueue(self, url):
        self.urls.append(url)

    def run(self):
        print('begin queue runner')
        while not self.event.is_set():
            try:
                url = self.urls.pop(0)
                print('got a url!')
                self._process_url(url)
                continue
            except IndexError:
                print('no urls')

            try:
                file, fname = self.files.pop(0)
                print('got a node')
                self._download_file(file, fname)
                continue
            except IndexError:
                print('no nodes')

            time.sleep(.1)

        print('queue runner done')

    def stop(self):
        self.event.set()

    @suppress_errors
    def _process_url(self, url):
        listener = LogListener('login to folder')
        self.api.loginToFolder(url, listener)
        listener.wait()

        listener = LogListener('fetch nodes')
        self.api.fetchNodes(listener)
        listener.wait()

        root_node = self.api.getRootNode()

        self._find_files(root_node)

    @suppress_errors
    def _download_file(self, file, fname):
        fpath = os.path.dirname(fname)
        os.makedirs(fpath, exist_ok=True)

        file_listener = FileListener(f'download {fname}', self)
        self.api.startDownload(file, localPath=fname, listener=file_listener)
        file_listener.wait()

    def _find_files(self, node, *directories):
        curdir = node.getName()

        lists: mega.MegaChildrenLists = self.api.getFileFolderChildren(node)

        files: mega.MegaNodeList = lists.getFileList()
        for index in range(files.size()):
            file: mega.MegaNode = files.get(index)
            fname = os.path.join(self.destination, *directories, curdir, file.getName())
            self.files.append((file, fname))

        folders: mega.MegaNodeList = lists.getFolderList()
        for index in range(folders.size()):
            folder: mega.MegaNode = folders.get(index)
            self._find_files(folder, *directories, curdir)


class FileListener(mega.MegaTransferListener):
    def __init__(self, prefix, queue: DownloadQueue):
        self.event = threading.Event()
        self.prefix = prefix
        self.queue = queue

        super().__init__()

    def _update(self, transfer: mega.MegaTransfer):
        if transfer is None:
            self.queue.status = 'idle'
        else:
            self.queue.status = f'{transfer.getFileName()} | {transfer.getTransferredBytes()} / {transfer.getTotalBytes()}'

    def onTransferStart(self, api: mega.MegaApi, transfer: mega.MegaTransfer):
        print('onTransferStart')
        self._update(transfer)

    def onTransferFinish(self, api: mega.MegaApi, transfer: mega.MegaTransfer, error: mega.MegaError):
        print(f'onTransferFinish: {error}')
        self._update(None)
        self.event.set()

    def onTransferUpdate(self, api: mega.MegaApi, transfer: mega.MegaTransfer):
        print('onTransferUpdate')
        self._update(transfer)

    def onTransferTemporaryError(self, api: mega.MegaApi, transfer: mega.MegaTransfer, error: mega.MegaError):
        print(f'onTransferTemporaryError: {error}')

    def onTransferData(self, api: mega.MegaApi, transfer: mega.MegaTransfer, buffer: str, size: int) -> bool:
        print('onTransferData')
        return True

    def wait(self):
        self.event.wait()


class LogListener(mega.MegaRequestListener):
    def __init__(self, prefix):
        super().__init__()

        self.prefix = prefix
        self.event = threading.Event()

    def onRequestStart(self, api: mega.MegaApi, request: mega.MegaRequest):
        print(f'{self.prefix} onRequestStart: {request}')

    def onRequestFinish(self, api: mega.MegaApi, request: mega.MegaRequest, e: mega.MegaError):
        print(f'{self.prefix} onRequestFinish {request} {e}')
        self.event.set()

    def onRequestTemporaryError(self, api: mega.MegaApi, request: mega.MegaRequest, error: mega.MegaError):
        print(f'{self.prefix} onRequestTemporaryError {request} {error}')

    def onRequestUpdate(self, api: mega.MegaApi, request: mega.MegaRequest):
        print(f'{self.prefix} onRequestUpdate {request}')

    def wait(self):
        self.event.wait()
