#重写了猪猪侠的weakfilescan, 只是重写了主要的部分，字典还是用的猪猪侠的字典.
优化了下爬虫和误报，爬虫只是简单的去重爬虫，可以自己指定爬虫深度，默认是不使用common_dir的，如果爬虫没有爬到链接会使用common_dir的字典，默认使用php字典，可以自己指定字典.

#
linux用户先 sudo pip install -r requirements.txt
windows用户需要手动安装lxml这个包

#
##具体使用
python sensitivefiles.py -u "http://www.baidu.com" -e "php" -d 6 -t 50
-e , --extion 指定网站具体类型， 默认为php

-d ，--depth  指定爬虫的深度，默认为6

-t , --threads 指定爆破的的线程, 默认为50
#
如果遇到网站误报率很高，可以降低self.threshold的值,不要低于0.50, 0.9最佳
欢迎提交issues 给我，或者merge好的字典
