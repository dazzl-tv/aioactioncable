import asyncio
import concurrent
import json
import logging
import threading
import websockets
from .subscription import Subscription

__all__ = ["Connect"]


class Connect:
    """
    Action Cable websocket client connection implementation
    Action Cable (https://guides.rubyonrails.org/action_cable_overview.html)
    is a Ruby on Rails websockets service
    This is an asyncio based implementation based on websockets
    (https://github.com/aaugustin/websockets)

    Connect can be used as part of an async context manager.
    e.g.
    import aioactioncable

    async with aioactioncable.connect(uri) as acwebsocket:
      ...

    Args:
      url: url of the Action Cable websocket server
    """

    CONNECT_TIMEOUT = 3
    SUBSCRIPTION_TIMEOUT = 2.0

    def __init__(self, url):
        self.event_loop = None
        self.websocket = None
        self.url = url
        self.is_welcomed = False
        self.subscriptions = {}
        self.logger = logging.getLogger('aioactioncable.connect')
        self.logger.setLevel('DEBUG')

    async def __aenter__(self):
        return await self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    def __await__(self):
        self.logger.info(' Awaiting Connect object to connect')
        return self.connect().__await__()

    def __init_thread(self):
        self.__thread = threading.Thread(
            target=self.__init_event_loop, daemon=True)
        self.__thread.start()

    def __init_event_loop(self):
        self.event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.event_loop)
        self.event_loop.run_forever()

    async def __wait_for_event_loop(self):
        while True:
            if self.event_loop is not None and \
                    self.event_loop.is_running():
                return
            await asyncio.sleep(0)

    async def __connect(self):
        self.websocket = await websockets.connect(self.url, close_timeout=2)
        try:
            await asyncio.wait_for(self.__is_welcomed(),
                                   timeout=self.SUBSCRIPTION_TIMEOUT)
        finally:
            if self.is_welcomed is False:
                raise Exception('Please verify you connect to an '
                                'Action Cable websocket server')
            else:
                self.logger.info(" Connection successful, start receiving!")
                return True

    async def __recv_type(self, json_data):
        self.logger.debug(f' Type field received: {json.dumps(json_data)}')
        if json_data['type'] == 'confirm_subscription':
            if 'identifier' not in json_data:
                self.logger.error(
                    ' Got a confirm_subscription with no identifier')
                return
            channel_identifier = json_data['identifier']
            self.logger.debug(
                f" Got a confirm_subscription for {channel_identifier}")
            if channel_identifier in self.subscriptions:
                self.subscriptions[channel_identifier] = True
        elif json_data['type'] == 'reject_subscription':
            if 'identifier' not in json_data:
                self.logger.error(
                    ' Got a reject_subscription with no identifier')
                return
            channel_identifier = json_data['identifier']
            self.logger.debug(
                f" Got a reject_subscription for {channel_identifier}")
            if channel_identifier in self.subscriptions:
                del self.subscriptions[channel_identifier]

    async def __recv_message(self, json_data):
        self.logger.debug(f' Message field received: {json.dumps(json_data)}')
        identifier = json_data['identifier']
        if identifier in self.subscriptions:
            subscription = self.subscriptions[identifier]
            self.logger.debug(f' Found subscription for {identifier}, '
                              'appending message to its recv Queue')
            await subscription.queue(json_data['message'])

    async def __recv(self):
        async for message in self.websocket:
            json_data = json.loads(message)
            if 'type' in json_data:
                await self.__recv_type(json_data)
            elif 'message' in json_data:
                await self.__recv_message(json_data)

    def __handle_disconnect(self, disconnect_data):
        self.logger.info(' Connect was rejected '
                         '(disconnect type message received)')
        if 'reason' in disconnect_data:
            self.logger.info(" Disconnect reason field is: "
                             f"\"{disconnect_data['reason']}\"")
        if 'reconnect' in disconnect_data:
            self.logger.info(" Disconnect reconnect field is: "
                             f"\"{disconnect_data['reconnect']}\"")

    async def __is_welcomed(self):
        data = await self.websocket.recv()
        json_data = json.loads(data)
        if 'type' not in json_data:
            self.logger.error(' No type in received message '
                              'while waiting for Welcome msg')
        if json_data['type'] == 'welcome':
            self.is_welcomed = True
        elif json_data['type'] == 'disconnect':
            self.__handle_disconnect(json_data)

    async def __is_subscribed(self, channel_identifier):
        while True:
            if self.subscriptions[json.dumps(channel_identifier)] is True:
                return
            await asyncio.sleep(0)

    async def __subscribe(self, identifier):
        self.subscriptions[json.dumps(identifier)] = False
        msg = {
            'command': 'subscribe',
            'identifier': json.dumps(identifier)
        }

        await self.websocket.send(json.dumps(msg))
        try:
            await asyncio.wait_for(self.__is_subscribed(identifier),
                                   timeout=self.SUBSCRIPTION_TIMEOUT)
        finally:
            if self.subscriptions[json.dumps(identifier)] is False:
                del self.subscriptions[json.dumps(identifier)]
                raise Exception(f'Could not subscribe to channel {identifier}')
            else:
                self.logger.info(
                    f'Subcription to channel {identifier} is successful')
                subscription = Subscription(
                    self.websocket, identifier, self.event_loop)
                self.subscriptions[json.dumps(identifier)] = subscription
                return subscription

    async def subscribe(self, identifier):
        """
        Subscribe allows to subscribe to an Action Cable channel
        Identifier is a json object which identifies the channel:
        e.g: {'channel': 'UserChannel'}

        Subscribe is an awaitable, it returns a Subscription object
        once the subscription is done
        """
        if json.dumps(identifier) in self.subscriptions:
            self.logger.error(f' You have already subscribed to {identifier}')
            return self.subscriptions[json.dumps(identifier)]
        future = asyncio.run_coroutine_threadsafe(self.__subscribe(identifier),
                                                  self.event_loop)
        try:
            result = future.result(self.SUBSCRIPTION_TIMEOUT)
        except concurrent.futures.TimeoutError:
            self.logger.error(
                f' Timeout while trying to subscribe to {identifier}')
            future.cancel()
        except Exception as exc:
            self.logger.error(f' Subscribe: {exc}')
            future.cancel()
        else:
            return result

    async def connect(self):
        """
        Connect is the main entry point. This is where the connection
        takes place

        It returns the Connect object once the connection is done.
        """
        self.__init_thread()
        await self.__wait_for_event_loop()
        if self.is_welcomed is True:
            self.logger.error(' Websocket is already connected')
            return self
        future = asyncio.run_coroutine_threadsafe(
            self.__connect(), self.event_loop)
        try:
            result = future.result(self.CONNECT_TIMEOUT)
        except concurrent.futures.TimeoutError:
            self.logger.error(' Timeout while trying to connect')
            future.cancel()
        except Exception as exc:
            self.logger.error(f' Connect: {exc}')
            future.cancel()
        else:
            self.logger.debug(f" Connect returned {result}")
            if result is True:
                self.logger.debug(' Scheduling recv coroutine')
                asyncio.run_coroutine_threadsafe(self.__recv(),
                                                 self.event_loop)
                return self

    async def close(self):
        """
        close stops the event loop and close the websocket connection.
        This is done automatically if you use a context manager
        """
        future = asyncio.run_coroutine_threadsafe(
            self.websocket.close(), self.event_loop)
        try:
            future.result()
        except Exception as exc:
            self.logger.error(f' Close: {exc}')
            future.cancel()
        else:
            self.logger.debug(" Successfully closed connection")
        self.event_loop.stop()
