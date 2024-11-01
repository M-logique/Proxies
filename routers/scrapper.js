const express = require('express')
const { request } = require('undici')
const { parse } = require('node-html-parser')
const router = express.Router()

router.get('/:channel', async (req, res) => {
    let requested = req.query.count || req.query.limit || req.query.amount || 20
    if (Number(requested) > 200) requested = 200
    const count = Math.ceil(Number(requested) / 20)
    const { body } = await request(`https://t.me/s/${req.params.channel}`)
    const text = await body.text()
    const html = parse(text)
    const widgets = html.querySelectorAll('.tgme_widget_message_text')
    let before = html.querySelector('.tme_messages_more')['_attrs']['data-before']
    let msgs = widgets.map(item => item.innerText).reverse()
    for (const i of new Array(count)) {
        const { body } = await request(`https://t.me/s/${req.params.channel}?before=${before}`)
        const text = await body.text()
        const html = parse(text)
        const widgets = html.querySelectorAll('.tgme_widget_message_text')
        before = html.querySelector('.tme_messages_more')['_attrs']['data-before']
        msgs = [...msgs, ...widgets.map(item => item.innerText).reverse()]
    }
    const pattern = /(?:vless|vmess|ss|trojan):\/\/[^\s#]+(?:#[^\s]*)?/g;
    const configs = msgs.flatMap(str => str.match(pattern)).filter(item => item).map(str => str.replaceAll('&amp;', '&'))
    const protocolFiltered = configs.filter(config => !req.query.protocol || config.startsWith(req.query.protocol))
    const sliced = protocolFiltered.slice(0, Number(requested));
    const joined = 'vless://discord@discord.server:0000?type=tcp#1oi.xyz/discord\n\n' + sliced.join('\n\n');
    res.set('Content-Type', 'text/plain')
    if (req.query.decrypted == '' || req.query.decrypted) {
        res.status(200).send(joined);
    } else {
        const encrypted = btoa(unescape(encodeURIComponent(joined)));
        res.status(200).send(encrypted);
    }
})

module.exports = {
    path: '/telegram',
    router: router
}
