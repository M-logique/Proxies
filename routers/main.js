const express = require('express')
const router = express.Router()

router.get('/', (req, res) => {
    res.send('I\'m Alive')
})

module.exports = {
    path: '/',
    router: router
}
