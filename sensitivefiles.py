# -*- coding:utf-8 -*-
# !/usr/bin/env python


import traceback
import re
import requests
import random
import urlparse
import argparse
from lxml import etree
from gevent import Timeout
from gevent.pool import Pool
from gevent.queue import Queue
from gevent.queue import Empty
from gevent import event
from gevent.lock import Semaphore
from gevent import monkey
import requests.packages.urllib3


requests.packages.urllib3.disable_warnings()
monkey.patch_all()


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


class Scanner(object):
    def __init__(self, url, extion, depth, nums):
        self.target = url
        self.headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }
        self.suffixs = ['.php', '.asp', '.jsp', '.do', '.action', '.aspx']
        self.random_files = [
            "........www.rar",
            "1111/2222/..git/config",
            "............................etc/passwd"
        ]
        self.q = Queue()
        self.urls = set()
        self.result = []
        self.depth = depth
        self.threshold = 0.75
        self.extion = extion
        self.sem = Semaphore()
        self.concurrent_num = nums
        self.crawl_pool = Pool(self.concurrent_num)
        self.fuzz_pool = Pool(self.concurrent_num)
        self.filter_urls = set()
        self.flag = event.Event()
        self.fuzzflag = event.Event()
        self.fuzz_queue = Queue()
        self.standers = {}
        self.black_suffixs = [
            ".jpg", '.png', '.gif', '.js', '.css',
            '.avi', '.pdf', '.exe', '.doc', '.xls'
        ]

    def parse_content(self, content, current_url):
        links = set()
        try:
            page = etree.HTML(content)
            for t in ['a', 'area']:
                a_tags = page.xpath(u'//{}'.format(t))
                for a_tag in a_tags:
                    link = a_tag.get('href')
                    if len(links) > 20:
                        continue
                    if not link:
                        continue
                    if not link.startswith('http'):
                        link = urlparse.urljoin(current_url, link)
                    netloc = urlparse.urlparse(link).netloc
                    if netloc != self.target_domain:
                        continue
                    flag = any(
                        map(
                            lambda x: link.split('?')[0].endswith(x),
                            self.black_suffixs
                        )
                    )
                    if flag:
                        self.urls.add(link)
                        continue
                    rules = re.sub('=[^&$]+', '=*', link)
                    if rules in self.filter_urls:
                        continue
                    links.add(link)
                    self.filter_urls.add(rules)
            for t in ['img', 'script']:
                a_tags = page.xpath(u'//{}'.format(t))
                for a_tag in a_tags:
                    link = a_tag.get('src')
                    if not link:
                        continue
                    if not link.startswith('http'):
                        link = urlparse.urljoin(current_url, link)
                    netloc = urlparse.urlparse(link).netloc
                    if netloc != self.target_domain:
                        continue
                    self.urls.add(link)
        except:
            pass
        return links

    def crawl(self):
        try:
            while not self.flag.isSet():
                try:
                    link = self.q.get_nowait()
                except Empty:
                    self.flag.set()
                    continue
                except:
                    continue
                r = self._requests(link, headers=self.headers)
                if isinstance(r, bool):
                    continue
                current_url = r.url
                text = r.text
                links = self.parse_content(text, current_url)
                self.cacheurls.update(links)
        except:
            traceback.print_exc()

    def start(self):
        try:
            self.flag = event.Event()
            self.cacheurls = set()
            for i in xrange(self.concurrent_num):
                self.crawl_pool.apply(self.crawl,)
            self.crawl_pool.join()
            next_urls = self.cacheurls.difference(self.urls)
            for url in next_urls:
                self.q.put(url)
            self.urls.update(next_urls)
        except:
            traceback.print_exc()

    def _requests(self, url, **kwargs):
        url = url
        print url
        params = _parse_params(kwargs)
        with Timeout(20, False) as timeout:
            if params['data']:
                try:
                    r = requests.post(
                        url, data=params['data'],
                        headers=params['headers'],
                        verify=params['verify'],
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

    def scan(self):
        self.target_domain = urlparse.urlparse(self.target).netloc
        self.scheme = urlparse.urlparse(self.target).scheme
        print "start crawl"
        print "*********************"
        r = self._requests(self.target, headers=self.headers)
        if isinstance(r, bool):
            print "invaild url please input correct url"
            return
        current_url = r.url
        text = r.text
        links = self.parse_content(text, current_url)
        self.urls.update(links)
        for link in links:
            self.q.put(link)
        for _ in xrange(self.depth):
            self.start()
        print "*********************"
        print "crawl  finish"
        fuzz_dirs = self.get_dir(self.urls)
        if len(fuzz_dirs) != 1:
            self.random_files.append(fuzz_dirs[-1])
        self.standers = self.get_site_stander()
        self.join_file_dir(fuzz_dirs)
        for _ in xrange(self.concurrent_num):
            self.fuzz_pool.apply(self.worker,)
        self.fuzz_pool.join()
        print "************************"
        print "finish scan"
        print "************************"
        print self.result

    def worker(self):
        try:
            while not self.fuzzflag.isSet():
                try:
                    url = self.fuzz_queue.get_nowait()
                except Empty:
                    self.fuzzflag.set()
                    continue
                except:
                    continue
                r = self._requests(
                    url, headers=self.headers, allow_redirects=True
                )
                if isinstance(r, bool):
                    continue
                code = r.status_code
                text = r.text
                if not text:
                    continue
                if 'code' in self.standers:
                    if code == self.standers['code']:
                        self.result.append(url)
                else:
                    texts = self.standers['text']

                    def calc_differece(t):
                        from difflib import SequenceMatcher
                        if SequenceMatcher(None, text, t).quick_ratio()\
                                > self.threshold:
                            return True
                    flag = any(
                        map(
                            calc_differece, texts
                        )
                    )
                    if not flag:
                        self.result.append(url)
        except:
            traceback.print_exc()

    def get_dicts(self, extion):
        results = []
        try:
            with open("dict/{}.txt".format(extion), "r") as f:
                values = f.readlines()
                for value in values:
                    results.append(value.strip('\n').strip())
        except:
            traceback.print_exc()
        finally:
            return results

    def get_site_stander(self):
        standers = {}
        try:
            infos = {}
            for file in self.random_files:
                url = urlparse.urljoin(self.target, file)
                r = self._requests(
                    url, timeout=10, headers=self.headers,
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

    def join_file_dir(self, fuzz_dirs):
        try:
            fuzz_dirs = list(fuzz_dirs)
            if len(fuzz_dirs) > 1:
                common_dirs = []
            else:
                common_dirs = self.get_dicts(extion="common_dir")
            common_files = self.get_dicts(extion=self.extion)
            fuzz_dirs.extend(common_dirs)
            dirs = list(set(fuzz_dirs))
            for dir in dirs:
                for file in common_files:
                    path = dir + '/' + file
                    url = urlparse.urljoin(
                        self.scheme + '://' + self.target_domain, path
                    )
                    self.fuzz_queue.put(url)
        except:
            traceback.print_exc()

    def get_dir(self, urls):
        fuzz_dirs = set()
        fuzz_dirs.add('')
        sxs = self.suffixs + self.black_suffixs
        try:
            for u in urls:
                u = u.split('?')[0]

                def map_suffixs(x):
                    if u.endswith(x):
                        if x == '.action' or x == '.do' or x == '.jsp':
                            self.extion = 'jsp'
                        elif x == '.php' or x == '.asp' or x == '.aspx':
                            self.extion = x.strip('.')
                        return True
                flag = any(
                    map(
                        map_suffixs, sxs
                    )
                )
                depth = True if flag else False
                __ = urlparse.urlparse(u)
                paths = __.path.split('/')
                try:
                    if not depth and len(paths) != 2:
                        fuzz_dirs.add(paths[1])
                    else:
                        __ = ""
                        for _ in paths:
                            if _ != paths[-1] and _:
                                __ += _ + '/'
                                fuzz_dirs.add(__.rstrip('/'))
                except:
                    pass
        except:
            traceback.print_exc()
        finally:
            return list(fuzz_dirs)


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
        params['allow_redirects'] = kwargs['allow_redirects']
    except:
        params['allow_redirects'] = False
    return params


if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument("-u", "--url", dest="url")
    parse.add_argument("-e", "--extion", dest='extion', default="php")
    parse.add_argument("-d", "--depth", dest="depth", default=6, type=int)
    parse.add_argument("-t", "--threads", dest="threads", default=50, type=int)
    args = parse.parse_args()
    url = args.url
    extion = args.extion
    depth = args.depth
    threads = args.threads
    if not url or not url.startswith('http'):
        print "please input correct url"
        exit()
    hand = Scanner(url, extion, depth, threads)
    hand.scan()
