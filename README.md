yatxmilter (yet another)
========================

_we recently changed the name of the project from **txmilter** to **yatxmilter** because there already was a [txmilter](https://github.com/flaviogrossi/txmilter) project under development with a different license and we didn't feel comfortable to use the name._

The milter protocol written in pure python as a twisted protocol, licensed under [GPLv2!](../master/LICENSE)

##wait, what?

The **yatxmilter** is a project that aims to bring the milter protocol to python using the [Twisted Matrix Framework](https://twistedmatrix.com/trac/). It was inspired after people telling us to use [crochet](https://pypi.python.org/pypi/crochet/) and libmilter to achieve our goals. As we like to use things inside Twisted the way Twisted works, it was decided to create this project.

The goal of using **yatxmilter** is to provide a _faster_ response using Twisted's power of asynchronous calls instead the threaded solution used by libmilter. **yatxmilter** is _really fast_ and can handle _lots_ of simultaneous connections. In pure python ;)

###how do I use it?

first, you'll have to install it using pip or from [PyPI](https://pypi.python.org/pypi/yatxmilter):

```
$ pip install yatxmilter
```

**yatxmilter** is designed to be as simple as possible, and as close as possible to libmilter (that you can check here: HTTPS://www.milter.org/developers/api/), having that in mind, if you know how libmilter works you won't get any trouble
working with yatxmilter. Function calls are (_almost_) the same and functions names really remembers libmilter name calls.

For example, take a close look to the code:


```
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

```

This is _just_ a twisted protocol inicialization as any twisted protocol will do ...

`MilterFactory` is just an empty factory that creates `Milter` objects. You should build your own factory to instantiate your milter objects. The `MilterProtocolFactory` is the one that does the magic for you, abstracting communication to expose you the `Milter` interface.

Your job is to extend `Milter`, override any method you need to work with _and_ the `xxfi_negotiate` method to exchange what signals your milter will support to build a `MilterFactory`.

As a plus, the **yatxmilter** can handle more than one milter plugin on the same connection, taking care of handling any signal different from continue and communicating with the MTA.


```
          MTA                 yatxmilter             your milter

  ___________________
  |                  |
  |    MTA opens     |
  |    connection    |
  |__________________|
           |             __________________
           |             |                 |
           |_________>   |   Instantiate   |
                         |   all plugins   |
                         |_________________|
  ___________________             |
  |                  |            |
  |   MTA starts     |            |
  |   negotiation    |  <_________|
  |__________________|
           |                                   ____________________
           |                                   |                   |
           |________________________________>  |    Send flags     |
                                               |___________________|
                                                        |
                         __________________             |
                         |                 |            |
                         |   Merge flags   |  <_________|
                         |_________________|
                                  |
  ___________________             |
  |                  |            |
  | Status filtering |            |
  |    request       |  <_________|
  |__________________|
           |
           |                                   ____________________
           |                                   |                   |
           |________________________________>  | Process and reply |
                                               |___________________|
                                                        |
                         __________________             |
                         |                 |            |
                         | Wait all finish |            |
                         | or first error  |  <_________|
                         |_________________|
                                  |
                                  V
                         __________________
                         |                 |
                         |  Reply status   |
                         |_________________|
                                  |
                                  V
  _________________________________________________________________
  |                                                                |
  |                        Close connection                        |
  |________________________________________________________________|

```

and that's all :)

#todo

* we still have no test units and code coverage, but you're welcome to push them if you want :)
* docs: wow, better examples and sphinx related docs are still pending;
* py3 was just completely ignored for now.


#license

**yatxmilter** code and docs are released under the [GPLv2](../master/LICENSE) license, from which is derived from the libmilter license - as we used its code as a base for ours and also as a form of gratitude.
