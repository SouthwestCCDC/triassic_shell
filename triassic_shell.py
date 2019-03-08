import sys
import logging
import socket
import argparse
import json
import os

from prompt_toolkit import PromptSession
from prompt_toolkit.eventloop import From, get_event_loop
from prompt_toolkit.patch_stdout import patch_stdout

import data_model
from triassic_prompts import BasePrompt

def run_local():
    pass
    session = PromptSession()
    shell_task = From(BasePrompt(session).loop_until_exit())
    get_event_loop().run_until_complete(shell_task)

def launch_telnet_session(connection):
    print('Launching new session')
    try:
        session = PromptSession(output=connection.vt100_output, input=connection.vt100_input)
        yield From(BasePrompt(session, connection=connection).loop_until_exit())
    except KeyboardInterrupt:
        pass
    except socket.error as e:
        print('Socket error %s. Shutting down session.' % e.errno)

def exception_handler(context):
    # If we've gotten here, it's likely that something horrible has happened.
    print("<<< Unhandled exception in an event loop.")
    print("<!! This usually means that something horrible has happened.")
    print("<!! Therefore, we will completely restart the server.")
    print("<!! Goodbye.")
    os.execl(sys.executable, sys.executable, *sys.argv)

def run_telnet(host, port):
    # Import it here, because the import causes an error in Windows;
    #  and I want to be able to run the local version in Windows.
    from telnet.server import TelnetServer

    logging.basicConfig()
    logging.getLogger().setLevel(logging.INFO)

    server = TelnetServer(interact=launch_telnet_session, host=host, port=port)
    server.start()
    get_event_loop().set_exception_handler(exception_handler)
    get_event_loop().run_forever()

def main():
    parser = argparse.ArgumentParser(prog='triassic_shell.py')
    parser.add_argument('-f', '--file', help="Path to the ZODB persistence file to use.")
    parser.add_argument('-c', '--config-file', type=data_model.consensus_config_from_file)
    telnet_parsers = parser.add_subparsers(dest='command')
    telnet_parser = telnet_parsers.add_parser('telnet')
    telnet_parser.add_argument('-a', '--address', default='127.0.0.1', dest='host')
    telnet_parser.add_argument('-p', '--port', type=int, default=21321)

    args = parser.parse_args()

    if args.config_file:
        data_model.consensus_config = args.config_file

    # Initialize the database, if needed.
    data_model.init_db(args.file if args.file else None)

    if args.command == 'telnet':
        run_telnet(args.host, args.port)
    else:
        run_local()

if __name__ == "__main__":
    main()
