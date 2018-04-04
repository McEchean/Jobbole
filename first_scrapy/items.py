# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy,re
from scrapy.loader.processors import MapCompose,TakeFirst,Join
from datetime import datetime
from scrapy.loader import ItemLoader

class ArticleItemloader(ItemLoader):
    default_output_processor = TakeFirst()


class FirstScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def datehander(value):
    try:
        value = re.match('.*?(\d+)/(\d+)/(\d+).*',value,re.DOTALL).groups()
        value = '/'.join(value)
        date = datetime.strptime(value, '%Y/%m/%d').date()
    except Exception as e:
        date = datetime.now().date()
    return date


def get_num(value):
    re_match = re.match('.*?(\d+).*', value)
    if re_match:
        shoucang2 = re_match.group(1)
    else:
        shoucang2 = 0
    return int(shoucang2)

def return_item(value):
    return value

def get_str(value):
    if '评论' not in value:
        return value


class ArticleItem(scrapy.Item):
    title = scrapy.Field()
    date = scrapy.Field(
        input_processor=MapCompose(datehander),
        output_processor=TakeFirst()
    )
    url = scrapy.Field()
    url_md5 = scrapy.Field()
    font_image_url = scrapy.Field(
        output_processor=MapCompose(return_item)
    )
    font_image_path = scrapy.Field()
    dianzan = scrapy.Field()
    shoucang = scrapy.Field(
        input_processor=MapCompose(get_num)
    )
    pinglun = scrapy.Field(
        input_processor=MapCompose(get_num)
    )
    content = scrapy.Field()
    tag = scrapy.Field(
        input_processor=MapCompose(get_str),
        output_processor=Join(',')
    )



