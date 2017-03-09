import os
import requests
import traceback
import urlparse
import random
from gevent import Timeout
from gevent import monkey
import requests.packages.urllib3


monkey.patch_all()
requests.packages.urllib3.disable_warnings()


servers = {
    "apache": "php",
    "iis": "asp",
    "tomcat": "jsp",
    "jboss": "jsp",
    "weblogic": "jsp",
    "websphere": "jsp"
}
random_files = [
            "public/root.rar",
            "1111/2222/..git/config",
            "............................etc/passwd"
        ]
USER_AGENTS = [
    "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
    "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML,"
    " like Gecko, Safari/419.3) Arora/0.6",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2p"
    "re) Gecko/20070215 K-Ninja/2.1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9)"
    " Gecko/20080705 Firefox/3.0 Kapiko/3.0",
    "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
    "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko"
    " Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
    "Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Prest"
    "o/2.9.168 Version/11.52",
]
headers = {
    "User-Agent": random.choice(USER_AGENTS)
}
extion = "php"
path = os.path.realpath(os.path.dirname(__file__))


def get_dict_by_server(head={}):
    dicts = set()
    try:
        server = ""
        keys = head.keys()
        if 'Server' in keys:
            server = head['Server'].lower()
        if server:
            for s in servers:
                if s in server:
                    file_path = os.path.abspath(os.path.join(path, "../dict/server/{}.txt".format(s)))
                    with open(file_path) as f:
                        keys = f.readlines()
                        for i in keys:
                            dicts.add(i.strip('\n'))
    except:
        traceback.print_exc()
    finally:
        return dicts


def get_extion_by_sever(url):
    extion = 'php'
    try:
        r = _requests(url)
        if isinstance(r, bool):
            return extion
        head = r.headers
        if 'Server' in head:
            server = head['Server'].lower()
            for s in servers:
                if s in server:
                    extion = servers[s]
                    break
    except:
        traceback.print_exc()
    finally:
        return extion


def get_site_stander(url):
    standers = {}
    try:
        infos = {}
        for file in random_files:
            url = urlparse.urljoin(url, file)
            r = _requests(
                url, timeout=10, headers=headers,
                allow_redircets=True
            )
            if isinstance(r, bool):
                continue
            infos[url] = {
                'code': r.status_code,
                'text': r.text,
                'headers': r.headers,
                'url': r.url
            }
        flag = filter(
            lambda x: infos[x]['code'] == 200, infos
        )
        if flag:
            _ = set()
            for i in infos:
                _.add(infos[i]['text'])
            standers['text'] = list(_)
        else:
            standers['code'] = 200
    except:
        traceback.print_exc()
    finally:
        return standers


def _requests(url, **kwargs):
    url = url
    params = _parse_params(kwargs)
    with Timeout(20, False) as _:
        if params['data']:
            try:
                r = requests.post(
                    url, data=params['data'],
                    headers=params['headers'],
                    verify=params['verify'],
                    stream=params['stream'],
                    allow_redirects=params['allow_redirects']
                )
                return r
            except:
                return False
        else:
            try:
                r = requests.get(
                    url, data=params['data'],
                    headers=params['headers'],
                    verify=params['verify'],
                    allow_redirects=params['allow_redirects']
                )
                return r
            except:
                return False
    return False


def _parse_params(kwargs):
    params = {}
    try:
        params['data'] = kwargs['data']
    except:
        params['data'] = ''
    try:
        params['headers'] = kwargs['headers']
    except:
        params['headers'] = {}
    try:
        params['verify'] = kwargs['verify']
    except:
        params['verify'] = False
    try:
        params['steam'] = kwargs['steam']
    except:
        params['steam'] = True
    try:
        params['allow_redirects'] = kwargs['allow_redirects']
    except:
        params['allow_redirects'] = True
    return params
