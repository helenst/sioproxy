sioproxy
========

sioproxy is a little proxy built on [tornadio2](https://github.com/mrjoes/tornadio2) which is a Tornado backend to the socket.io multitransport web networking library.

sioproxy allows you to write normal TCP servers to talk to webclients. It'll talk to the browser in whatever transport is possible, and proxy the messages to and from the TCP server.

It can handle multiple servers and makes use of the socket.io protocol's endpoint system to connect clients to the correct backend. Backends must be set up in a dictionary.

Limitations:
------------
* ignores socket.io's RPC - it just dumbly passes messages back and forth. Allows
* no handling of reconnecting - if either client or server goes away, the other is cut off
* text messages only
* no SSL at present
* a little rough around the edges, you'll need to edit the file to set up your own endpoints etc.
* could probably use a bit of demo code or examples.
