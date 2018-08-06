from setuptools import setup

setup(
    # Application name:
    name="megadloader",

    # Version number (initial):
    version="0.1",

    # Application author details:
    author="Joe Lombrozo",
    author_email="joe@djeebus.net",

    # Packages
    packages=["megadloader"],

    # Details
    url="https://github.com/djeebus/megadloader",

    install_requires=[
        'mega',
        'pyramid',
    ],

    description="megadloader is a demon for download public links from http://mega.co.nz",

    entry_points = {
        'paste.app_factory': [
            'main = megadloader.web:main',
        ],
    },
)
