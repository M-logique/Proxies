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
        
        res.set('profile-title', `base64:${atob(subName)}`);
        res.set("upload", 0);
        res.set("download", 0);
        res.set("expire", 0);
        res.set("total", 10737418240000000);
        res.set('profile-update-interval', 6);
        res.set('profile-web-page-url', "https://github.com/M-logique/Proxies");
        res.set('support-url', "https://github.com/M-logique/Proxies");
        res.set('Content-Type', 'text/plain');
    }
};