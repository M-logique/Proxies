const express = require('express')
const router = express.Router()

router.all('/', (req, res) => {
    res.sendFile('index.html', { root: '../static/' })
})

module.exports = {
    path: '/',
    router: router
}
