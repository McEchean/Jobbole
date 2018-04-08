#-*-coding:utf-8-*-
__author__: 'McEachen'
__date__: '2018/3/30 20:41'
import hashlib
import re

def get_md5(url):
    if isinstance(url, str):
        url = url.encode('utf-8')
    md5 = hashlib.md5()
    md5.update(url)
    return md5.hexdigest()

def get_num(value):
    re_match = re.match('.*?(\d+).*', value)
    if re_match:
        num = re_match.group(1)
    else:
        num = 0
    return int(num)