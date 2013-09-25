// pageChangingObserver
// Has there been a MutationObserver event within the specified timeout?
// Are there any active XMLHttpRequests?
// If so, the page is returned as still-changing, and Gossamer polls again.
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
        return timeout > ( Date.now() - window._gossamerLastModified )
             && window._gossamerXMLHTTPs == 0;
    }
    var observer = new MutationObserver(
        function(mutations) {
            window._gossamerLastModified = Date.now();
        }
    );
    observer.observe(document, { childList: true });
})();
