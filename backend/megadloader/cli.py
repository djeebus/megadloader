import click
import mega
import os

from megadloader import MEGA_API_KEY
from megadloader.processor import (
    FileNodeDownloader,
    UrlProcessor,
    FileListener,
)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('url')
@click.argument('dest')
def one_shot(url, dest):
    os.makedirs(dest, exist_ok=True)

    api = mega.MegaApi(MEGA_API_KEY)
    processor = UrlProcessor(api)
    file_nodes = processor.process(url)

    processor = FileNodeDownloader(api)
    for fname, file_node in file_nodes:
        fname = os.path.join(dest, fname)

        file_listener = FileListener()
        processor.download(fname, file_node, file_listener)
        file_listener.wait()


if __name__ == '__main__':
    cli()
