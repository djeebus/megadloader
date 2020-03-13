import click

from megadloader.processor import UrlProcessor


@click.group()
def cli():
    pass


@cli.command()
@click.argument('url')
@click.argument('dest')
def one_shot(url, dest):
    processor = UrlProcessor()
    files = processor.process(url)

    processor = FileProcessor(dest)
    for file in files:
        processor.process(file)



if __name__ == '__main__':
    cli()
