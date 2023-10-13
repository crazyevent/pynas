import json
import os
from string import Template
import subprocess
import sys
import threading
import time
import gevent
import bottle
import multiprocessing
import hashlib
from cgi import parse_header
import re
from bottle import Bottle, request
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer
from gevent import monkey
from beaker.middleware import SessionMiddleware


monkey.patch_all()


def load_config(file_path):
    with open(file_path, 'r') as f:
        conf = json.load(f)
        if 'session_expires' not in conf:
            conf['session_expires'] = 600
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
app = Bottle()
script_path = os.path.split(os.path.realpath(__file__))[0] + os.sep
public_path = script_path + 'public'
config_path = script_path + 'config.json'
hls_path = script_path + 'hls'
config = load_config(config_path)
session_opts = {
    'session.type': 'file',
    'session.cookie_expires': config['session_expires'] ,
    'session.data_dir': 'sessions',
    'session.auto': True
}

'''
key=md5(hls-full-path),
value=
{
    ts: latest_access
    prepared: true
    proc: subprocess
    hls_full: hls_full_path
    media: media_path
    hls: hls_play_path
}
'''
hls_media_map = {}


def md5(content):
    if content is None:
        return ''
    md5gen = hashlib.md5()
    md5gen.update(content.encode())
    md5code = md5gen.hexdigest()
    md5gen = None
    return md5code


def convert_to_utf8(data):
    """
    @brief string convert to utf8 string
    @param data: string to be convert
    @return utf8 string
    """
    if isinstance(data, str):
        return data.encode('utf-8')
    elif isinstance(data, bytes):
        return data.decode('utf-8').encode('utf-8')
    elif isinstance(data, dict):
        return {convert_to_utf8(key): convert_to_utf8(value) for key, value in data.items()}
    elif isinstance(data, (list, tuple)):
        return type(data)(convert_to_utf8(element) for element in data)
    else:
        return data


def clear_hls_cache(item):
    # item['proc'].communicate(input='q')
    # item['proc'].wait()
    # item['proc'].terminate()
    # item['proc'].kill()
    # it's the best way to kill process for now
    if sys.platform == 'win32':
        p = subprocess.Popen('taskkill /F /PID ' + str(item['proc'].pid))
    else:
        p = subprocess.Popen('kill -9 ' + str(item['proc'].pid))
    p.wait()
    hls_full = item['hls_full']
    files = os.listdir(hls_full)
    for f in files:
        os.remove(hls_full + os.sep + f)
    os.rmdir(hls_full)


def check_hls_timeout():
    keys = []
    for k, v in hls_media_map.items():
        now = time.clock()
        if now - v['ts'] >= 30:
            print(k + ' is timeout')
            keys.append(k)
            clear_hls_cache(v)
    for key in keys:
        hls_media_map.pop(key)
    threading.Timer(5, check_hls_timeout).start()


def is_hls_compat(path):
    _, ext = os.path.splitext(path)
    if len(ext) == 0:
        return False
    exts = ['.rm', '.rmvb', '.avi', '.wmv', '.flv', '.mpg']
    return ext not in exts


def prepare_media(hls_base_path, media_path, muxer_mode):
    key = md5(media_path)
    fpath = hls_base_path + os.sep + key
    if key in hls_media_map:
        if muxer_mode == hls_media_map[key]['muxer_mode']:
            return key
        clear_hls_cache(hls_media_map[key])

    if (not os.path.exists(fpath)):
        os.mkdir(fpath)
    hls = '/hls/' + key + '/' + 'index.m3u8'
    hls_full = fpath + os.sep + 'index.m3u8'
    cmd = ''
    if is_hls_compat(media_path) and muxer_mode == 0:
        cmd = 'ffmpeg -i "' + media_path + '" -c:v copy -c:a copy -f hls -hls_list_size 0 "' + \
            hls_full + '"'
    else:
        cmd = 'ffmpeg -i "' + media_path + '" -c:v h264_qsv -c:a aac -f hls -hls_list_size 0 "' + \
            hls_full + '"'
    print(cmd)
    p = subprocess.Popen(cmd,
        shell=False,
        stdout=sys.stdout,
        stderr=sys.stderr,
        )
    hls_media_map[key] = {'ts': time.clock(),
        'prepared': False,
        'proc': p,
        'hls_full': fpath,
        'media': media_path,
        'hls': hls,
        'muxer_mode': muxer_mode}
    return key


@ app.route('/prepare/<filepath:path>')
def prepare_hls(filepath):
    muxer_mode = int(request.query.muxer_mode or '0')
    base_path = ''
    split_path = filepath.split('/')
    path_name = split_path[0]
    for item in config['www']:
        if item['name'] != path_name:
            continue
        base_path = item['path']
        break
    if len(base_path) == 0:
        return {'code': 404}
    split_path.pop(0)
    media_path = base_path + os.sep + '/'.join(split_path)
    key = prepare_media(hls_path, media_path, muxer_mode)
    return {'code': 0, 'key': key, 'prepared': False}


