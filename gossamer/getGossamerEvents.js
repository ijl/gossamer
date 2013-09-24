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
