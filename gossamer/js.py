"""
JavaScript to be executed in the testing user agent.
"""

# Copyright (c) 2013 contributors; see AUTHORS.
# Licensed under the Apache License, Version 2.0
# https://www.apache.org/licenses/LICENSE-2.0

import pkg_resources
import json


def _get_javascript(name):
    """
    Convenience for reading JavaScript from package.
    """
    return pkg_resources.resource_stream('gossamer', '%s.js' % name).read()


# https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver
pageChangingObserver = _get_javascript('pageChangingObserver')


getGossamerEvents = _get_javascript('getGossamerEvents')


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
    if not isinstance(postdata, dict):
        postdata = json.loads(postdata)

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
