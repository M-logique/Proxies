const chalk = require('chalk')
const { port } = require('./config.json')
const fs = require('node:fs');
const http = require('http');
const express = require('express');
const logger = require('./server/functions/logger.js')
const compression = require('compression')
const session = require('express-session')
const app = express();
const server = http.createServer(app);
const path = require('path');

app.use(compression())
app.use(express.json())
app.use(express.urlencoded({ extended: true }))

app.use(session({
    secret: 'mySecretKey',
    resave: false,
    saveUninitialized: false
}));


app.use(express.static('public'))
app.set('views', './views');
app.use('/assets', express.static(path.join(__dirname, 'server/static/assets')));



const routers = fs.readdirSync('./server/routers');
const middlewares = fs.readdirSync('./server/middlewares');

logger.log('Started loading middlewares ...')
for (const middleware of middlewares) {
    const mw = require(`./server/middlewares/${middleware}`);
    app.use(mw)
    logger.success(`('${middleware}') middleware loaded!`)
}

logger.log('Started loading routers ...')
for (const router of routers) {
    const r = require(`./server/routers/${router}`);
    app.use(r.path, r.router)
    logger.success(`('${router}' - '${r.path}') router loaded!`)
}

server.listen(port, async () => {
    logger.log(`App is listening on port ${port}`);
})


process.on("unhandledRejection", (reason, p) => {
    console.log(chalk.gray("————————————————————————————————————————————————————"));
    console.log(
       chalk.white("["),
       chalk.red.bold("AntiCrash"),
       chalk.white("]"),
       chalk.gray(" : "),
       chalk.white.bold("Unhandled Rejection/Catch")
    );
    console.log(chalk.gray("————————————————————————————————————————————————————"));
    console.log(reason, p);
 });
 process.on("uncaughtException", (err, origin) => {
    console.log(chalk.gray("————————————————————————————————————————————————————"));
    console.log(
       chalk.white("["),
       chalk.red.bold("AntiCrash"),
       chalk.white("]"),
       chalk.gray(" : "),
       chalk.white.bold("Uncaught Exception/Catch")
    );
    console.log(chalk.gray("————————————————————————————————————————————————————"));
    console.log(err, origin);
 });