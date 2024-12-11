const express = require("express");
const { path } = require("./main");
const router = express.Router();


router.get("/import/:app/:pattern/", async (req, res) => {

    let app = req.params.app;
    let pattern = req.params.pattern;
    var url = req.query.url;

    if (!url) return res
        .status(400)
        .send("bad usage");

    url = url.replace("@", `http://${req.headers.host}`);

    return res.status(301).redirect(`${app}://${pattern}?url=${url}`);

});

router.get("/raw-import", async (req, res) => {

    var url = req.query.url;

    if (!url) return res
        .status(400)
        .send("bad usage");

    url = url.replace("@", `http://${req.headers.host}`);

    return res.status(301).redirect(url);

});


module.exports = {
    path: "/",
    router: router,
};
