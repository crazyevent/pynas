var heartbeatInterval = 10000;
var options = {};
let videoTemplate = src =>
    `<video
        id="my-player"
        class="video-js"
        controls
        preload="auto"
        poster="//vjs.zencdn.net/v/oceans.png"
        data-setup='{}'
        style="width: 100%; height: 100%; object-fit: fill">
            <source src="${src}" type="application/x-mpegURL"></source>
            <p class="vjs-no-js">
            To view this video please enable JavaScript, and consider upgrading to a
            web browser that
            <a href="https://videojs.com/html5-video-support/" target="_blank">
                supports HTML5 video
            </a>
        </p>
    </video>`;

let createPlayer = (opts, src) => {
    document.querySelector('.section_2').innerHTML = videoTemplate(src);

    var player = videojs('my-player', opts, function onPlayerReady() {
        //videojs.log('Your player is ready!');

        // In this context, `this` is the player that was created by Video.js.
        this.play();

        // How about an event listener?
        this.on('ended', function () {
            //videojs.log('Awww...over so soon?!');
        });
    });
    return player;
};

let getQueryValue = (key) => {
    var reg = new RegExp("(^|&)" + key + "=([^&]*)(&|$)", "i");
    var r = window.location.search.substring(1).match(reg); // 获取url中"?"符后的字符串并正则匹配
    var context = "";
    if (r != null)
        context = decodeURIComponent(r[2]);
    reg = null;
    r = null;
    return context == null || context == "" || context == "undefined" ? "" : context;
};

let heartbeat = url => {
    $.get(url, res => {
        // nothing todo
    });
    setTimeout(_=>{
        heartbeat(url);
    }, heartbeatInterval);
};

let checkHlsPrepared = async key => {
    var res = await new Promise((resolve, reject) => {
        $.get(`/isprepared/${key}`, resolve);
    });
    if (res.code != 0) {
        console.error(res);
        return;
    }
    if (!res.prepared) {
        setTimeout(_ => {
            checkHlsPrepared(key);
        }, 1000);
        return;
    }
    createPlayer(options, res.hls);
    // keep hls alive
    heartbeat(res.hls);
};

window.onload = async _ => {
    var res = await new Promise((resolve, reject) => {
        $.get(`/prepare${getQueryValue('f')}`, resolve);
    });
    if (res.code != 0) {
        console.error(res);
        return;
    }
    setTimeout(_ => {
        checkHlsPrepared(res.key);
    }, 1000);
}