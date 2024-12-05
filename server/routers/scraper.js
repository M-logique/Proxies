const express = require('express')
const { request } = require('undici') // undici is used for making HTTP requests
const { parse } = require('node-html-parser') // Used for parsing HTML
const router = express.Router()
const config = require('../../config.json')

router.get('/:channel', async (req, res) => {
    // Determine the number of configs to fetch, with a maximum of 200
    let requested = req.query.count || req.query.limit || req.query.amount || 20
    if (Number(requested) > 200) requested = 200
    const count = Math.ceil(Number(requested) / 20)

    // Fetch the initial page of the Telegram channel
    const { body } = await request(`https://t.me/s/${req.params.channel}`)
    const text = await body.text()
    const html = parse(text)

    // Extract message texts and the 'before' parameter for pagination
    const widgets = html.querySelectorAll('.tgme_widget_message_text')
    let before = html.querySelector('.tme_messages_more')['_attrs']['data-before']
    let msgs = widgets.map(item => item.innerText).reverse()

    // Fetch additional pages if needed
    for (const i of new Array(count)) {
        const { body } = await request(`https://t.me/s/${req.params.channel}?before=${before}`)
        const text = await body.text()
        const html = parse(text)
        const widgets = html.querySelectorAll('.tgme_widget_message_text')
        before = html.querySelector('.tme_messages_more')['_attrs']['data-before']
        msgs = [...msgs, ...widgets.map(item => item.innerText).reverse()]
    }

    // Regular expression to match VPN configuration URLs
    const pattern = /(?:vless|vmess|ss|trojan):\/\/[^\s#]+(?:#[^\s]*)?/g;

    // Extract VPN configs from messages, filter out null matches, and replace HTML entities
    const configs = msgs.flatMap(str => str.match(pattern)).filter(item => item).map(str => str.replaceAll('&amp;', '&'))

    // Filter configs based on the protocol query parameter (if provided)
    const protocolFiltered = configs.filter(config => !req.query.protocol || config.startsWith(req.query.protocol))

    // Slice the filtered configs array to the requested number of items
    const sliced = protocolFiltered.slice(0, Number(requested));

    // Join the configs with double newlines
    const joined = sliced.join('\n\n');

    utils.setHeaders(res, `Git: M-logique/Proxies | ${req.params.name.toUpperCase()}`)

    // Check if decrypted output is requested
    if (req.query.decrypted == '' || req.query.decrypted) {
        // Send the joined configs as plain text
        res.status(200).send(joined);
    } else {
        // Encrypt the joined configs using Base64 encoding
        const encrypted = btoa(unescape(encodeURIComponent(joined)));
        res.status(200).send(encrypted);
    }
})

module.exports = {
    path: '/telegram',
    router: router
}

