const express = require('express')
const router = express.Router()

router.get('/', (req, res) => {
    res.send('im alive')
})

module.exports = {
    path: '/',
    router: router
}
