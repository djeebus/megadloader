import atexit
import enum
import logging
import pyramid.config
import pyramid.events
import pyramid.httpexceptions
import pyramid.renderers
import pyramid.response
import pyramid.static
import subprocess
import sys
import uuid

from megadloader import decode_url
from megadloader.db import configure_db, Db
from megadloader.processor import DownloadProcessor


def main(global_config, **settings):
    config = pyramid.config.Configurator(settings={**settings, **global_config})

    config.include(_api)
    config.include(_cors)
    config.include(_db)
    config.include(_log)
    config.include(_processor)
    config.include(_renderers)
    config.include(_static)

    return config.make_wsgi_app()


PROCESSOR_KEY = '--processor-key--'


def _processor(config: pyramid.config.Configurator):
    from megadloader import processor
    processor_id = str(uuid.uuid4())

    config_name = config.registry.settings['__file__']

    process = subprocess.Popen(
        args=[
            sys.executable,
            processor.__file__,
            '--processor-id', processor_id,
            '--config', config_name,
            '--app-name', 'main',
        ],
    )

    config.registry[PROCESSOR_KEY] = process

    config.add_request_method(
        name='processor_id',
        callable=lambda r: processor_id,
        reify=True,
    )

    atexit.register(_kill_processor, process)


def _kill_processor(process: subprocess.Popen):
    process.kill()


def _cors(config: pyramid.config.Configurator):
    config.add_tween('megadloader.web.cors_tween_factory')


def cors_tween_factory(handler, registry):
    cors_domain = registry.settings.get('cors_domain')
    if not cors_domain:
        return handler

    def tween(request):
        response = handler(request)

        response.headerlist.extend([
            ('Access-Control-Allow-Origin', cors_domain),
        ])

        return response

    return tween


def _log(config: pyramid.config.Configurator):
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

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

    config.add_route('api: categories', '/api/categories/')
    config.add_view(
        request_method='GET', route_name='api: categories',
        view=handle_list_categories, renderer='json',
    )
    config.add_view(
        request_method='POST', route_name='api: categories',
        view=handle_create_category, renderer='json',
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

    config.add_route('api: queue items', '/api/queue/{queue_id}')
    config.add_view(
        request_method='DELETE', route_name='api: queue items',
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


def _static(config: pyramid.config.Configurator):
    config.add_route(name='index', path='/*subpath')
    config.add_view(
        request_method='GET', route_name='index',
        view=pyramid.static.static_view(
            root_dir='megadloader:static/',
            package_name='megadloader:static',
        ),
    )


def handle_status(request):
    db: Db = request.db
    return {'urls': [url for url in db.get_urls()]}


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

    url_id = request.matchdict['queue_id']
    url_model = db.get_url(url_id)
    if not url_model:
        request.response.status_code = 404
        return {'code': 'url_not_found'}

    if processor.current_url == url_model:
        request.response.status_code = 400
        return {'code': 'cannot_stop_current_url'}

    db.delete_url(url_model)
    return {'code': 'ok'}


def handle_list_categories(request):
    db: Db = request.db

    categories = db.list_categories()
    return categories


def handle_create_category(request):
    db: Db = request.db
    payload = request.json

    category = db.create_category(**payload)

    return category
