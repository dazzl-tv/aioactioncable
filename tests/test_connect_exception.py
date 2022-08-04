import aioactioncable
import asyncio
import pytest

async def connect_exception(uri):
    async with aioactioncable.connect(uri) as acconnect:
        pass

def test_connect_exception():
    with pytest.raises(Exception):
        asyncio.run(connect_exception('wss://cable.example.com'))

