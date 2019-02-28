import sys
import asyncio
import logging
import socket

from prompt_toolkit import PromptSession
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop
from prompt_toolkit.patch_stdout import patch_stdout

import data_model
from triassic_prompts import BasePrompt

def main():
    # Tell prompt_toolkit to use the asyncio event loop.
    use_asyncio_event_loop()
    data_model.init_db()

    session = PromptSession()

    shell_task = asyncio.ensure_future(BasePrompt(session).loop_until_exit())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(shell_task)


async def launch_session(connection):
    print('Launching new session')
    try:
        session = PromptSession(output=connection.vt100_output, input=connection.vt100_input)
        await BasePrompt(session, connection=connection).loop_until_exit()
    except KeyboardInterrupt:
        pass
    except socket.error as e:
        print('Socket error. Shutting down session.')

def main_telnet():
    from telnet.server import TelnetServer

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    # Tell prompt_toolkit to use the asyncio event loop.
    use_asyncio_event_loop()

    server = TelnetServer(interact=launch_session, host='0.0.0.0', port=21321)
    server.start()
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'telnet':
        main_telnet()
    main()
