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
Take in configured settings, and run tests and such. Or, it should do this.

For settings initialization, see huxley/cmdline.py
"""

def main(*args, **kwargs):
    """
    Placeholder for unittest, TODO
    """
    raise NotImplementedError

def dispatcher(*args, **kwargs):
    """
    Given settings, huxley file?,  a MODE, dispatch the appropriate runs and 
    return an exit code. For consumption by the CLI and unittest 
    integration.
    """
    pass
