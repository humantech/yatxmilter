txmilter
========

The milter protocol written in pure python as a twisted protocol! 
All under GNU GPLv2!

####What?

The txmilter is a project that aims to bring milter as a reactor, to do that 
twisted framework for python is perfect, it abstracts all connections and all 
asynchronous operations needed to archive this.

The goal of using txmilter is to provide a _faster_ response using the power of 
asynchronous server instead the threaded solution used by libmilter. Txmilter is 
_really fast_ and can handle _lots_ of simultaneous connections thanks to twisted.

###How do I use it?

txmilter is designed to be as simple as possible, and as close as possible to 
libmilter (that you can check here: HTTPS://www.milter.org/developers/api/), 
having that in mind, if you know how libmilter works you won't get any trouble 
working with txmilter. Function calls are (_almost_) the same and functions 
names really remembers libmilter name calls.

For example, take a close look to the code:


```
#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from twisted.internet import reactor
from protocol import MilterProtocolFactory
from defaults import MilterFactory

def main():
    reactor.listenTCP( 1234, MilterProtocolFactory( 
        MilterFactory()
    ) )
    reactor.run()

if __name__ == '__main__':
    main()

```

This is _just_ a twisted protocol inicialization as any twisted program will do...

`MilterFactory` is a just a empty factory that builds `Milter` objects. You should 
build your own factory to instantiate your own milter objects. The MilterProtocolFactory 
is what do all the magic for you, it abstracts the communication to give you the 
`Milter` interface.

Your job is to extend `Milter`, override the method that you need to work with, 
override the `xxfi_negotiate` to signal to the exchange what you plan to support 
and build a `MilterFactory`.

For a plus, one txmilter program can handle more than one milter plugin on the 
same connection, taking care of handling any signal different from continue and 
communicating the MTA.


```
             MTA                                txmilter                       your milter plugin

  _____________________________
  |                            |
  | MTA Opens Connection       |
  |____________________________|
 
   
                |                      _____________________________
                |                     |                            |
                |_________________>   | Instantiate all plugins    |
                                      |____________________________|
  _____________________________                 |
  |                            |                |
  | MTA Starts Negotiation     |  <_____________|
  |____________________________|
    
                |                                                       _____________________________
                |                                                       |                            |
                |___________________________________________________>   | Send flags                 |
                                                                        |____________________________|
                                                                                     |
                                       _____________________________                 |
                                      |                            |                 |
                                      | Merge flags                |    <____________|
                                      |____________________________|
                                                   |
  _____________________________                    |
  |                            |                   |
  | Status filtering request   |  <________________|
  |____________________________|
                |
                |                                                       _____________________________
                |                                                       |                            |
                |___________________________________________________>   | Process And reply          |
                                                                        |____________________________|
                                                                                     |
                                       _________________________________             |
                                      |                                |             |
                                      | Wait all finish or first error |  <__________|
                                      |________________________________|
                                                      |
                                                      V
                                       _________________________________
                                      |                                |
                                      | Reply Status                   |
                                      |________________________________|
                                                      |
                                                      V
  _________________________________________________________________________________________________________________
  |                                                                                                                |
  |                                       Close connection.........                                                |
  |________________________________________________________________________________________________________________|
    
``` 
