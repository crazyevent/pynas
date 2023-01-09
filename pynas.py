import json
import os
import gevent
import bottle
import multiprocessing
from bottle import Bottle
from gevent.pool import Pool
from gevent.pywsgi import WSGIServer
from gevent import monkey


monkey.patch_all()
config_file = './config.json'
max_filename_len = 40


def load_config(file_path):
    with open(file_path, 'r') as f:
        config = json.load(f)
        return config


config = load_config(config_file)
app = Bottle()
public_path = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'public'


@app.route('/public/<filepath:path>')
def web_views(filepath):
    return bottle.static_file(filepath, public_path)


@app.route('/<filepath:path>')
def share_public(filepath):
    sub_path = ''
    split_path = filepath.split('/')
    base_path = split_path[0]
        
    for item in config['www']:
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

        outstr = ''
        items = os.listdir(fpath)
        split_path = filepath.split('/')
        split_path.pop() # remove last path
        paths = []
        for d in items:
            size = os.path.getsize(fpath + os.sep + d)
            base = os.path.basename(d)
            url = '/%s/%s' % (filepath, base)
            paths.append({'path':url, 'title':base, 'size':size})
        return bottle.template('main', items = paths)
    return bottle.template('error', code = 404)


@app.route('/')
def share_index():
    config = load_config(config_file)
    paths = []
    for item in config['www']:
        f = item['path']
        n = item['name']
        if not os.path.exists(f):
            continue
        size = os.path.getsize(f)
        if os.path.isdir(f):
            sep = '/'
        paths.append({'path':sep+n, 'title':n+sep, 'size':size})
    return bottle.template('main', items = paths)
    

def run(addr, port):
    pool = Pool(256)
    server = WSGIServer((addr, port), app, spawn=pool)
    server.backlog = 256
    server.max_accept = 30000
    server.serve_forever()

if __name__ == '__main__':
    print(config)
    for item in config['listen']:
        p = multiprocessing.Process(target=run, args=(item['addr'], item['port']))
        p.start()