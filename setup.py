#!/usr/bin/env python

import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="yatxmilter",
    version="0.1.1",
    author="Humantech Knowledge Management",
    author_email="humantech@humantech.com.br",
    maintainer="Jean Marcel Duvoisin Schmidt",
    maintainer_email="jean.schmidt@humantech.com.br",
    description="Twisted protocol to handle Milter Connections in libmilter style",
    keywords=['milter', 'twisted', 'protocol'],
    license="GNU GPLv2",
    url="https://github.com/humantech/yatxmilter",
    install_requires=["twisted"],
    packages=["yatxmilter"],
    long_description=read("README.md"),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Framework :: Twisted',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Communications :: Email :: Filters',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Networking :: Monitoring',
    ]
)
