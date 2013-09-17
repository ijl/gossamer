"""
JavaScript to be executed in the testing user agent.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

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
    """
    Has page changed within the given `timeout`, in milliseconds?
    """
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
        function(e) { events.push([Date.now(), 'scroll', [this.pageXOffset, this.pageYOffset]]); },
        true
    );

    window._getHuxleyEvents = function() { return events };
})();
"""
