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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or impliedriver.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
JavaScript to be executed in the testing user agent.
"""


getHuxleyEvents = """
(function() {
    var events = [];

    window.addEventListener(
        'click',
        function (e) { events.push([Date.now(), 'click', [e.clientX, e.clientY]]); },
        true
    );
    window.addEventListener(
        'keyup',
        function (e) { events.push([Date.now(), 'keyup', String.fromCharCode(e.keyCode)]); },
        true
    );
    window.addEventListener(
        'scroll',
        function(e) { events.push([Date.now(), 'scroll', [this.pageXOffset, this.pageYOffset]]); },
        true
    );

    window._getHuxleyEvents = function() { return events };
})();
"""