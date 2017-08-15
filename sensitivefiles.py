# -*- coding:utf-8 -*-
# !/usr/bin/env python


import traceback
import urlparse
import argparse
import time
import multiprocessing
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
                print "invaild url please input correct url"
                return
            self.target_domain = urlparse.urlparse(self.target).netloc
            print "start crawl"
            print "*********************"
            hand = crawl(self.target, self.depth, self.concurrent_num)
            crawl_urls = hand.scan()
            print "*********************"
            print "crawl  finish"
            dirs = self.get_dir(crawl_urls)
            print "*********************"
            print "load server path "
            server_result = exploit_server_path(self.target)
            print "*********************"
            print "load backup path"
            backup_result = exploit_backup_path(self.target, dirs)
            print "*********************"
            print "load directory path"
            directory_result = exploit_directory_path(self.target, dirs)
            print "*********************"
            print "load common file path"
            if self.parse_extion:
                common_file_result = exploit_common_file(self.target, self.parse_extion, dirs)
            else:
                extion = get_extion_by_sever(self.target)
                if extion:
                    common_file_result = exploit_common_file(self.target, extion, dirs)
                else:
                    common_file_result = exploit_common_file(self.target, self.extion, dirs)
            print "************************"
            print "finish scan :: {}".format(self.target)
            print "************************"
            if any([server_result, backup_result, directory_result, common_file_result]):
                with open(self.target_domain + ".txt", 'w') as f:
                    if server_result:
                        f.writelines("************server path************\n")
                        for url in server_result:
                            f.writelines(url + '\n')
                        f.writelines("************server path************\n\n\n")
                    if backup_result:
                        f.writelines("************backup path************\n")
                        for url in backup_result:
                            f.writelines(url + '\n')
                        f.writelines("************backup path************\n\n\n")
                    if directory_result:
                        f.writelines("************directory path************\n")
                        for url in directory_result:
                            f.writelines(url + '\n')
                        f.writelines("************directory path************\n\n\n")
                    if common_file_result:
                        f.writelines("************common file path************\n")
                        for url in common_file_result:
                            f.writelines(url + '\n')
                        f.writelines("************common file path************\n\n\n")
                    f.close()
        except:
            traceback.print_exc()

    """
    @note: 解析爬虫的urls获取网站目录结构，获取网站语言extion
    """

    def get_dir(self, urls):
        fuzz_dirs = set()
        fuzz_dirs.add('')
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
    # parse = argparse.ArgumentParser()
    # parse.add_argument("-u", "--url", dest="url")
    # parse.add_argument("-e", "--extion", dest='extion', default="php")
    # parse.add_argument("-d", "--depth", dest="depth", default=4, type=int)
    # parse.add_argument("-t", "--threads", dest="threads", default=50, type=int)
    # parse.add_argument("-f", "--file", dest="file", type=str)
    # args = parse.parse_args()
    # url = args.url
    # extion = args.extion
    # depth = args.depth
    # threads = args.threads
    # file = args.file
    # if not url and not file:
    #     print "please input correct url"
    #     exit()
    # st = time.time()
    # if file:
    #     urls = get_target(file)
    #     if not urls:
    #         print "{} has no urls".format(file)
    #     else:
    #         for url in urls:
    #             hand = Scanner(url, extion, depth, threads)
    #             hand.scan()
    # else:
    #     fuzz(url, extion, depth, threads)
    # ft = time.time()
    # print "scan time :: " + str(ft-st)
    hand = Scanner("http://183.131.231.229/guestbook/index.php", extion="php")
    hand.scan()