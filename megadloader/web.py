import pyramid.config
import pyramid.events
import pyramid.httpexceptions
import pyramid.response
import signal
import uuid

from megadloader import decode_url
from megadloader.db import configure_db, Db
from megadloader.processor import DownloadProcessor


def main(global_config, **settings):
    config = pyramid.config.Configurator(settings=settings)

    config.include(_db)
    config.include(_queue)
    config.include(_static)
    config.include(_api)

    return config.make_wsgi_app()


def _api(config: pyramid.config.Configurator):
    config.add_route('api: status', '/api/status')
    config.add_view(
        request_method='GET', route_name='api: status',
        view=handle_status, renderer='json',
    )

    config.add_route('api: urls', '/api/urls/')
    config.add_view(
        request_method='GET', route_name='api: urls',
        view=handle_get_urls, renderer='json',
    )
    config.add_view(
        request_method='POST', route_name='api: urls',
        view=handle_add_url, renderer='json',
    )

    config.add_route('api: url', '/api/urls/{url_id}')
    config.add_view(
        request_method='DELETE', route_name='api: url',
        view=handle_delete_url, renderer='json',
    )

    config.add_route('api: files', '/api/files/')
    config.add_view(
        request_method='GET', route_name='api: files',
        view=handle_list_files, renderer='json',
    )

    config.add_route('api: file', '/api/files/{file_id}')
    config.add_view(
        request_method='GET', route_name='api: file',
        view=handle_get_file, renderer='json',
    )


def _db(config: pyramid.config.Configurator):
    configure_db(config.registry.settings)

    config.add_request_method(
        _db_factory, 'db', reify=True,
    )


def _db_factory(request):
    db = Db()

    def fin(req):
        db.dispose()

    request.add_finished_callback(fin)

    return db


def _queue(config: pyramid.config.Configurator):
    processor_id = str(uuid.uuid4())[:6]

    processor = DownloadProcessor(
        destination=config.registry.settings['destination'],
        db=Db(),
        processor_id=processor_id,
    )
    processor.start()

    def bye(*args, **kwargs):
        processor.stop()
        exit(0)

    signal.signal(signal.SIGINT, bye)

    config.add_request_method(lambda request: processor_id, 'processor_id', reify=True)
    config.add_request_method(lambda request: processor, 'processor', reify=True)


def _static(config: pyramid.config.Configurator):
    config.add_route('root', '/')
    config.add_view(
        request_method='GET', route_name='root',
        view=handle_get_root,
    )


def handle_status(request):
    db: Db = request.db
    queue: DownloadProcessor = request.queue

    return {
        'status': queue.status,
        'urls': db.get_urls(),
        'files': [
            {'filename': fname, 'filesize': fnode.getSize()}
            for fnode, fname in queue.get_files()
        ],
    }


def handle_add_url(request):
    db: Db = request.db
    mega_url = request.POST['mega_url']
    category = request.POST.get('category')
    mega_url = decode_url(mega_url)
    if not mega_url:
        request.response.status_code = 400
        return {'code': 'invalid_mega_url'}

    url = db.add_url(mega_url, category)
    request.response.status_code = 201
    return url


def handle_get_urls(request):
    db: Db = request.db

    urls = db.get_urls()
    return urls


def handle_get_root(request):
    body = f"""
<html>
<body>
    <div id="app"></div>
    <script src="{request.registry.settings["bundle_url"]}"></script>
</body>
</html>
"""
    return pyramid.response.Response(
        body=body,
        content_type='text/html',
    )


def handle_list_files(request):
    db: Db = request.db

    params = request.GET
    files = db.get_files(**params)

    return files


def handle_get_file(request):
    db: Db = request.db
    file_id = request.matchdict['file_id']
    file_model = db.get_file(file_id)
    if file_model is None:
        request.response.status_code = 404
        return {'code': 'file_not_found'}

    return file_model


def handle_delete_url(request):
    db: Db = request.db
    processor: DownloadProcessor = request.processor

    url_id = request.matchdict['url_id']
    url_model = db.get_url(url_id)
    if not url_model:
        request.response.status_code = 404
        return {'code': 'url_not_found'}

    if processor.current_url == url_model:
        request.response.status_code = 400
        return {'code': 'cannot_stop_current_url'}

    db.delete_url(url_model)
    return {'code': 'ok'}
