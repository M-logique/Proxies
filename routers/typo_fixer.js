const express = require('express')
const router = express.Router()

router.get('/:name', (req, res) => {
    const params = new URLSearchParams(req.query).toString();
    res.redirect(`../receive/${req.params.name}?${params}`)
})

module.exports = {
    path: '/recive',
    router: router
}
// kiram be kos khar ermia