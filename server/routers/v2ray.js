const express = require('express')
const fs = require('node:fs');
const path = require('node:path')
const router = express.Router()

router.get('/:name', async (req, res) => {
    const folderPath = path.join(process.cwd(), 'proxies', 'v2ray')
    const v2rayFiles = fs.readdirSync(folderPath);
    const fileName = v2rayFiles.find(file => (file === req.params.name) || (file.split('.')[0] === req.params.name));
    const filePath = path.join(folderPath, fileName)
    const fileContent = fs.readFileSync(filePath, { encoding: 'utf8' });
    const configs = fileContent.split('\n');
    const protocolFiltered = configs.filter(config => !req.query.protocol || config.startsWith(req.query.protocol))
    const amount = Number(req.query.amount) || Number(req.query.limit) || Number(req.query.count) || -1;
    const sliced = protocolFiltered.slice(0, amount);
    const joined = 'vless://discord@discord.server:0000?type=tcp#1oi.xyz/discord\n\n' + sliced.join('\n\n');
    res.set('Content-Type', 'text/plain');
    if (req.query.decrypted == '' || req.query.decrypted) {
        res.status(200).send(joined);
    } else {
        const encrypted = btoa(unescape(encodeURIComponent(joined)));
        res.status(200).send(encrypted);
    }    
});

router.get('/', async (req,res) => {
    const folderPath = path.join(process.cwd(), 'proxies', 'v2ray')
    const v2rayFiles = fs.readdirSync(folderPath);
    const mapped = v2rayFiles.map(file => file.split('.')[0] || file);
    const joined = mapped.join(', ');
    res.status(200).send(`available endpoints: ${joined}`);
});

module.exports = {
    path: '/proxies/v2ray',
    router: router
}
