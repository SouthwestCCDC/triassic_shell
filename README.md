# triassic_shell

## License

MIT License.

## Introduction

This module operates the park fences at Triassic Park for the Southwest 
Regional Collegiate Cyber Defense Competition. It has two parts: the
Park Control Console, which is the CLI and either accessibly locally,
or by running the `telnet` subcommand to expose it over telnet; and a
simple flash webservice used to score and/or degrade the fences.

Persistence to disk is optional via the `-f` flag. It uses flat files
with Python's pickle module, so thread-safety and concurrency is not
guaranteed (rather the opposite, as a matter of fact).

## Requirements

* Python 3.7 or higher
* Linux, for the telnet server (Windows works for the local version)
* All the python modules in `requirements.txt`
* Root access, to use ports 23 and 80.

## Important files

* `triassic_shell.py` - The shell itself. Run this directly. See its
  help command (`python triassic_shell.py -h`) for details.

* `triassic_scoring.py` - The web service - run directly. See its help
  command (`python triassic_shell.py -h`) for details.

* `prompt_command.py` and `triassic_prompts.py` - These implement most
  of the behavior of the CLI, using the Prompt Toolkit library.

* `data_model.py` - The data model.

* `telnet/` - A patched version of Prompt Toolkit's built-in telnet
  server to make it a little bit more robust and allow errors to be
  passed up to the main server outer loop.

* `degrade_step.py` - Run this every minute to degrade the fences
  that are failing.

* `requirements.py` - A list of dependencies to install with pip.
