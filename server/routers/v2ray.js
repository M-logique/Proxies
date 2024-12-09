const express = require('express')
const fs = require('node:fs');
const path = require('node:path')
const router = express.Router()
const utils = require('../functions/utils');

router.get('/:name', async (req, res) => {
    const folderPath = path.join(process.cwd(), 'proxies', 'v2ray');
    const v2rayFiles = fs.readdirSync(folderPath);
    const fileName = v2rayFiles.find(file => (file === req.params.name) || (file.split('.')[0] === req.params.name));

    if (!fileName) {
        // If file not found, return 404
        return res.status(404).send({ error: 'File not found' });
    }

    const filePath = path.join(folderPath, fileName);
    const fileContent = fs.readFileSync(filePath, { encoding: 'utf8' });
    const configs = fileContent.split('\n');
    const protocolFiltered = configs.filter(config => !req.query.protocol || config.startsWith(req.query.protocol));
    const amount = Number(req.query.amount) || Number(req.query.limit) || Number(req.query.count) || -1;
    const sliced = protocolFiltered.slice(0, amount);
    const joined = sliced.join('\n\n');

    utils.setHeaders(res, `Github: M-logique/Proxies | ${req.params.name.toUpperCase().replaceAll("-", " ")}`);

    if (req.query.decrypted == '' || req.query.decrypted) {
        res.status(200).send(joined);
    } else {
        const encrypted = utils.b64encode(joined);
        res.status(200).send(encrypted);
    }    
});

router.get('/location/:location', async (req, res) => {
    let json = require('../../proxies/byLocation.json')
    json = Object.assign({}, json.profilesByCountryCode, json.profilesByCountryName)
    json["Netherlands"] = [...json["Netherlands"], ... json["The Netherlands"]]
    json = lowerize(json)

    const loc = req.params.location;

    const configs = json[loc]

    if (!configs) {
        return res.status(404).send({ error: 'File not found' });
    }
    
    const protocolFiltered = configs.filter(config => !req.query.protocol || config.startsWith(req.query.protocol));
    const amount = Number(req.query.amount) || Number(req.query.limit) || Number(req.query.count) || -1;
    const sliced = protocolFiltered.slice(0, amount);
    const joined = sliced.join('\n\n');

    utils.setHeaders(res, `Github: M-logique/Proxies | ${req.params.location.toUpperCase().replaceAll("-", " ")}`);

    if (req.query.decrypted == '' || req.query.decrypted) {
        res.status(200).send(joined);
    } else {
        const encrypted = utils.b64encode(joined);
        res.status(200).send(encrypted);
    }    

})

router.get('/', async (req,res) => {
    const folderPath = path.join(process.cwd(), 'proxies', 'v2ray')
    const v2rayFiles = fs.readdirSync(folderPath);
    const mapped = v2rayFiles.map(file => file.split('.')[0] || file);
    const json = require('../../proxies/byLocation.json')
    const arr = [...json.locations.byCountryCode, ...json.locations.byNames].map(item => 'location/'+item)
    const all = [...mapped, ...arr]
    const joined = all.join(', ');
    res.status(200).send(`available endpoints: ${joined}`);
});

module.exports = {
    path: '/proxies/v2ray',
    router: router
}

const lowerize = (obj) =>
    Object.keys(obj).reduce((acc, k) => {
      acc[k.toLowerCase()] = obj[k];
      return acc;
}, {});