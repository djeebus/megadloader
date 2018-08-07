import pyramid.config
import pyramid.events
import pyramid.httpexceptions
import pyramid.response
import signal

from megadloader.queue import DownloadQueue


def main(global_config, **settings):
    config = pyramid.config.Configurator(settings=settings)

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
        request_method='POST', route_name='api: urls',
        view=handle_add_url, renderer='json',
    )


def handle_status(request):
    queue: DownloadQueue = request.queue

    return {
        'status': queue.status,
        'queue': queue.urls,
        'files': [
            {'filename': fname, 'filesize': fnode.getSize()}
            for fnode, fname in queue.files
        ],
    }


def handle_add_url(request):
    queue: DownloadQueue = request.queue
    mega_url = request.POST['mega_url']
    queue.enqueue(mega_url)


def _queue(config: pyramid.config.Configurator):
    queue = DownloadQueue(destination=config.registry.settings['destination'])
    queue.start()

    def bye(*args, **kwargs):
        queue.stop()
        exit(0)

    signal.signal(signal.SIGINT, bye)

    config.add_request_method(lambda request: queue, 'queue', reify=True)


def _static(config: pyramid.config.Configurator):
    config.add_route('root', '/')
    config.add_view(
        request_method='GET', route_name='root',
        view=handle_get_root,
    )


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
