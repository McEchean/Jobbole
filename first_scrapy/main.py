#-*-coding:utf-8-*-
__author__: 'McEachen'
__date__: '2018/3/29 15:41'

from scrapy.cmdline import execute

import sys,os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(['scrapy','crawl','jobbole'])