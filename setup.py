# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in ql/__init__.py
from ql import __version__ as version

setup(
	name='ql',
	version=version,
	description='Supporting Future of Medicine',
	author='Perkasa JoB',
	author_email='perkasajob@gmail.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
