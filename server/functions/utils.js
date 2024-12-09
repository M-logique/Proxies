const c = require('../countries.json')
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
        // نه
        res.set('profile-update-interval', 2);
        res.set('profile-web-page-url', "https://github.com/M-logique/Proxies");
        res.set('support-url', "https://github.com/M-logique/Proxies");
        res.set('Content-Type', 'text/plain');
    },
    b64encode: function (t) {
        return btoa(unescape(encodeURIComponent(t)));
    },
    getName: (input="us") => {
        input = input.toLowerCase()
        const country = c.find(item => item.name === input || item.code === input)
        return country.name.toUpperCase();
    },
    
    getFlag: (input="us") => {
        input = input.toLowerCase()
        const country = c.find(item => item.name === input || item.code === input)
        const codePoints = country.code.toUpperCase().split('').map(char => 127397 + char.charCodeAt(0));
        return String.fromCodePoint(...codePoints);
    }
};