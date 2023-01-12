import json
import os
import gevent
import bottle
import multiprocessing
from bottle import Bottle, request
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer
from gevent import monkey
from beaker.middleware import SessionMiddleware


monkey.patch_all()

def load_config(file_path):
    with open(file_path, 'r') as f:
        conf = json.load(f)
        # merge config
        main_owner = conf.get('owner', '*').split(',')
        main_ext = conf.get('ext_filter', '').split(',')
        for item in conf['www']:
            owner = main_owner
            if 'owner' in item:
                owner = item['owner'].split(',')
            item['owner'] = owner
            
            ext = main_ext
            if 'ext_filter' in item:
                ext = item['ext_filter'].split(',')
            item['ext_filter'] = ext
        return conf


pool_size = 256
backlog = 256
max_accept = 32767
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 600,
    'session.data_dir': 'sessions',
    'session.auto': True
}
app = Bottle()
script_path = os.path.split(os.path.realpath(__file__))[0] + os.sep
public_path = script_path + 'public'
config_path = script_path+'config.json'
config = load_config(config_path)


@app.route('/public/<filepath:path>')
def web_public(filepath):
    return bottle.static_file(filepath, public_path)


@app.route('/<filepath:path>')
def share_public(filepath):
    if filepath == 'favicon.ico':
        return bottle.static_file(filepath, public_path)
    sub_path = ''
    split_path = filepath.split('/')
    base_path = split_path[0]
    s = request.environ.get('beaker.session')
    user = s.get('user', None)
        
    for item in config['www']:
        owner = item['owner']
        if '*' not in owner and user not in owner:
            return bottle.template('error', code = 403)

        dest_path = item['path']
        if item['name'] != base_path:
            continue
        split_path.pop(0)
        sub_path = '/'.join(split_path)
        fpath = dest_path + '/' + sub_path
        if not os.path.exists(fpath):
            return bottle.template('error', code = 404)
        if not os.path.isdir(fpath):
            return bottle.static_file(sub_path, dest_path, download=True)

        items = os.listdir(fpath)
        split_path = filepath.split('/')
        split_path.pop() # remove last path
        paths = []
        paths.append({'path':'/', 'title':'/', 'size':0, 'type':'D'})
        paths.append({'path':'/' + '/'.join(split_path), 'title':'..', 'size':0, 'type':'D'})
        for d in items:
            base = os.path.basename(d)
            _, ext = os.path.splitext(base)
            if ext in item['ext_filter']:
                continue
            t = 'F'
            this_path = fpath + os.sep + d
            if os.path.isdir(this_path):
                t = 'D'
            size = os.path.getsize(this_path)
            url = '/%s/%s' % (filepath, base)
            paths.append({'path':url, 'title':base, 'size':size, 'type':t})
        return bottle.template('main', params = json.dumps(paths), user = user)
    return bottle.template('error', code = 404)


@app.route('/')
def share_index():
    s = request.environ.get('beaker.session')
    user = s.get('user', None)
    paths = []
    for item in config['www']:
        f = item['path']
        n = item['name']
        owner = item['owner']
        if '*' not in owner and user not in owner:
            continue
        if not os.path.exists(f):
            continue
        
        size = os.path.getsize(f)
        if os.path.isdir(f):
            sep = '/'
        paths.append({'path':sep+n, 'title':n+sep, 'size':size, 'type':'D'})
    return bottle.template('main', params = json.dumps(paths), user = user)


@app.route('/login')
def login_page():
    s = request.environ.get('beaker.session')
    user = s.get('user', None)
    if user!=None:
        return bottle.redirect('/')
    return bottle.template('login')


@app.route('/login', method="post")
def do_login():
    user = request.forms.get('user')
    passwd = request.forms.get('passwd')
    login_sucess = False
    for u in config['users']:
        if user != u['user']:
            continue
        if len(passwd)>0 and passwd==u['passwd']:
            login_sucess = True
            break

    if not login_sucess:
        print('%s login with %s failed' % (user, passwd))
        return bottle.redirect('/')

    s = request.environ.get('beaker.session')
    print('%s is login' % user)
    s['user'] = user
    s.save()
    print(s)
    return bottle.redirect('/')


@app.route('/logout')
def do_logout():
    s = request.environ.get('beaker.session')
    user = s.get('user', None)
    if user!=None:
        print('%s is logout' % user)
        s.delete()
    return bottle.redirect('/')


def run(addr, port):
    web_app = SessionMiddleware(app, session_opts)
    pool = Pool(pool_size)
    server = WSGIServer((addr, port), web_app, spawn=pool)
    server.backlog = backlog
    server.max_accept = max_accept
    server.serve_forever()

if __name__ == '__main__':
    print(config)
    for item in config['listen']:
        p = multiprocessing.Process(target=run, args=(item['addr'], item['port']))
        p.start()