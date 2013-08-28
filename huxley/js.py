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

now = """
return Date.now();
"""

# todo work around IE < 11 not supporting MutationObserver.. 
# back to DOM Mutation Events?
pageChangingObserver = """
(function() {
    window._huxleyLastModified = Date.now()
    window._huxleyIsPageChanging = function(timeout) {
        return timeout > ( Date.now() - window._huxleyLastModified );
    }

    var observer = new MutationObserver(
        function(mutations) {
            window._huxleyLastModified = Date.now();
        }
    );
    observer.observe(document, { childList: true });
})();
"""

def isPageChanging(timeout):
    return """
return window._huxleyIsPageChanging(%s);
""" % timeout

listenForKeyEvents = """
(function() {
    var keyPresses = [];
    window.addEventListener(
        'keyup',
        function (e) { 
            keyPresses.push([
                Date.now(), 
                'keyup', [
                    e.target.id, 
                    e.target.className, 
                    e.target.classList
                ]
            ]); 
        },
        true
    );
    window._getKeyEvents = function(timestamp) {
        var result = [];
        keyPresses.forEach(
            function(press) {
                if ( press[0] > timestamp ) {
                    result.push(press)
                }
            })
        return result;
    }
})();
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
        function (e) { 
            events.push([
                Date.now(), 
                'keyup', [
                    String.fromCharCode(e.keyCode), 
                    e.shiftKey,
                    e.target.id, 
                    e.target.className, 
                    e.target.classList
                ]
            ]); 
        },
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
