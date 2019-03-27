# triassic_shell

## License

Copyright 2019 George Louthan, Brady Deetz, and SWCCDC. Permission is 
hereby granted, free of charge, to any person obtaining 
a copy of this software and associated documentation files (the 
"Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to
the following conditions:  The above copyright notice and this permission
notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

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
