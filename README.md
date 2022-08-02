# aioactioncable: async Action Cable client library
aioactioncable is a python library for building Ruby on Rails [Action Cable](https://guides.rubyonrails.org/action_cable_overview.html) clients.

The library is based on [websockets](https://github.com/aaugustin/websockets) and asyncio.

aioactioncable is thus an async Rails Action Cable client library.

## Installation

```
$ python3 -m pip install aioactioncable
```

aioactioncable requires Python 3 and therefore needs to be installed using the Python 3 version of pip. 

## Requirements

* Python >= 3.7
* [websockets](https://github.com/aaugustin/websockets)

## Usage

In addition to managing websockets connections, Action Cable servers manage multiple channels, that clients can subscribe to.

Here is a code example to connect to an Action Cable server, subscribe to a channel and receive messages on that channel:

```python
#!/usr/bin/env python3

import aioactioncable
import asyncio

def process(msg)
  print(f'Message received on {json.dumps(identifier)}')
  ...

async def ac_recv(uri, identifier):
  async with aioactioncable.connect(uri) as acconnect:
    subscription = acconnect.subscribe(identifier)
    async for msg in subscription:
      process(msg, identifier)

asyncio.run(ac_recv('wss://example.app', {'channel': 'ChatChannel'}))

```

**All the code examples below must be run in an asyncio event loop.**
Examples are built "chronologically", object created in Connect section is reused in Subscribe section, and so on.

### Connect to an Action Cable server

```python
import aioactioncable

acconnect = aioactioncable.connect(uri)
```

aioactioncable Connect object is an async context manager, you can thus use it in an `async with` statement:
```python
import aioactioncable
import asyncio

async with aioactioncable.connect('wss://example.app') as acconnect:
  ...
```

### Subscribe to an Action Cable channel

```python
subscription = acconnect.subscribe({'channel': 'ChatChannel'})
```

### Recv messages on an Action Cable channel

Receive next message on subscription channel:
```python
msg = subscription.recv()
```

Subscription object is an iterable, you can thus iterate over to recv messages in an async for loop:
```python
async for msg in subscription:
  ...
```

### Send messages on an Action Cable channel

```python
subscription.send({'action': 'create', 'chatRoom': 'climbing'})
```

### Unsubscribe from an Action Cable channel

```python
subscription.unsubscribe()
```

### Close an Action Cable server connection

Explicit close of the connection is not needed if it is done in an `async with` statement.

Otherwise:
```python
acconnect.close()
```

## License

aioactioncable is distributed under the MIT license.

## Contributions

Contributions are very welcome!

Feel free to open an [issue](https://github.com/dazzl-tv/aioactioncable/issues/new) for any bug report.

Feel free to propose bug fixes or features via a [Pull Request](https://github.com/dazzl-tv/aioactioncable/compare).
