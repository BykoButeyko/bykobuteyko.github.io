// Page-view count: one empty request per page load, with the page and where the visitor came from.
// No cookies, nothing stored in the browser. The server keeps IPs cut to /24.
new Image().src = "https://whales.bykobuteyko.com/hit?p=" + encodeURIComponent(location.pathname) +
  "&r=" + encodeURIComponent(document.referrer);
