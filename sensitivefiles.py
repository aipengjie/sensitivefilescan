# -*- coding:utf-8 -*-
# !/usr/bin/env python


import traceback
import urlparse
import argparse
import time
import json
from multiprocessing import Pool
from lib.crawl import crawl
from lib.basicinfo import _requests
from lib.basicinfo import headers
from lib.crawl import black_suffixs
from lib.exploit import exploit_backup_path
from lib.exploit import exploit_common_file
from lib.exploit import exploit_directory_path
from lib.exploit import exploit_server_path
from lib.exploit import get_extion_by_sever


__author__ = 'longxiaowu'


class Scanner(object):
    def __init__(self, url, extion='php', depth=4, nums=50):
        self.target = url
        self.suffixs = ['.php', '.asp', '.jsp', '.do', '.action', '.aspx']
        self.urls = set()
        self.result = []
        self.depth = depth
        self.threshold = 0.9
        self.extion = extion
        self.concurrent_num = nums
        self.fuzz_urls = []
        self.standers = {}
        self.extion = extion
        self.parse_extion = ""

    def scan(self):
        try:
            if not self.target.startswith("http"):
                self.targets = [
                    "http://" + self.target,
                    "https://" + self.target
                ]
                for target in self.targets:
                    r = _requests(target, headers=headers)
                    if not isinstance(r, bool):
                        self.target = target
                        break
            r = _requests(self.target, headers=headers)
            if isinstance(r, bool):
                print "{} is invaild url".format(self.target)
                return
            print "target is {}".format(self.target)
            self.target_domain = urlparse.urlparse(self.target).netloc
            print "*********************   start crawling  ***********************"
            hand = crawl(self.target, self.depth, self.concurrent_num)
            crawl_urls = hand.scan()
            dirs = self.get_dir(crawl_urls)
            print "*********************** start fuzzing *************************"
            server_result = exploit_server_path(self.target)
            backup_result = exploit_backup_path(self.target, dirs)
            directory_result = exploit_directory_path(self.target, dirs)
            dirs.append("")
            if self.parse_extion:
                common_file_result = exploit_common_file(self.target, self.parse_extion, dirs)
            else:
                extion = get_extion_by_sever(self.target)
                if extion:
                    common_file_result = exploit_common_file(self.target, extion, dirs)
                else:
                    common_file_result = exploit_common_file(self.target, self.extion, dirs)
            if any([server_result, backup_result, directory_result, common_file_result]):
                with open("report/" + self.target_domain + ".txt", 'w') as f:
                    if server_result:
                        f.writelines("****************** server path ******************\n")
                        for url in server_result:
                            f.writelines(url + '\n')
                        f.writelines("****************** server path ******************\n")
                    if backup_result:
                        f.writelines("****************** backup path ******************\n")
                        for url in backup_result:
                            f.writelines(url + '\n')
                        f.writelines("****************** backup path ******************\n")
                    if directory_result:
                        f.writelines("**************** directory path *****************\n")
                        for url in directory_result:
                            f.writelines(url + '\n')
                        f.writelines("**************** directory path *****************\n")
                    if common_file_result:
                        f.writelines("*************** common file path ****************\n")
                        for url in common_file_result:
                            f.writelines(url + '\n')
                        f.writelines("*************** common file path ****************\n")
                    f.close()
        except:
            traceback.print_exc()

    """
    @note: 解析爬虫的urls获取网站目录结构，获取网站语言extion
    """

    def get_dir(self, urls):
        fuzz_dirs = set()
        sxs = self.suffixs + black_suffixs
        try:
            for u in urls:
                u = u.split('?')[0]

                def map_suffixs(x):
                    if u.endswith(x):
                        if x == '.action' or x == '.do' or x == '.jsp':
                            self.parse_extion = 'jsp'
                        elif x == '.php' or x == '.asp' or x == '.aspx':
                            self.parse_extion = x.strip('.')
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


def get_target(file):
    urls = []
    try:
        with open(file) as f:
            targets = f.readlines()
            for i in targets:
                urls.append(i.strip("\n"))
            f.close()
    except:
        traceback.print_exc()
    return urls


def fuzz(url, extion, depth, threads):
    try:
        hand = Scanner(url, extion, depth, threads)
        hand.scan()
    except:
        traceback.print_exc()


if __name__ == "__main__":
    parse = argparse.ArgumentParser()
    parse.add_argument("-u", "--url", dest="url", help="the target to be scanned")
    parse.add_argument("-e", "--extion", dest='extion', default="php", help="the extion of target")
    parse.add_argument("-d", "--depth", dest="depth", default=4, type=int, help="the depth of crawl")
    parse.add_argument("-t", "--threads", dest="threads", default=50, type=int, help="the num of threads")
    parse.add_argument("-f", "--file", dest="file", type=str, help="scan multiple target")
    parse.add_argument("--log-json", dest="log_json", type=str, help="scan whatweb 's result that --log-json format")
    args = parse.parse_args()
    url = args.url
    extion = args.extion
    depth = args.depth
    threads = args.threads
    file = args.file
    log_json = args.log_json
    if not url and not file and not log_json:
        print "please input correct url"
        exit()
    st = time.time()
    if file:
        urls = get_target(file)
        if not urls:
            print "{} has no urls".format(file)
        else:
            for url in urls:
                fuzz(url, extion, depth, threads)
    elif log_json:
        with open(args.log_json) as f:
            target_infos = json.loads(f.read())
            for target_info in target_infos:
                if target_info.has_key("http_status"):
                    if 200 <= target_info["http_status"] < 300:
                        fuzz(target_info["target"], extion, depth, threads)
                    if 300 <= target_info["http_status"] < 400:
                        if target_info["plugins"].has_key("RedirectLocation"):
                            for url in target_info["plugins"]["RedirectLocation"]["string"]:
                                fuzz(target_info["target"], extion, depth, threads)
    else:
        fuzz(url, extion, depth, threads)
    ft = time.time()
    print "scan time :: " + str(ft-st)