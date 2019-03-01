import asyncio, telnetlib3

import sys
import logging
import socket
import argparse

from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop
from prompt_toolkit.patch_stdout import patch_stdout

import asyncio

async def shell(reader, writer):
    session = PromptSession('Would you like to play a game?', input=reader, output=writer)
    # writer.write('\r\nWould you like to play a game? ')
    # inp = await reader.read(1)
    inp = await session.prompt()
    if inp:
        writer.echo(inp)
        writer.write('\r\nThey say the only way to win '
                     'is to not play at all.\r\n')
        await writer.drain()
    writer.close()

use_asyncio_event_loop()
loop = asyncio.get_event_loop()
coro = telnetlib3.create_server(port=6023, shell=shell)
server = loop.run_until_complete(coro)
loop.run_until_complete(server.wait_closed())