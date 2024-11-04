const logger = require('../functions/logger.js')
module.exports = function (req, res, next) {
    logger.log(`${req.ip} - ${req.method} ${req.originalUrl}`)
    next();
}