# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy, re
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from datetime import datetime
from scrapy.loader import ItemLoader
from first_scrapy.utils.common import get_num


class ArticleItemloader(ItemLoader):
    default_output_processor = TakeFirst()


class FirstScrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def datehander(value):
    try:
        value = re.match('.*?(\d+)/(\d+)/(\d+).*', value, re.DOTALL).groups()
        value = '/'.join(value)
        date = datetime.strptime(value, '%Y/%m/%d').date()
    except Exception as e:
        date = datetime.now().date()
    return date


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

    def get_sql(self):
        insert_sql = """
                           insert into jobbole (title,date,url,url_md5,font_image_url,font_image_path,dianzan,shoucang,pinglun,content,tag)
                           values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
                       """
        params = (self['title'], self['date'], self['url'], self['url_md5'], self['font_image_url'], \
                  self['font_image_path'], self['dianzan'], self['shoucang'], self['pinglun'], \
                  self['content'], self['tag'])

        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_sql(self):
        insert_sql = """
            insert into zhihu_question (zhihu_id,topics,url,title,content,answer_num,comments_num,watch_user_num,click_num,crawl_time)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            on DUPLICATE KEY UPDATE content=VALUES (content),answer_num = VALUES (answer_num),comments_num = VALUES (comments_num),
            watch_user_num = VALUES (watch_user_num), click_num = VALUES (click_num);
        """

        zhihu_id = int(self['zhihu_id'][0])
        topics = ','.join(self['topics'])
        url = self['url'][0]
        title = ''.join(self['title'])
        content = ''.join(self['content'])
        answer_num = get_num(''.join(self['answer_num']))
        comments_num = get_num(''.join(self['comments_num']))
        watch_user_num = int(self['watch_user_num'][0])
        click_num = int(self['watch_user_num'][1])
        crawl_time = datetime.now().strftime('%Y-%m-%d %X')
        params = (
            zhihu_id, topics, url, title, content, answer_num, comments_num, watch_user_num, click_num, crawl_time)

        return insert_sql, params


class ZhihuAnswerItem(scrapy.Item):
    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()

    def get_sql(self):
        insert_sql = """
            insert into zhihu_answer (zhihu_id,url,question_id,author_id,content,praise_num,comments_num,create_time,update_time,crawl_time)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE content=VALUES (content),comments_num = VALUES (comments_num),
            praise_num = VALUES (praise_num),update_time = VALUES (update_time);
        """
        create_time = datetime.fromtimestamp(self['create_time']).strftime('%Y-%m-%d')
        update_time = datetime.fromtimestamp(self['update_time']).strftime('%Y-%m-%d')

        params = (
            self['zhihu_id'], self['url'], self['question_id'], self['author_id'], self['content'], self['praise_num']
            , self['comments_num'], create_time, update_time, self['crawl_time'])

        return insert_sql, params
