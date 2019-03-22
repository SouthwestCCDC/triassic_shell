import time

from prompt_toolkit.eventloop import From
from prompt_command import CommandLevel
import data_model

class BasePrompt(CommandLevel):
    command_desc_dict = {
        "enable" : "enter privileged mode",
        "access" : "manage park systems (not all commands supported)",
        "show" : "show status of exhibits and security nodes"
    }

    def __init__(self, session, enabled=False, **kwargs):
        super().__init__(session, **kwargs)
        self.enabled = enabled
        if enabled:
            self.prompt_text = '#> '

    def prompt_enter(self):
        if not self.enabled:
            self.println("Triassic Park, System Security Interface")
            self.println("Version 4.0.5, Alpha E")
            self.println("Ready...\n")

    def _enable_parser(self, parser):
        # No parameters - just `enable`
        return parser

    def _do_enable(self, args):
        if not self.enabled:
            self.println('No password is configured...')
            yield From(BasePrompt(self.session, enabled=True).loop_until_exit())

    def _access_parser(self, parser):
        access_subparsers = parser.add_subparsers(required=True, dest='command')
        for command in ['main', 'backup']:
            sp = access_subparsers.add_parser(command, add_help=False, print_fn=self.println)
            sp_subparsers = sp.add_subparsers(required=True, dest='subcommand')
            for sc in ['security', 'program']:
                subcommand = sp_subparsers.add_parser(sc, add_help=False, print_fn=self.println)
                if sc == 'security':
                    subcommand.add_argument('node', action='store', choices=['grid'])
        return parser

    def _do_access(self, args):
        if not self.enabled:
            self.println('ACCESS DENIED')
            return
        elif args.command == 'main' and args.subcommand == 'security' and args.node =='grid' :
            # ACCESS MAIN SECURITY GRID
            self.println('ok')
            yield From(GridPrompt(self.session).loop_until_exit())
        else:
            # poop
            self.println("command not available")

    def _show_parser(self, parser):
        subparsers = parser.add_subparsers(required=True, dest='command')
        subparsers.add_parser('all', add_help=False, print_fn=self.println)
        exhibit_parser = subparsers.add_parser('exhibit', add_help=False, print_fn=self.println)
        exhibit_parser.add_argument('name', nargs='?', type=str) # TODO: choices
        node_parser = subparsers.add_parser('node', add_help=False, print_fn=self.println)
        def nodeid(i):
            return int(i, 16)
        node_parser.add_argument('id', type=nodeid)
        return parser

    def _do_show(self, args):
        all_exhibits = set()
        fence_sections = {}
        data_model.load_from_disk()
        for id,node in data_model.fence_segments.items():
            all_exhibits.add(node.dinosaur)
            fence_sections[id] = node

        if args.command == 'all':
            self.println('node\texhibit\t\tstatus')
            self.println('====\t=======\t\t======')
            for section in fence_sections.values():
                self.println('%x\t%s\t%s' % (
                    section.id, 
                    section.dinosaur,
                    section.fence_status()
                ))
                time.sleep(data_model.DELAY_SLEEP)
        elif args.command == 'exhibit':
            if args.name:
                self.println('node\tstatus')
                self.println('====\t======')
                for section in fence_sections.values():
                    if section.dinosaur == args.name:
                        time.sleep(data_model.DELAY_SLEEP)
                        self.println('%x\t%s' % (section.id, section.fence_status()))
            else:
                self.println('exhibit')
                self.println('=======')
                for exh in all_exhibits:
                    time.sleep(data_model.DELAY_SLEEP)
                self.println(exh)
        elif args.command == 'node':
            if args.id:
                self.println('node\texhibit\t\tstatus\tcondition')
                self.println('====\t=======\t\t======\t=========')
                if args.id in fence_sections:
                    section = fence_sections[args.id]
                    time.sleep(data_model.DELAY_SLEEP)
                    self.println('%x\t%s\t%s\t%0.3f' % (section.id, section.dinosaur,
                                        section.fence_status(), section.state))


class GridPrompt(CommandLevel):
    command_desc_dict = {
        "set" : "manually toggle power to a security node or exhibit",
        "resync" : "fast restart of a node's Super Cortex Engine\u2122",
    }
    default_prompt_text = 'main security grid #> '

    def _set_parser(self, parser):
        # set node <id> <up/down>
        # set exhibit <name> <up/down>
        subparsers = parser.add_subparsers(required=True, dest='scope')
        exhibit_parser = subparsers.add_parser('exhibit', add_help=False, print_fn=self.println)
        exhibit_parser.add_argument('name', type=str) # TODO: choices?
        exhibit_parser.add_argument('state', type=str, choices=['up', 'down'])

        node_parser = subparsers.add_parser('node', add_help=False, print_fn=self.println)
        def nodeid(i):
            return int(i, 16)
        node_parser.add_argument('id', type=nodeid)
        node_parser.add_argument('state', type=str, choices=['up', 'down'])
        return parser
    
    def _do_set(self, args):
        if args.scope == 'exhibit':
            data_model.load_from_disk()
            self.println('node\texhibit\t\tstatus')
            self.println('====\t=======\t\t======')
            # DATABASE_SECTION
            for id,node in data_model.fence_segments.items():
                if node.dinosaur != args.name:
                    continue
                # The node matches the requested exhibit, so make it so:
                if args.state == 'up' and node.enabled:
                    self.println('Error: requested node to up is already up')
                    break
                node.enabled = (args.state=='up') # True for up, False for down

                self.println('%x\t%s\t%s' % (id, node.dinosaur, node.fence_status()))
            data_model.save_to_disk()
        elif args.scope == 'node':
            data_model.load_from_disk()

            if args.id not in data_model.fence_segments:
                self.println('error')
                # TODO: "dump core"
                raise EOFError()

            # DATABASE_SECTION
            node = data_model.fence_segments[args.id]
            node.enabled = (args.state=='up') # True for up, False for down
            data_model.save_to_disk()

            self.println('node\tstatus')
            self.println('====\t======')
            self.println('%x\t%s' % (node.id, node.fence_status()))

    def _resync_parser(self, parser):
        # resync node <id>
        subparsers = parser.add_subparsers(required=True, dest='scope')
        node_parser = subparsers.add_parser('node', add_help=False, print_fn=self.println)
        def nodeid(i):
            return int(i, 16)

        node_parser.add_argument('id', type=nodeid)
        return parser

    def _do_resync(self, args):
        # The only option, currently, is `alloc node <id> <val>`
        #  so we know that's been validated.
        # DATABASE_SECTION
        data_model.load_from_disk()
        if args.id not in data_model.fence_segments:
            self.println('error')
            conn.close()
            # TODO: "dump core"
            raise EOFError()

        # Now we know val, and id, are both ok.
        node = data_model.fence_segments[args.id]
        node.resync()
        data_model.save_to_disk()

        self.println('node\tstatus\tcondition')
        self.println('====\t======\t=========')
        self.println('%x\t%s\t%0.3f' % (node.id,
                            node.fence_status(), node.state))
