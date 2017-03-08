#sensitivefilescan

工具会首先爬取网站链接，根据链接解析目录，然后枚举当前目录是否存在敏感文件，此外了还增加目录遍历检查和一些敏感server 路径检查

##安装环境
###首先安装python的第三份方包
pip install -r requirements.txt

##用法

1. python sensitivefiles.py "http://www.baidu.com"
2. python sensitivefiles.py "http://www.baidu.com" -e 'php' -t 40 -d 10
3. python sensitivefiles.py -f example.txt
4. -e 表示网站类型，-t 为爬虫的协程池默认为30， -d 则是爬虫的深度

##note

这里的字典都是自己精挑细选出来的，大家有好的字典或者bug,可以提交issue或者merger代码
