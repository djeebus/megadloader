import logging
import mega
import sqlalchemy
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import typing

from megadloader.models import Base, Url, UrlStatus, File, Category

DBSession = sqlalchemy.orm.scoped_session(
    sqlalchemy.orm.sessionmaker(),
)


def configure_db(settings):
    engine = sqlalchemy.engine_from_config(settings, 'db.')

    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all()


class Db:
    def __init__(self):
        self.log = logging.getLogger('db')
        self.session = DBSession()

    def add_url(self, url, category=None) -> Url:
        model = self.session.query(Url).filter(Url.url == url).first()
        if model is not None:
            return model

        self.log.info(f'creating url {url} @ {category}')
        model = Url(url=url, category=category)
        self.session.add(model)
        self.session.commit()
        return model

    def get_next_url(self) -> typing.Optional[Url]:
        url = self.session.query(Url) \
            .filter(Url.status.in_([
                UrlStatus.idle.value,
                UrlStatus.processing.value,
            ])) \
            .first()
        if not url:
            return

        return url

    def get_url(self, url_id) -> Url:
        url = self.session.query(Url).get(url_id)
        if url:
            return url

    def get_urls(self) -> typing.List[Url]:
        urls = self.session.query(Url).all()
        return urls

    def delete_url(self, url_model: Url):
        for file in url_model.files:
            self.session.delete(file)

        self.session.delete(url_model)
        self.session.commit()

    def update_url(
        self, url_model: Url, processor_id, status: UrlStatus, error_msg=None,
    ):
        url_model.processor_id = processor_id
        url_model.status = status.value
        url_model.message = error_msg

        self.session.commit()

    def dispose(self):
        self.session.close()

    def create_file(self, url_model: Url, file_node: mega.MegaNode, fname):
        file_handle = file_node.getBase64Handle()
        files = self.session.query(File) \
            .filter(File.file_handle == file_handle) \
            .filter(File.url_id == url_model.id)
        for file in files:
            return file

        self.log.info(f'creating file from {fname}')
        file_model = File(
            url_id=url_model.id,
            path=fname,
            total_bytes=file_node.getSize(),
            file_handle=file_handle,
        )

        self.session.add(file_model)
        self.session.commit()
        return file_model

    def reset_file(self, file_model: File):
        file_model.is_processing = False
        file_model.is_finished = False

        self.session.commit()

    def mark_file_status(self, file_id, is_processing):
        file_model = self.get_file(file_id)

        file_model.is_processing = is_processing

        self.session.commit()

    def update_file_node(self, file_model: File, transfer):
        file_model.start_time = transfer.getStartTime()
        file_model.transferred_bytes = transfer.getTransferredBytes()
        file_model.num_retry = transfer.getNumRetry()
        file_model.max_retries = transfer.getMaxRetries()
        file_model.mean_speed = transfer.getMeanSpeed()
        file_model.is_finished = transfer.isFinished()
        file_model.state = transfer.getState()

        self.session.commit()

    def get_files(self, url_id=None):
        q = self.session.query(File)
        if url_id:
            q = q.filter(File.url_id == url_id)

        files = q.all()
        return files

    def get_file(self, file_id):
        file_model = self.session.query(File).get(file_id)
        if file_model:
            return file_model

    def create_category(self, *, name):
        category = Category(
            name=name,
        )
        self.session.add(category)
        self.session.commit()
        return category

    def list_categories(self):
        q = self.session.query(Category)
        categories = q.all()
        return categories


class NotFoundError(Exception):
    pass
