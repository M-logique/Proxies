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
    
};