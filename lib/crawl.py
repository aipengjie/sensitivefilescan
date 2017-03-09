from lxml import etree
from gevent.pool import Pool
from basicinfo import _requests
from basicinfo import headers
import traceback
import urlparse
import re


black_suffixs = [
    ".jpg", '.png', '.gif', '.js', '.css', '.zip', 'tar.gz',
    'apk', 'iso', '.avi', '.pdf', '.exe', '.doc', '.xls',
    'rar', 'tar', 'dmg', 'txt', 'avi', 'xlsx', '.docx', '.7z'
]


class crawl():
    def __init__(self, url, depth=4, nums=30):
        self.url = url
        self.urls = set()
        self.crawl_pool = Pool(nums)
        self.filter_urls = set()
        self.depth = depth

    def parse_content(self, content, current_url):
        links = set()
        try:
            page = etree.HTML(content)
            for t in ['a', 'area']:
                a_tags = page.xpath(u'//{}'.format(t))
                for a_tag in a_tags:
                    link = a_tag.get('href')
                    if len(links) > 5:
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
                            black_suffixs
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

    def start(self):
        try:
            self.cacheurls = set()
            for link in self.crawl_links:
                self.crawl_pool.spawn(self.crawl, link)
            self.crawl_pool.join()
            next_urls = self.cacheurls.difference(self.urls)
            self.crawl_links = list(next_urls)
            self.urls.update(next_urls)
        except:
            traceback.print_exc()

    def crawl(self, link):
        try:
            print "crawl url ===>" + link
            r = _requests(link, headers=headers)
            if isinstance(r, bool):
                return
            current_url = r.url
            text = r.text
            links = self.parse_content(text, current_url)
            self.cacheurls.update(links)
        except:
            traceback.print_exc()

    def scan(self):
        try:
            self.target_domain = urlparse.urlparse(self.url).netloc
            r = _requests(self.url, headers=headers)
            current_url = r.url
            text = r.text
            self.links = self.parse_content(text, current_url)
            self.crawl_links = list(self.links)
            self.urls.update(self.links)
            for _ in xrange(self.depth):
                self.start()
        except:
            traceback.print_exc()
        finally:
            return self.urls

