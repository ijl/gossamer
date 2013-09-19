"""
JavaScript to be executed in the testing user agent.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import json

def isPageChanging(timeout): # pragma: no cover
    """
    Has page changed within the given `timeout`, in milliseconds, and are
    there no XMLHTTP requests active?
    """
    return """
return window._gossamerIsPageChanging(%s);
""" % timeout


def get_post(url, postdata): # pragma: no cover
    """
    Retrieve data for navigate.
    """
    markup = '\n'.join([
        '<form method="post" action="%s">' % url,
        '\n'.join(['<input type="hidden" name="%s" />' % k for k in postdata.keys()]),
        '</form>'
    ])

    script = 'var container = document.createElement("div"); container.innerHTML = %s;' \
            % json.dumps(markup)

    for (i, v) in enumerate(postdata.values()):
        if not isinstance(v, basestring):
            v = json.dumps(v)
        script += 'container.children[0].children[%d].value = %s;' % (i, json.dumps(v))

    script += 'document.body.appendChild(container);'
    script += 'container.children[0].submit();'
    return '(function(){ ' + script + '; })();'

now = """
return Date.now();
"""

# https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver
pageChangingObserver = """
(function() {
    window._gossamerLastModified = Date.now();
    var _XMLHttpRequest = XMLHttpRequest.prototype.open;;
    window._gossamerXMLHTTPs = 0;
    XMLHttpRequest.prototype.open = function(method, url, async, user, pass) {
        window._gossamerXMLHTTPs++;
        this.addEventListener("readystatechange", function() {
            if (this.readyState == 4) {
                window._gossamerXMLHTTPs--;
            }
        }, false);
        _XMLHttpRequest.call(this, method, url, async, user, pass);
    }
})(XMLHttpRequest);
(function() {
    window._gossamerIsPageChanging = function(timeout) {
        return timeout > ( Date.now() - window._gossamerLastModified ) &&
            window._gossamerXMLHTTPs == 0;
    }
    var observer = new MutationObserver(
        function(mutations) {
            window._gossamerLastModified = Date.now();
        }
    );
    observer.observe(document, { childList: true });
})();
"""

getGossamerEvents = """
(function() {
    var events = [];

    window.addEventListener(
        'click',
        function (e) {
            events.push([Date.now(), 'click', [e.clientX, e.clientY]]);
        },
        true
    );
    window.addEventListener(
        'keyup',
        function (e) {
            var idVal = e.target.id ?
                document.querySelector('#'+e.target.id).value : null
            var classNameVal = e.target.className ?
                document.querySelector('.'+e.target.className).value : null;
            var classListVal = e.target.classList ?
                document.querySelector('.'+e.target.classList.toString()).value : null;
            events.push([
                Date.now(),
                'keyup', [
                    String.fromCharCode(e.keyCode),
                    e.shiftKey,
                    [e.target.id, idVal],
                    [e.target.className, classNameVal],
                    [e.target.classList, classListVal]
                ]
            ]);
        },
        true
    );
    window.addEventListener(
        'scroll',
        function(e) {
            events.push([Date.now(), 'scroll', [this.pageXOffset, this.pageYOffset]]);
        },
        true
    );

    window._getGossamerEvents = function() { return events };
})();
"""
