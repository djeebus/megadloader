import enum
import logging
import pyramid.config
import pyramid.events
import pyramid.httpexceptions
import pyramid.renderers
import pyramid.response
import signal
import uuid

from megadloader import decode_url
from megadloader.db import configure_db, Db
from megadloader.processor import DownloadProcessor


def main(global_config, **settings):
    config = pyramid.config.Configurator(settings=settings)

    config.include(_api)
    config.include(_db)
    config.include(_log)
    config.include(_renderers)
    config.include(_processor)
    config.include(_static)

    return config.make_wsgi_app()


def _log(config: pyramid.config.Configurator):
    logging.basicConfig()

    config.add_tween('megadloader.web.log_tween_factory')


def log_tween_factory(view, registry):
    def wrap_view(request):
        print(f'{request.method} {request.path}')
        response = view(request)
        print(f'{request.method} {request.path} [{response.status_code}]')
        return response
    return wrap_view


def _renderers(config: pyramid.config.Configurator):
    pyramid.renderers.json_renderer_factory.add_adapter(
        enum.Enum, lambda e, r: e.value,
    )


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


def _processor(config: pyramid.config.Configurator):
    processor_id = str(uuid.uuid4())[:6]

    processor = DownloadProcessor(
        destination=config.registry.settings['destination'],
        processor_id=processor_id,
    )
    processor.start()

    def bye(*args, **kwargs):
        processor.stop()
        exit(0)

    signal.signal(signal.SIGINT, bye)

    config.add_request_method(
        lambda request: processor_id, 'processor_id', reify=True,
    )
    config.add_request_method(
        lambda request: processor, 'processor', reify=True,
    )


def _static(config: pyramid.config.Configurator):
    config.add_static_view(name='static', path='megadloader:static/')

    config.add_route('root', '/')
    config.add_view(
        request_method='GET', route_name='root',
        view=handle_get_root,
    )


def handle_status(request):
    db: Db = request.db
    processor: DownloadProcessor = request.processor

    return {
        'status': processor.status,
        'urls': [url for url in db.get_urls()],
    }


def handle_add_url(request):
    db: Db = request.db
    mega_url = request.POST['mega_url']
    category = request.POST.get('category')
    mega_url = decode_url(mega_url) or ''
    mega_url = mega_url.strip()

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
    bundle_url = request.registry.settings.get("bundle_url")
    if not bundle_url:
        bundle_url = '/static/app.js'

    body = f"""
<html>
<body>
    <div id="app"></div>
    <script src="{bundle_url}"></script>
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
