#!/usr/bin/env python
"""
A simple Telnet application that asks for input and responds.
The interaction function is a prompt_toolkit coroutine.
Also see the `hello-world-asyncio.py` example which uses an asyncio coroutine.
That is probably the preferred way if you only need Python 3 support.
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.eventloop import From, get_event_loop
from prompt_toolkit.shortcuts import prompt, clear
from prompt_toolkit import PromptSession
import logging

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def interact(connection):
    clear()
    session = PromptSession(output=connection.vt100_output, input=connection.vt100_input)
    connection.send('Welcome!\n')

    try:
        while True:

            # Ask for input.
            result = yield From(session.prompt(message='Say something: ', async_=True))

            # Send output.
            connection.send('You said: {}\n'.format(result))
    except EOFError:
        pass

    connection.send('Bye.\n')


def main():
    server = TelnetServer(interact=interact, host='0.0.0.0', port=2323)
    server.start()
    get_event_loop().run_forever()


if __name__ == '__main__':
    main()