const express = require('express')
const router = express.Router()

router.all('/', (req, res) => {
    res.send('I\'m Alive')
})

router.all('/discord', (req, res) => {
    res.redirect('https://discord.gg/uqRESgqZSQ')
})

module.exports = {
    path: '/',
    router: router
}
