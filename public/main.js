var page_size = 10;
var page_index = 0;
var total_pages = 0;

let get_cookie = function(key) {
    var val;
    console.log(document.cookie, key);
    document.cookie.split(';').forEach((item,i,all)=>{
        var ret = item.trim().split('=');
        if (ret[0] == key) {
            val = ret[1];
            console.log('found', ret[0],  ret[1]);
            return;
        }
    });
    return val;
}

let set_cookie = function(key, val, expire) {
    document.cookie = `${key}=;expires=0;path=/`;
    document.cookie = `${key}=${val};expires=${new Date(Date.now() + expire)};path=/`;
}

let set_page_size = function(size) {
    page_size = size;
    set_cookie('page_size', page_size, 3600);
}

let load_page_size = function() {
    set_page_size(parseInt(get_cookie('page_size') || 10));
}

let load_nav = function() {
    var show_class = user.length==0?'.sign-out':'.sign-in';
    var hide_class = user.length>0?'.sign-out':'.sign-in';
    var name = user.length==0?'None':user;
    document.querySelector(hide_class).classList.add('visually-hidden');
    document.querySelector(show_class).classList.remove('visually-hidden');
    document.querySelectorAll('.user-name').forEach((v,i,all)=>{
        v.textContent = name;
    });

    var paths = decodeURI(window.location.pathname).split('/');
    var bread = document.querySelector('.breadcrumb');
    bread.innerHTML = '';
    paths.forEach((v,i,all)=>{
        var li = document.createElement('li');
        li.classList.add('breadcrumb-item');
        if (i == all.length-1) {
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

let load_content = function() {
    var start = page_index*page_size;
    var end = start + page_size;
    end = end>params.length ? params.length : end;
    var items = params.slice(start, end);
    var tbody = document.querySelector('tbody');
    tbody.innerHTML = '';
    items.forEach((item,i,all)=>{
        var tr = document.createElement('tr');
        var tds = [document.createElement('td'),
            document.createElement('td'),
            document.createElement('td')];
        var a = document.createElement('a');
        a.href = item.path;
        a.textContent = item.title;
        tds[0].classList.add('text-truncate');
        tds[0].style.maxWidth = '200px';
        tds[0].style.textAlign = 'left';
        tds[0].appendChild(a);
        tds[1].innerHTML = item.type;
        tds[2].innerHTML = item.size;
        tr.innerHTML = '';
        tr.appendChild(tds[0]);
        tr.appendChild(tds[1]);
        tr.appendChild(tds[2]);
        tbody.appendChild(tr);
    });
}

let load_footer = function() {
    load_page_size();
    document.querySelectorAll('.page-size-sel').forEach((v,i,all)=>{
        v.onclick = e =>{
            set_page_size(parseInt(v.innerHTML));
            load_pages();
            load_content();
        };
    });
    load_pages();
}

let load_pages = function() {
    total_pages = Math.floor(params.length / page_size) + (params.length%page_size>0?1:0);
    if (page_index>=total_pages-1) {
        page_index = total_pages - 1;
    }
    document.querySelector('.page-size').innerHTML = page_size;
    var ul = document.querySelector('.page-items');
    ul.innerHTML = '';
    for(var i=0; i<total_pages; i++) {
        var a = document.createElement('a');
        var li = document.createElement('li');
        a.classList.add('dropdown-item');
        a.classList.add('page-index-sel');
        a.innerHTML = i+1;
        li.appendChild(a);
        ul.appendChild(li);
    }
    setTimeout(_=>{
        document.querySelectorAll('.page-index-sel').forEach((v,i,all)=>{
            v.onclick = e => {
                page_index = parseInt(e.target.innerHTML) - 1;
                switch_page(page_index, total_pages);
            };
        });
    }, 10);
    document.querySelector('.page-start').onclick = e=>{
        page_index = 0;
        switch_page(page_index, total_pages);
    };
    document.querySelector('.page-end').onclick = e=>{
        page_index = total_pages-1;
        switch_page(page_index, total_pages);
    };
    document.querySelector('.page-prev').onclick = prev_page;
    document.querySelector('.page-next').onclick = next_page;
    switch_page(page_index, total_pages);
}

let next_page = function() {
    if (page_index<total_pages-1) {
        page_index++;
    }
    switch_page(page_index, total_pages);
}

let prev_page = function() {
    if (page_index>0) {
        page_index--;
    }
    switch_page(page_index, total_pages);
}

let switch_page = function(index, total) {
    console.log(index,total);
    document.querySelector('.page-index').innerHTML = `${index+1}/${total}`;
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
    if (index == total-1) {
        if (!page_end.classList.contains('disabled')) {
            page_end.classList.add('disabled');
        }
        if (!page_next.classList.contains('disabled')) {
            page_next.classList.add('disabled');
        }
    }
    load_content();
}

let init_page = function() {
    load_nav();
    load_content();
    load_footer();
}

window.onload = init_page;
