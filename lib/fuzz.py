import traceback
import urlparse
import re
from basicinfo import headers
from basicinfo import _requests
from gevent.pool import Pool


class fuzz():
    def __init__(self, url, dicts, stander={}, concurrent_num=30, threshold=0.95):
        self.stander = stander
        self.url = url
        self.dicts = dicts
        self.fuzz_pool = Pool(concurrent_num)
        self.return_urls = set()
        self.return_texts = set()
        self.result = []
        self.threshold = threshold

    def worker(self, url):
        try:
            print "fuzz url ===>" + url
            r = _requests(
                url, headers=headers, allow_redirects=True
            )
            if isinstance(r, bool):
                return
            code = r.status_code
            text = r.text
            return_url = r.url
            return_headers = r.headers
            if return_url in self.return_urls or not text or text in self.return_texts:
                return
            elif self.stander.has_key('title'):
                match = url.split('/')[-2]
                re_rule = self.stander['title']
                flag = re.findall(re_rule, text)
                if flag:
                    if match in flag[0]:
                        self.result.append(url)
                        self.return_urls.add(return_url)
                        self.return_texts.add(text)
            elif self.stander.has_key('Content-Type'):
                values = return_headers['Content-Type']
                rule = self.stander['Content-Type']
                flag = filter(
                    lambda x: x in values, rule
                )
                if flag:
                    self.result.append(url)
                    self.return_urls.add(return_url)
                    self.return_texts.add(text)
            elif 'code' in self.stander:
                if code == self.stander['code']:
                    self.result.append(url)
                    self.return_urls.add(return_url)
                    self.return_texts.add(text)
            else:
                texts = self.stander['text']

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
                    self.return_urls.add(return_url)
                    self.return_texts.add(text)
        except:
            traceback.print_exc()

    def get_paths(self, dicts):
        fuzz_urls = []
        try:
            for i in dicts:
                u = urlparse.urljoin(self.url, i)
                fuzz_urls.append(u)
        except:
            pass
        finally:
            return fuzz_urls

    def scan(self):
        try:
            fuzz_urls = self.get_paths(self.dicts)
            for url in fuzz_urls:
                self.fuzz_pool.spawn(self.worker, url)
            self.fuzz_pool.join()
            self.fuzz_pool.kill()
        except:
            traceback.print_exc()
        finally:
            return self.result
