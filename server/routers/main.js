const express = require('express')
const router = express.Router()
const path = require('path');


router.all('/', (req, res) => {
    const filePath = path.join(__dirname, '..', 'static', 'index.html');
    res.sendFile(filePath);
})

module.exports = {
    path: '/',
    router: router
}
