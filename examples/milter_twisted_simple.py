#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from twisted.internet import reactor
from protocol import MilterProtocolFactory
from defaults import MilterFactory

def main():
    reactor.listenTCP( 1234, MilterProtocolFactory( 
#      [ MilterFactory(), MilterFactory(), MilterFactory() ]
        MilterFactory()
    ) )
    reactor.run()

if __name__ == '__main__':
    main()
