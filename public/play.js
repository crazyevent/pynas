var heartbeatInterval = 10000;
var options = {
    autoplay: true
};
let videoTemplate = (src,vtt) =>
    `<video
        id="my-player"
        class="video-js"
        controls
        muted="muted"
        preload="auto"
        poster="//vjs.zencdn.net/v/oceans.png"
        data-setup='{}'
        style="width: 100%; height: 100%; object-fit: fill">
            <source src="${src}" type="application/x-mpegURL"></source>
            <track kind="captions" src="${vtt}" srclang="zh" label="Chinese" default />
            <p class="vjs-no-js">
            To view this video please enable JavaScript, and consider upgrading to a
            web browser that
            <a href="https://videojs.com/html5-video-support/" target="_blank">
                supports HTML5 video
            </a>
        </p>
    </video>`;

let createPlayer = (opts, src, vtt) => {
    document.querySelector('.section_2').innerHTML = videoTemplate(src, vtt);

    var player = videojs('my-player', opts, function onPlayerReady() {
        //videojs.log('Your player is ready!');

        // In this context, `this` is the player that was created by Video.js.
        var currTime = get_cookie('current_time') || 0;
        this.currentTime(currTime);
        this.play();

        // How about an event listener?
        this.on('ended', _ => {
            //videojs.log('Awww...over so soon?!');
        });

        this.on('timeupdate', _ => {
            // record play time
            set_cookie('current_time', this.currentTime(), 3600);
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
    createPlayer(options, res.hls, res.vtt);
    // keep hls alive
    heartbeat(res.hls);
};

window.onload = async _ => {
    document.querySelector('.btn').onclick = e => {
        window.location.href = window.location.href + '&muxer_mode=1';
    };

    var res = await new Promise((resolve, reject) => {
        $.get(`/prepare${getQueryValue('f')}`, resolve);
    });
    if (res.code != 0) {
        console.error(res);
        return;
    }
    checkHlsPrepared(res.key);
}