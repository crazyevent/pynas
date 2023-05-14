let get_cookie = function (key) {
    var val;
    //console.log(document.cookie, key);
    document.cookie.split(';').forEach((item, i, all) => {
        var ret = item.trim().split('=');
        if (ret[0] == key) {
            val = ret[1];
            //console.log('found', ret[0], ret[1]);
            return;
        }
    });
    return val;
}

let set_cookie = function (key, val, expire) {
    document.cookie = `${key}=;expires=0;path=/`;
    document.cookie = `${key}=${val};expires=${new Date(Date.now() + expire)};path=/`;
}