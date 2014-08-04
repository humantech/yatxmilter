#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from yatxmilter.protocol import MilterProtocolFactory
from yatxmilter.defaults import MilterFactory


def main():
    # we consider a "good pattern" to import reactor just when you'll use it,
    # since we have other reactors in our codebase
    from twisted.internet import reactor

    reactor.listenTCP(1234, MilterProtocolFactory(
        MilterFactory()
    ))

    reactor.run()

if __name__ == '__main__':
    main()
