#!/usr/bin/env python

import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "txmilter",
    version = "0.1.0",
    author = ["Humantech Knowledge Management", "Jean Marcel Duvoisin Schmidt"],
    author_email = "jean.schmidt@humantech.com.br",
    description = "Twisted protocol to handle Milter Connections in libmilter style",
    license = "GNU GPLv2",
    keywords = "Milter, Twisted",
    url = "https://github.com/humantech/txmilter",
    install_requires=["twisted"],
    packages=["txmilter"],
    long_description=read("README.md")
)
