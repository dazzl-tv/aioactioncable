import asyncio
import json
import logging


class Subscription:
    """
    Implementation of an Action Cable subscription.
    A Subscription object is returned when a subscribe is done
    from Connect object.

    The object is iterable to retrieve messages received over
    the subscribed channel.

    e.g.
    import aioactioncable

    async with aioactioncable.connect(uri) as acwebsocket:
      subscription = acwebsocket.subscribe(identifier)
      async for msg in subscription:
        process(msg)

    """

    def __init__(self, websocket, identifier, event_loop):
        self.websocket = websocket
        self.identifier = json.dumps(identifier)
        self.event_loop = event_loop
        self.logger = logging.getLogger('aioactioncable.subscription')
        self.recv_queue = asyncio.Queue()
        self.logger.debug(' Subscription object init')

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.unsubscribe()

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.recv()

    """ queue method, must be called internally from ACWebsockets only """
    async def queue(self, message):
        self.recv_queue.put_nowait(message)

    async def __send(self, data):
        msg = {
            'command': 'message',
            'identifier': self.identifier,
            'data': json.dumps(data)
        }
        await self.websocket.send(json.dumps(msg))

    async def send(self, data):
        future = asyncio.run_coroutine_threadsafe(
            self.__send(data), self.event_loop)
        try:
            result = future.result()
        except Exception as exc:
            self.logger.error(f' Send: {exc}')
            future.cancel()
        else:
            return result

    async def __recv(self):
        msg = await self.recv_queue.get()
        self.recv_queue.task_done()
        return json.dumps(msg)

    async def recv(self):
        """
        Recv awaits for next received message on channel
        """
        future = asyncio.run_coroutine_threadsafe(
            self.__recv(), self.event_loop)
        try:
            result = future.result()
        except Exception as exc:
            self.logger.error(f' Recv: {exc}')
            future.cancel()
        else:
            return result

    async def __unsubscribe(self):
        msg = {
            'command': 'unsubscribe',
            'identifier': self.identifier
        }
        await self.websocket.send(json.dumps(msg))

    async def unsubscribe(self):
        """
        unsubscribe implements channel unsubscribe
        """
        future = asyncio.run_coroutine_threadsafe(
            self.__unsubscribe(), self.event_loop)
        try:
            result = future.result()
        except Exception as exc:
            self.logger.error(f' Unsubscribe: {exc}')
            future.cancel()
        else:
            return result
