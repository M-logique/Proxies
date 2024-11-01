const express = require('express')
const fs = require('node:fs');
const router = express.Router()

router.get('/:name', async (req, res) => {
    const regularFiles = fs.readdirSync('proxies/regular');
    const fileName = regularFiles.find(file => (file === req.params.name) || (file.split('.')[0] === req.params.name));
    const fileContent = fs.readFileSync(`proxies/regular/${fileName}`, { encoding: 'utf8' });
    const configs = fileContent.split('\n');
    const amount = Number(req.query.amount) || Number(req.query.limit) || Number(req.query.count) || -1;
    const sliced = configs.slice(0, amount);
    const joined = sliced.join('\n');
    res.set('Content-Type', 'text/plain');
    res.status(200).send(joined);
});

router.get('/', async (req,res) => {
    const regularFiles = fs.readdirSync('proxies/regular');
    const mapped = regularFiles.map(file => file.split('.')[0] || file);
    const joined = mapped.join(', ');
    res.status(200).send(`available endpoints: ${joined}`);
});

module.exports = {
    path: '/proxies/regular',
    router: router
}
