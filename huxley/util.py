# Copyright (c) 2013 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Utilities.
"""

import os
import jsonpickle
from huxley import errors


def read_recorded_run(filename):
    """
    Load a serialized run. TODO in versioning, validation, etc.
    """
    try:
        if os.path.getsize(filename) <= 0:
            raise errors.RecorcedRunEmpty('%s is empty' % filename)
    except OSError:
        raise errors.RecordedRunDoesNotExist('%s does not exist' % filename)
    try:
        with open(os.path.join(filename, 'record.json'), 'r') as fp:
            recorded_run = jsonpickle.decode(fp.read())
        # todo validate
        return recorded_run
    except ValueError as exc:
        raise # todo error
    except Exception as exc:
        raise exc


def write_recorded_run(filename, output):
    """
    Serialize a recorded run to a JSON file.
    """
    try:
        with open(os.path.join(filename, 'record.json'), 'w') as fp:
            fp.write(
                jsonpickle.encode(
                    output
                )
            ) # todo version the recorded run, and validate it
    except Exception as exc: # todo how can this fail
        raise exc
    return True


def prompt(display, options=None):
    """
    Given text as `display` and optionally `options` as an 
    iterable containing acceptable input, returns a boolean 
    of whether the prompt was met.
    """
    inp = raw_input(display)
    if options:
        if inp in options:
            return True
        return False
    return True

