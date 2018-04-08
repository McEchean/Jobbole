# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.pipelines.images import ImagesPipeline
import codecs, json
from scrapy.exporters import JsonItemExporter
import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi


class FirstScrapyPipeline(object):
    def process_item(self, item, spider):
        return item


class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class JsonExpoterPipeline(object):
    # 调用scrapy 提供的 json exporter  导出json文件
    def __init__(self):
        self.file = open('jsonexplor.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def close_spider(self, spider):
        self.exporter.finish_exporting()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class MysqlPipeline(object):
    def __init__(self):
        self.conn = MySQLdb.connect('127.0.0.1', 'root', 'password', 'scrapy', charset='utf8', use_unicode=True)
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        insert_sql = """
            insert into jobbole (title,date,url,url_md5,font_image_url,font_image_path,dianzan,shoucang,pinglun,content,tag)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);
        """
        self.cursor.execute(insert_sql,
                            (item['title'], item['date'], item['url'], item['url_md5'], item['font_image_url'], \
                             item['font_image_path'], item['dianzan'], item['shoucang'], item['pinglun'], \
                             item['content'], item['tag']))
        self.conn.commit()
        return item


class MysqlTwisedPipeline(object):
    def __init__(self, dbpool):
        self.dbpool = dbpool

    @classmethod
    def from_settings(cls, settings):
        params = dict(settings['PARAMS'])
        dbpool = adbapi.ConnectionPool('MySQLdb', **params)
        return cls(dbpool)

    # 使用Twised 将mysql插入变成异步执行
    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)  # 处理异常
        return item

    def handle_error(self, failure, item, spider):
        # 处理异步插入的异常
        print(failure)

    def do_insert(self, cursor, item):
        insert_sql, params = item.get_sql()

        cursor.execute(insert_sql, params)


class ArticleImagePipeline(ImagesPipeline):
    def item_completed(self, results, item, info):
        for ok, value in results:
            if 'font_image_url' in item:
                image_file_path = value['path']
            item['font_image_path'] = image_file_path
        return item
