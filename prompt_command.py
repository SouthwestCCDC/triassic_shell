import sys
import argparse

from prompt_toolkit.eventloop import From
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.eventloop.future import Future

class CommandParseFail(Exception):
    pass

class PromptCommandParse(argparse.ArgumentParser):
    def __init__(self, *args, print_fn=None, print_file=sys.stderr, **kwargs):
        super().__init__(*args, **kwargs)
        self.print_file = print_file
        self.print_fn = print_fn

    def exit(self, status=0, message=None):
        raise CommandParseFail(message if message else 'general failure')

    def _print_message(self, message, file=None):
        # Just rewire all output to our default output file.
        if message:
            if self.print_fn:
                self.print_fn(message)
            else:
                file = self.print_file
                file.write(message)
                file.write('\r\n')

class CommandLevel():
    command_desc_dict = dict()
    default_prompt_text = '> '

    def __init__(self, session, connection=None):
        self.session = session
        self.prompt_text = self.default_prompt_text
        self.connection = connection
        
        # If the subclass hasn't changed the descriptions for 
        # the `help` and `exit` built-ins, go ahead and set the defaults:
        self.command_desc_dict.setdefault('help', 'get help on commands')
        self.command_desc_dict.setdefault('exit', 'exit current level')
        
        self.command_parsers = dict()

        for command, description in self.command_desc_dict.items():
            # TODO: default of self._default_passthrough_argparse???
            self.command_parsers[command] = getattr(self, '_%s_parser' % command)(self.base_parser(command, description))
            assert ('_do_%s' % command) in dir(self)

    def base_parser(self, name, desc):
        return PromptCommandParse(prog=name, description=desc, add_help=False, allow_abbrev=True, print_file=self.session.output, print_fn=self.println)

    def _default_passthrough_argparse(self, parser):
        return parser

    def _help_parser(self, parser):
        parser.add_argument('command', choices=self.command_parsers.keys())
        parser.add_argument('subcommand', nargs='*')
        return parser

    def _do_help(self, args):
        parser = self.command_parsers[args.command]
        if args.subcommand and parser._subparsers._actions:
            while args.subcommand:
                if not parser._subparsers:
                    self.println('got extra garbage: %s' % ' '.join(args.subcommand))
                    return
                choices = parser._subparsers._actions[0].choices
                sc = args.subcommand.pop(0)
                if sc in choices:
                    parser = choices[sc]
                else:
                    self.println('unknown subcommand: %s\n' % sc)
                    return
        parser.print_help(file=self.session.output)

    def _exit_parser(self, parser):
        return parser

    def _do_exit(self, args):
        raise EOFError()

    def println(self, text):
        if self.connection:
            self.connection.send('%s\n' % text)
        else:
            self.session.app.print_text('%s\n' % text)
    
    def prompt_enter(self):
        pass

    def prompt_exit(self):
        pass

    def loop_until_exit(self):
        completer = WordCompleter(self.command_parsers.keys())
        self.prompt_enter()
        while True:
            try:
                # # TODO: Probably not needed, ultimately.
                # with patch_stdout():
                    # Show a prompt, and store the user's input once it's received.
                shell_input_raw = yield From(self.session.prompt(
                    self.prompt_text, 
                    completer=completer, 
                    complete_style=CompleteStyle.READLINE_LIKE,
                    async_=True
                ))
                
                # Tokenize the input
                shell_input_params = shell_input_raw.split()

                # If it's a blank line, ignore the input and prompt again.
                if not shell_input_raw:
                    continue
                    
                # Interpret the first token as the command, and the remainder as args.
                cmd = shell_input_params.pop(0)

                # Check whether the command is valid in this context.
                if cmd not in self.command_parsers:
                    self.println('unknown command %s' % cmd)
                    continue

                # Run the appropriate argparse on the command.
                try:
                    args = self.command_parsers[cmd].parse_args(args=shell_input_params)
                except CommandParseFail as e:
                    self.println(str(e))
                    continue

                # If we're here, the command `cmd` has been evaluated by the appropriate
                #  argparse, so we know it's valid. The constructor has done the required
                #  introspection and assertions to make sure that all the below derived
                #  function names exist as methods on this class. So here we go!

                # TODO: Does the thing where it will accept a fragment break us here?
                cmd_method = getattr(self, '_do_%s' % cmd)

                # TODO TODO TODO horrible hack
                if cmd in ['access', 'enable']:
                    yield From(cmd_method(args))
                else:
                    cmd_method(args)
                

            except EOFError:
                # An EOFError is raised when it's time to leave this level.
                break
        self.prompt_exit()