@ app.route('/isprepared/<key>')
def check_hls_prepared(key):
    if key not in hls_media_map:
        return {'code': 404}
    item = hls_media_map[key]
    ret = len(os.listdir(item['hls_full'])) > 0
    hls_media_map[key]['prepared'] = ret
    data = {'code': 0, 'key': key, 'prepared': ret, 'hls': item['hls']}
    data['vtt'] = '/hls/' + key + '/' + 'index_vtt.m3u8'
    return data


@ app.route('/hls/<filepath:path>')
def play_hls(filepath):
    split_path = filepath.split('/')
    key = split_path[0]
    if key in hls_media_map:
        hls_media_map[key]['ts'] = time.clock()
    return bottle.static_file(filepath, hls_path)


@ app.route('/play/<filepath:path>')
def do_play(filepath):
    return bottle.template('play', filepath=filepath)


@ app.route('/public/<filepath:path>')
def web_public(filepath):
    return bottle.static_file(filepath, public_path)


@ app.route('/<filepath:path>')
def share_public(filepath):
    if filepath == 'favicon.ico':
        return bottle.static_file(filepath, public_path)
    sub_path = ''
    split_path = filepath.split('/')
    base_path = split_path[0]
    s = request.environ.get('beaker.session')
    user = s.get('user', None)

    for item in config['www']:
        dest_path = item['path']
        if item['name'] != base_path:
            continue

        owner = item['owner']
        if '*' not in owner and user not in owner:
            return bottle.template('error', code=403)
        
        split_path.pop(0)
        sub_path = '/'.join(split_path)
        fpath = dest_path + '/' + sub_path
        if not os.path.exists(fpath):
            return bottle.template('error', code=404)
        if not os.path.isdir(fpath):
            return bottle.static_file(sub_path, dest_path, download=True)

        items = os.listdir(fpath)
        split_path = filepath.split('/')
        split_path.pop()  # remove last path
        paths = []
        paths.append({'path': '/', 'title': 'root', 'size': 0, 'type': 'D'})
        paths.append({'path': '/' + '/'.join(split_path),
            'title': 'parent', 'size': 0, 'type': 'D'})
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
            paths.append({'path': url, 'title': base, 'size': size, 'type': t})
        return bottle.template('main', params=json.dumps(paths), user=user)
    return bottle.template('error', code=404)


@ app.route('/')
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
        paths.append({'path': sep+n, 'title': n +
            sep, 'size': size, 'type': 'D'})
    return bottle.template('main', params=json.dumps(paths), user=user)


@ app.route('/login')
def login_page():
    s = request.environ.get('beaker.session')
    user = s.get('user', None)
    if user != None:
        return bottle.redirect('/')
    return bottle.template('login')


@ app.route('/login', method="post")
def do_login():
    user = request.forms.get('user')
    passwd = request.forms.get('passwd')
    login_sucess = False
    for u in config['users']:
        if user != u['user']:
            continue
        if len(passwd) > 0 and passwd == u['passwd']:
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


@ app.route('/logout')
def do_logout():
    s = request.environ.get('beaker.session')
    user = s.get('user', None)
    if user != None:
        print('%s is logout' % user)
        s.delete()
    return bottle.redirect('/')


@ app.route('/upload', method='POST') 
def do_upload():
    updir = config['updir']
    if len(updir) == 0:
        return {'code': 403, 'msg': 'reject'}
    
    #content_len = request.content_length
    _, dispos = parse_header(request.headers.get('Content-Disposition'))
    filename = dispos['filename']
    if len(filename) == 0:
        return {'code': 403, 'msg': 'reject'}
    
    range, _ = parse_header(request.headers.get('Content-Range'))
    if len(range) == 0:
        return {'code': 403, 'msg': 'reject'}
    match = re.match(r"bytes (\d+)-(\d+)/(\d+)", range)
    start = int(match.group(1))
    end = int(match.group(2))
    total = int(match.group(3))
    if end >= total:
        return {'code': 403, 'msg': 'reject'}

    save_file = f'{updir}{filename}'
    progress = end + 1
    with open(save_file, 'a+b') as f:
        f.seek(start)
        f.write(request.body.read())
        f.seek(progress)
        f.truncate()
    return {'code': 200, 'filename': filename, 'progress': progress, 'msg': 'success'}


def run(addr, port):
    check_hls_timeout()

    web_app = SessionMiddleware(app, session_opts)
    pool = Pool(pool_size)
    server = WSGIServer((addr, port), web_app, spawn=pool)
    server.backlog = backlog
    server.max_accept = max_accept
    server.serve_forever()


if __name__ == '__main__':
    print(config)
    for item in config['listen']:
        p = multiprocessing.Process(
            target=run, args=(item['addr'], item['port']))
        p.start()
