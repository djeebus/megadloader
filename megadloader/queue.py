import mega
import os
import threading
import time


class DownloadQueue(threading.Thread):
    def __init__(self, destination):
        super().__init__(name='DownloadQueueProcessor', daemon=False)

        self.api = mega.MegaApi('vIJE2YwK')
        self.destination = destination
        self.event = threading.Event()
        self.queue = []
        self.status = 'idle'
        self._files = []

    def run(self):
        print('begin queue runner')
        while not self.event.is_set():
            try:
                url = self.queue.pop(0)
            except IndexError:
                time.sleep(.1)
                continue

            print('got a url!')
            try:
                print('processing ... ')
                self._process(url)
            except Exception as e:
                print(f'error! {e}')
        print('queue runner done')

    def stop(self):
        self.event.set()

    def _process(self, url):
        listener = LogListener('login to folder')
        self.api.loginToFolder(url, listener)
        listener.wait()

        listener = LogListener('fetch nodes')
        self.api.fetchNodes(listener)
        listener.wait()

        root_node = self.api.getRootNode()

        self._find_files(root_node)

        for file, fname in self._files:
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
            self._files.append((file, fname))

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
        self._update(transfer)

    def onTransferFinish(self, api: mega.MegaApi, transfer: mega.MegaTransfer, error: mega.MegaError):
        self._update(None)
        self.event.set()

    def onTransferUpdate(self, api: mega.MegaApi, transfer: mega.MegaTransfer):
        self._update(transfer)

    def onTransferTemporaryError(self, api: mega.MegaApi, transfer: mega.MegaTransfer, error: mega.MegaError):
        pass

    def onTransferData(self, api: mega.MegaApi, transfer: mega.MegaTransfer, buffer: str, size: int) -> bool:
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
