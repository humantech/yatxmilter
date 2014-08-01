#!/usr/bin/env python

import os
from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "TxMilter",
    version = "0.1",
    author = "Jean Marcel Duvoisin Schmidt, Humantech",
    author_email = "contato@jschmidt.me",
    description = "Twisted protocol to handle Milter Connections in libmilter style",
    license = "GNU GPLv2",
    keywords = "Milter, Twisted",
    url = "https://github.com/humantech/txmilter",
    packages=["txmilter"],
    long_description=read("README.md")
)
