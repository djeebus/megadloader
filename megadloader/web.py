import pyramid.config
import pyramid.events
import pyramid.httpexceptions
import pyramid.response
import signal

from megadloader.queue import DownloadQueue


def main(global_config, **settings):
    config = pyramid.config.Configurator(settings=settings)

    config.add_route('root', '/')
    config.add_view(
        request_method='GET', route_name='root',
        view=handle_get_root,
    )

    config.add_view(
        request_method='POST', route_name='root',
        view=handle_post_root,
    )

    queue = DownloadQueue(destination=settings['destination'])
    queue.start()

    def bye(*args, **kwargs):
        queue.stop()
        exit(0)

    signal.signal(signal.SIGINT, bye)

    config.add_request_method(lambda request: queue, 'queue', reify=True)

    return config.make_wsgi_app()


def handle_get_root(request):
    queue: DownloadQueue = request.queue

    url_rows = [f'<tr><td>{url}</td></tr>' for url in queue.queue]
    url_rows = ''.join(url_rows)

    file_rows = [f'<tr><td>{fname}</td></tr>' for fnode, fname in queue._files]
    file_rows = ''.join(file_rows)

    body = f"""
<html>
<body>
    <form method="POST">
        <input name="mega_url" type="text">
        <input type="submit">
    </form>
    
    <table>
        <caption>URL Queue</caption>
        <thead>
            <tr><th>Url</th></tr>
        </thead>
        <tbody>{url_rows}</tbody>
    </table>
    
    <table>
        <caption>File Queue</caption>
        <thead>
            <tr><th>Filename</th></tr>
        </thead>
        <tbody>{file_rows}</tbody>
    </table>
    
    <div>
        Status: {queue.status}
    </div>
</body>
</html>
"""
    return pyramid.response.Response(
        body=body,
        content_type='text/html',
    )


def handle_post_root(request):
    queue: DownloadQueue = request.queue
    mega_url = request.POST['mega_url']
    queue.queue.append(mega_url)

    route_url = request.route_url(route_name='root')
    raise pyramid.httpexceptions.HTTPFound(location=route_url)
