import m3u8
import os
import requests


proxies = {
    'http': 'http://127.0.0.1:1080',
    'https': 'http://127.0.0.1:1080',
}


class RequestsClient():
    def download(self, uri, timeout=None, headers={}, verify_ssl=True):
        o = requests.get(uri, timeout=timeout, headers=headers, proxies=proxies)
        return o.text, o.url


def set_proxies(uri):
    proxies['http'] = uri
    proxies['https'] = uri


def down_ts(ts_url, name, num_retries):
    print(f'remain {num_retries}, down {ts_url}, to {name}')
    try:
        with requests.get(ts_url, stream=True, timeout=(5, 60), verify=False, headers={}) as res:
            if res.status_code != 200:
                print(res.status_code)
                if num_retries > 0: 
                    down_ts(ts_url, name, num_retries - 1)
                return
            with open(name, "wb") as ts:
                for chunk in res.iter_content(chunk_size=1024):
                    if chunk == None:
                        continue
                    ts.write(chunk)
    except Exception as e:
        if os.path.exists(name):
            os.remove(name)
        if num_retries > 0:
            down_ts(ts_url, name, num_retries - 1)


def down(uri, save_path):
    print(f'get {uri}')
    variant_m3u8 = m3u8.load(uri, http_client=RequestsClient())
    f = os.path.basename(uri)
    base_uri = uri.removesuffix(f)
    if variant_m3u8.is_variant:
        playlist = variant_m3u8.playlists[0]
        print(f'select {playlist.stream_info.bandwidth}: {playlist.uri}')
        u = playlist.uri 
        if '://' not in u:
            u = base_uri + u
        down(u, save_path)
        return
    
    save_path += os.sep
    if not os.path.exists(save_path):
        os.mkdir(save_path)

    for segment in variant_m3u8.segments:
        tsu = segment.uri
        file = save_path + os.path.basename(tsu)
        if '://' not in tsu:
            tsu = base_uri + segment.uri
        down_ts(tsu, file, 3)
