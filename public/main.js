var page_size = 10;
var page_index = 0;
var total_pages = 0;

let set_page_size = function (size) {
    page_size = size;
    set_cookie('page_size', page_size, 3600);
}

let load_page_size = function () {
    set_page_size(parseInt(get_cookie('page_size') || 10));
}

let load_nav = function () {
    var show_class = user.length == 0 ? '.sign-out' : '.sign-in';
    var hide_class = user.length > 0 ? '.sign-out' : '.sign-in';
    var name = user.length == 0 ? 'None' : user;
    document.querySelector(hide_class).classList.add('visually-hidden');
    document.querySelector(show_class).classList.remove('visually-hidden');
    document.querySelectorAll('.user-name').forEach((v, i, all) => {
        v.textContent = name;
    });

    var paths = decodeURI(window.location.pathname).split('/');
    var bread = document.querySelector('.breadcrumb');
    bread.innerHTML = '';
    paths.forEach((v, i, all) => {
        var li = document.createElement('li');
        li.classList.add('breadcrumb-item');
        if (i == all.length - 1) {
            li.classList.add('active');
            li.textContent = v;
            li.setAttribute('aria-current', 'page');
            bread.appendChild(li);
            return;
        }
        var a = document.createElement('a');
        a.href = '../'.repeat(all.length - i - 1);
        a.textContent = v;
        li.appendChild(a);
        bread.appendChild(li);
    });
}

let get_size_with_unit = size => {
    let sizeUnit = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    var uIndex = 0;
    var uSize = size;
    while (uSize >= 1000) {
        uSize = uSize / 1000;
        uIndex++;
    }
    uSize = Math.ceil(uSize);
    let unit = sizeUnit[uIndex];
    return `${uSize}${unit}`;
};

let is_video = path => {
    let exts = ['.mp4', '.mkv', '.rm', '.rmvb', '.flv', '.webm', '.avi', '.wmv', '.mpg', '.ogg', '.mov', '.3gp', '.vob'];
    var found = false;
    exts.forEach(e => {
        if (path.endsWith(e)) {
            found = true;
            return;
        }
    });
    return found;
};

let reset_play_time = _ => {
    set_cookie('current_time', 0, 0);
};

let load_content = function () {
    var start = page_index * page_size;
    var end = start + page_size;
    end = end > params.length ? params.length : end;
    var items = params.slice(start, end);
    var tbody = document.querySelector('tbody');
    tbody.innerHTML = '';
    items.forEach((item, i, all) => {
        var tds = [
            document.createElement('td'),
            document.createElement('td'),
            document.createElement('td'),
            document.createElement('td')
        ];
        // File
        var a = document.createElement('a');
        a.href = item.path;
        a.textContent = item.title;
        tds[0].classList.add('text-truncate');
        tds[0].style.maxWidth = '200px';
        tds[0].style.textAlign = 'left';
        tds[0].appendChild(a);
        // Type
        tds[1].innerHTML = item.type;
        // Size
        tds[2].innerHTML = get_size_with_unit(item.size);
        // Action
        if (item.type === 'F' && is_video(item.title)) {
            var play = document.createElement('a');
            play.href = `/play${item.path}`;
            play.textContent = 'Play';
            play.setAttribute('onclick', 'reset_play_time()');
            tds[3].appendChild(play);
        }

        var tr = document.createElement('tr');
        tr.innerHTML = '';
        tr.appendChild(tds[0]);
        tr.appendChild(tds[1]);
        tr.appendChild(tds[2]);
        tr.appendChild(tds[3]);
        tbody.appendChild(tr);
    });
}

let load_footer = function () {
    load_page_size();
    document.querySelectorAll('.page-size-sel').forEach((v, i, all) => {
        v.onclick = e => {
            set_page_size(parseInt(v.innerHTML));
            load_pages();
            load_content();
        };
    });
    load_pages();
}

let load_pages = function () {
    total_pages = Math.floor(params.length / page_size) + (params.length % page_size > 0 ? 1 : 0);
    if (page_index >= total_pages - 1) {
        page_index = total_pages - 1;
    }
    document.querySelector('.page-size').innerHTML = page_size;
    var ul = document.querySelector('.page-items');
    ul.innerHTML = '';
    for (var i = 0; i < total_pages; i++) {
        var a = document.createElement('a');
        var li = document.createElement('li');
        a.classList.add('dropdown-item');
        a.classList.add('page-index-sel');
        a.innerHTML = i + 1;
        li.appendChild(a);
        ul.appendChild(li);
    }
    setTimeout(_ => {
        document.querySelectorAll('.page-index-sel').forEach((v, i, all) => {
            v.onclick = sel_page;
        });
    }, 10);
    document.querySelector('.page-start').onclick = start_page;
    document.querySelector('.page-end').onclick = end_page;
    document.querySelector('.page-prev').onclick = prev_page;
    document.querySelector('.page-next').onclick = next_page;
    switch_page(page_index, total_pages);
}

let sel_page = function (e) {
    page_index = parseInt(e.target.innerHTML) - 1;
    //switch_page(page_index, total_pages);
    url_switch_page();
}

let start_page = function (e) {
    page_index = 0;
    //switch_page(page_index, total_pages);
    url_switch_page();
};

let end_page = function (e) {
    page_index = total_pages - 1;
    //switch_page(page_index, total_pages);
    url_switch_page();
};

let next_page = function (e) {
    if (page_index < total_pages - 1) {
        page_index++;
    }
    //switch_page(page_index, total_pages);
    url_switch_page();
}

let prev_page = function (e) {
    if (page_index > 0) {
        page_index--;
    }
    //switch_page(page_index, total_pages);
    url_switch_page();
}

let url_switch_page = () => {
    var url = window.location.href.split('?')[0];
    window.location.href = `${url}?page_index=${page_index}&page_size=${page_size}`;
};

let switch_page = function (index, total) {
    // console.log(index, total);
    document.querySelector('.page-index').innerHTML = `${index + 1}/${total}`;
    var page_start = document.querySelector('.page-start');
    var page_end = document.querySelector('.page-end');
    var page_prev = document.querySelector('.page-prev');
    var page_next = document.querySelector('.page-next');

    page_start.classList.remove('disabled');
    page_prev.classList.remove('disabled');
    page_end.classList.remove('disabled');
    page_next.classList.remove('disabled');

    if (index == 0) {
        if (!page_start.classList.contains('disabled')) {
            page_start.classList.add('disabled');
        }
        if (!page_prev.classList.contains('disabled')) {
            page_prev.classList.add('disabled');
        }
    }
    if (index == total - 1) {
        if (!page_end.classList.contains('disabled')) {
            page_end.classList.add('disabled');
        }
        if (!page_next.classList.contains('disabled')) {
            page_next.classList.add('disabled');
        }
    }
    load_content();
}

let load_query = _ => {
    var paras = parse_query();
    var query = {};
    query.page_index = parseInt(paras.page_index) || 0;
    query.page_size = parseInt(paras.page_size) || 10;

    set_page_size(query.page_size);
    page_index = query.page_index || 0;
};

let init_page = function () {
    load_query();
    load_nav();
    load_content();
    load_footer();
}

window.onload = init_page;
