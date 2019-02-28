import sys
import asyncio

from prompt_toolkit import PromptSession
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop
from prompt_toolkit.patch_stdout import patch_stdout

import data_model
from triassic_prompts import BasePrompt

def main_sync():
    root = data_model.get_data_root()

    session = PromptSession()
    BasePrompt(session, zodb_root=root).loop_until_exit()

def main():
    # Tell prompt_toolkit to use the asyncio event loop.
    use_asyncio_event_loop()
    root = data_model.get_data_root()

    session = PromptSession()

    shell_task = asyncio.ensure_future(BasePrompt(session, zodb_root=root).loop_until_exit())

    loop = asyncio.get_event_loop()
    loop.run_until_complete(shell_task)


async def launch_session(connection):
    try:
        root = data_model.get_data_root()
        session = PromptSession(output=connection.vt100_output, input=connection.vt100_input)
        await BasePrompt(session, zodb_root=root, connection=connection).loop_until_exit()
    except KeyboardInterrupt:
        pass

def main_telnet():
    from prompt_toolkit.contrib.telnet.server import TelnetServer
    # Tell prompt_toolkit to use the asyncio event loop.
    use_asyncio_event_loop()

    server = TelnetServer(interact=launch_session, host='0.0.0.0', port=2323)
    server.start()
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'telnet':
        main_telnet()
    main()