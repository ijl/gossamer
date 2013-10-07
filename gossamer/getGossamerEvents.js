// getGossamerEvents
// Store events we're interested in reproducing.
(function() {
    "use strict";

    var events = [];

    window.addEventListener(
        'click',
        function (e) {
            var isSelect = false;
            var idText, classNameText, classListText, elm = null;
            if (e.target.nodeName === "SELECT") { // dropdown
                isSelect = true;
                if (e.target.id) {
                    elm = document.querySelector('#' + e.target.id);
                    idText = elm.options[elm.selectedIndex].text;
                } else {};
                if (e.target.className) {
                    elm = document.querySelector('.' + e.target.className);
                    classNameText = elm.options[elm.selectedIndex].text;
                } else {};
                if (e.target.classList.toString()) {
                    elm = document.querySelector('.' + e.target.classList.toString());
                    classListText = elm.options[elm.selectedIndex].text;
                } else {};
            };
            events.push([
                Date.now(),
                'click', [
                    [e.clientX, e.clientY],
                    isSelect,
                    [e.target.id, idText],
                    [e.target.className, classNameText],
                    [e.target.classList, classListText]
                ]
            ]);
        },
        true
    );

    window.addEventListener(
        'keyup',
        function (e) {
            var idVal = e.target.id ?
                        document.querySelector('#' + e.target.id).value : null;
            var classNameVal = e.target.className ?
                        document.querySelector('.' + e.target.className).value : null;
            var classListVal = e.target.classList.toString() ?
                        document.querySelector('.' + e.target.classList.toString()).value : null;
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
