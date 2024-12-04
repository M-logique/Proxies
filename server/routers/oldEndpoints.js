const express = require('express')
const router = express.Router()
const utils = require("../functions/utils");


router.get('/recive/:name', (req, res) => {
    utils.handleRedirect(req, res, `/proxies/v2ray/${req.params.name}`);
});
router.get('/receive/:name', (req, res) => {
    utils.handleRedirect(req, res, `/proxies/v2ray/${req.params.name}`);
});

router.get('/channel/:name', (req, res) => {
    utils.handleRedirect(req, res, `/telegram/${req.params.name}`);
});

module.exports = {
    path: '/',
    router: router
}
// kiram be kos khar ermia