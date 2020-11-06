#!/usr/bin/env python

import os
from setuptools import setup, find_packages
from katastertools import __VERSION__

classifiers = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Scientific/Engineering :: GIS',
    'License :: OSI Approved :: GNU General Public License version 2.0 (GPL-2)',
]

# setup
setup(
    name='kataster-import',
    version=__VERSION__,
    description='Import tools for Slovak cadastral data',
    long_description="This package is dedicated for processing cadastral data in exchange formats created by "
                     "The Geodesy, Cartography and Cadastre Authority of Slovak republic."
                     "There is no reason to use it for other purposes.",

    author='Peter Hyben, Ivan Mincik, Marcel Dancak',
    author_email='peter.hyben@hugis.eu, ivan.mincik@gmail.com, dancakm@gmail.com',

    license='GNU GPL-2',
    url='https://github.com/imincik/kataster-import',

    package_dir={'katastertools': 'katastertools'},
    packages=find_packages(),
    package_data={'katastertools': ['sql/*.sql']},
    setup_requires=['GDAL', 'dbf', 'click'],
    entry_points={'console_scripts': ['kt_vgi2shp=katastertools.kt_vgi2shp:main',
                                      'kt_import_dbf2=katastertools.kt_import_dbf2:main',
                                      'kt_import_fuvi=katastertools.kt_import_fuvi:main',
                                      'kt_vycisti_fuvi=katastertools.kt_vycisti_fuvi:main',
                                      'kt_vytvor_db=katastertools.kt_vytvor_db:main',
                                      'kt_sql=katastertools.kt_sql']},

    classifiers=classifiers
)

# vim: set ts=4 sts=4 sw=4 noet:
