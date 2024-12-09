module.exports = {
    handleRedirect: function (req, res, newEndpoint) {
        // Convert query parameters to a string
        const params = new URLSearchParams(req.query).toString();
    
        // Construct the target URL
        const targetUrl = params 
            ? `${newEndpoint}?${params}` 
            : `${newEndpoint}`;
    
        // Redirect to the target URL
        res.redirect(targetUrl);
    },
    setHeaders: function (res, subName) {
        
        res.set('profile-title', `base64:${this.b64encode(subName)}`);
        // res.set("subscription-userinfo", "upload=0; download=0; total=10737418240000000; expire=2546249531");
        res.set('profile-update-interval', 6);
        res.set('profile-web-page-url', "https://github.com/M-logique/Proxies");
        res.set('support-url', "https://github.com/M-logique/Proxies");
        res.set('Content-Type', 'text/plain');
    },
    b64encode: function (t) {
        return btoa(unescape(encodeURIComponent(t)));
    }
};