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

let parse_query = () => {
    var url = window.location.search.trim(); // 获取url中"?"符后的字串
    var query = {};
    if (url.indexOf("?") < 0) {
        return query;
    }
    var str = url.substring(1);
    var strs = str.split("&");
    strs.forEach(v => {
        var kv = v.split("=");
        query[kv[0]] = decodeURI(kv[1]);
    });
    return query;
};

let to_query_string = (query) => {
    var str = '';
    for (var k in query.keys) {
        str += `${k}=${query[k]}`;
    }
    str = str.length > 0 ? '?' + str : str;
    return str;
};