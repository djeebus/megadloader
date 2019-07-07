import os
from setuptools import setup

setup(
    # Application name:
    name="megadloader",

    # Version number (initial):
    version=open('VERSION').read(),

    # Application author details:
    author="Joe Lombrozo",
    author_email="joe@djeebus.net",

    # Packages
    packages=["megadloader"],
    package_dir={'': 'backend'},

    # Details
    url="https://github.com/djeebus/megadloader",

    install_requires=[
        'megasdk',
        'pyramid',
        'sqlalchemy',
        'waitress',
    ],

    description="megadloader is a demon for download public links from http://mega.co.nz",

    entry_points = {
        'paste.app_factory': [
            'main = megadloader.web:main',
        ],
    },

    include_package_data=True,
)
