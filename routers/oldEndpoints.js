const express = require('express')
const router = express.Router()

router.get('/recive/:name', (req, res) => {
    const params = new URLSearchParams(req.query).toString();
    res.redirect(`../../proxies/v2ray/${req.params.name}?${params}`)
})
router.get('/receive/:name', (req, res) => {
    const params = new URLSearchParams(req.query).toString();
    res.redirect(`../../proxies/v2ray/${req.params.name}?${params}`)
})

module.exports = {
    path: '/',
    router: router
}
// kiram be kos khar ermia