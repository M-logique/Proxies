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
        res.set('Profile-Title', subName)
        res.set('profile-update-interval', 6)
        res.set('profile-web-page-url', "https://github.com/M-logique/Proxies")
        res.set('support-url', "https://github.com/M-logique/Proxies")
        res.set('Content-Type', 'text/plain')
    }
};