const express = require('express');
//const cors = require('cors');
const app = express();
const html = __dirname + '/public'
//var youtubedl = require('youtube-dl');
/*
var corsOptions = {
    //origin: 'http://localhost:8080/',
    origin: '172.31.26.194:80/',
    optionsSuccessStatus: 200
}
app.use(cors(corsOptions));
*/
app.use(function (req, res, next) {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Access-Control-Allow-Credentials', true);
    next();
});

//TODO try to use youtube-dl te get id

app.listen(80, () => console.log('Application listening on port 80'))
app.use('/static', express.static('static'));
app.use(express.static(html))
app.get('/vids/:vid', (req, res) => {
    //var videoLink = decodeURIComponent(req.params.vid);

    //console.log(videoLink);
    var vidLink = req.params.vid;
    console.log('Node says: received \"' + vidLink + '\" from Angular');
    var runPy = new Promise(function (success, nosuccess) {
        var  spawn  = require('child_process');
        console.log("Node.js calling python with argument: " + vidLink)
        var pyprog = spawn('python', ["/home/ubuntu/videoBlender/server/python/vidBlend.py", vidLink]);
        // on laptop call python2
        //const pyprog = spawn('python2', ["C:/_sw/fooNode/fooPyScripts/vidBlend.py", vidLink]);
        pyprog.stdout.on('data', function (data) { success(data); });
        pyprog.stderr.on('data', (data) => { nosuccess(data); });
    });


    runPy.then(function (fromRunpy) {
        //console.log("Message returned from python is: " + fromRunpy.toString());
        res.send(fromRunpy);
        //console.log('finished running')
    });


})
