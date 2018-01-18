# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='datum',
    version='1.0.0',
    py_modules=['datum'],
    install_requires=[
        'Click',
        'pymysql',
    ],
    entry_points='''
        [console_scripts]
        datum=datum:main
    ''',
    description='Personal data management platform',
    long_description=readme,
    author='Travis Kohlbeck',
    author_email='me@travisk.com',
    url='https://github.com/tdkohlbeck/datum-cli',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)
