import enum
import sqlalchemy.ext.declarative

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship

Base = sqlalchemy.ext.declarative.declarative_base()


class UrlStatus(enum.Enum):
    idle = 'IDLE'
    processing = 'PROCESSING'
    error = 'ERROR'
    done = 'DONE'


class Url(Base):
    __tablename__ = 'urls'

    id = Column(Integer, primary_key=True)
    category = Column(String(250), nullable=True)
    url = Column(String(250), nullable=False)

    processor_id = Column(String(250), default='')
    status = Column(String(20), default=UrlStatus.idle.value)
    message = Column(Text(), default='')

    files = relationship('File')

    def get_status(self, processor_id):
        if self.status == UrlStatus.processing:
            if self.processor_id != processor_id:
                return UrlStatus.idle
        return self.status

    @property
    def is_file(self):
        index = self.url.index('#')
        if index == -1:
            return False

        return self.url[index+1] != 'F'

    def __json__(self, request):
        status = self.get_status(request.processor_id)

        return {
            'id': self.id,
            'files': [f for f in self.files],
            'status': status,
            'url': self.url,
            'error_msg': self.message,
            'transferred_size': sum((f.transferred_bytes for f in self.files)),
            'total_size': sum((f.total_bytes for f in self.files)),
        }


class File(Base):
    __tablename__ = 'files'

    id = Column(sqlalchemy.Integer, primary_key=True)
    url_id = Column(sqlalchemy.Integer, ForeignKey('urls.id'))
    url = relationship('Url', back_populates='files')
    path = Column(String(1024), nullable=False)
    file_handle = Column(String(1024), nullable=False)

    is_processing = Column(Boolean, default=False)

    total_bytes = Column(sqlalchemy.BigInteger, nullable=False)
    transferred_bytes = Column(sqlalchemy.BigInteger, default=0)
    num_retry = Column(sqlalchemy.Integer, nullable=True)
    max_retries = Column(sqlalchemy.Integer, nullable=True)
    mean_speed = Column(sqlalchemy.BigInteger, nullable=True)
    is_finished = Column(Boolean, default=False)
    state = Column(Integer, nullable=True)

    @property
    def status(self):
        if self.is_finished:
            return 'finished'

        if self.is_processing:
            return 'downloading'

        return 'idle'

    def __json__(self, request):
        return {
            'file_id': self.id,
            'url_id': self.url_id,
            'path': self.path,
            'total_bytes': self.total_bytes,
            'file_handle': self.file_handle,
            'is_downloading': self.is_processing,

            'transferred_bytes': self.transferred_bytes,
            'num_retry': self.num_retry,
            'max_retries': self.max_retries,
            'mean_speed': self.mean_speed,
            'is_finished': self.is_finished,
            'state': self.state,
            'status': self.status,
        }
