let init_nav = function() {
    var show_class = user.length==0?'.sign-out':'.sign-in';
    var hide_class = user.length>0?'.sign-out':'.sign-in';
    var name = user.length==0?'None':user;
    document.querySelector(hide_class).classList.add('visually-hidden');
    document.querySelector(show_class).classList.remove('visually-hidden');
    document.querySelectorAll('.dropdown-toggle').forEach((v,i,all)=>{
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

let init_content = function() {
    var tbody = document.querySelector('tbody');
    tbody.innerHTML = '';
    params.forEach((item,i,all)=>{
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

let init_footer = function() {
    
}

let init_page = function() {
    init_nav();
    init_content();
    init_footer();
}

window.onload = init_page;
