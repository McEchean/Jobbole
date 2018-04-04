# -*- coding: utf-8 -*-
import scrapy
import re
from scrapy.http import Request
from urllib import parse
from first_scrapy.items import ArticleItem
from first_scrapy.utils.common import get_md5
from datetime import datetime
from first_scrapy.items import ArticleItemloader


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['python.jobbole.com']
    start_urls = ['http://python.jobbole.com/all-posts/']

    def parse(self, response):
        #提取页面中所有文章的详细url
        artile_nodes = response.css('#archive .floated-thumb .post-thumb a')
        for node in artile_nodes:
            article_url = node.css('::attr(href)').extract_first('')
            image_url = node.css('img::attr(src)').extract_first('')
            # response.url + article_url  #拼接是为了防止有些href它不包括主域名，只有一个具体的，好好用urllib 里的parse函数
            yield Request(url=parse.urljoin(response.url,article_url),meta={'font_image_url':parse.urljoin(response.url, image_url)},callback=self.parse_detail)

        #提取下一页的url
        next_url = response.css('.next.page-numbers ::attr(href)').extract_first('')
        if next_url:
            yield Request(url=parse.urljoin(response.url,next_url),callback=self.parse)



        # # re_seletor = response.xpath('//*[@id="post-88940"]/div[1]/h1')
        # re_seletor = response.xpath('//div[@class="entry-header"]/h1/text()')
        # title = re_seletor.extract()
        # datatime = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()').extract_first('').strip().replace('·','').strip()
        # dianzan = response.xpath('//div[@class="post-adds"]/span[1]/h10/text()').extract_first('')
        # shoucang = response.xpath('//div[@class="post-adds"]/span[2]/text()').extract_first('').strip()
        # pinglun = response.xpath('//div[@class="post-adds"]/a[1]/span[1]/text()').extract_first('').strip()
        # re_match = re.match('.*?(\d+).*',shoucang)
        # if re_match:
        #     shoucang = re_match.group(1)
        # re_match = re.match('.*?(\d+).*', pinglun)
        # if re_match:
        #     pinglun = re_match.group(1)
        #
        # content = response.xpath('//div[@class="entry"]').extract()[0]
        #
        # tag_list = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        # category = [element for element in tag_list if not element.strip().endswith('评论')]
        # tags = ','.join(category)

    def parse_detail(self,response):
        # font_image_url = response.meta.get('font_image_url','')
        # title2 = response.css('div.entry-header h1::text').extract_first('')
        # datatime2 = response.css('p.entry-meta-hide-on-mobile ::text').extract_first('').strip().replace('·', '').strip()
        # dianzan2 = response.css('.vote-post-up h10::text').extract_first('')
        # shoucang2 = response.css('span.bookmark-btn ::text').extract_first('').strip()
        # re_match123 = re.match('(\d+).*', shoucang2)
        # if re_match123:
        #     shoucang2 = re_match123.group(1)
        # else:
        #     shoucang2 = 0
        #
        # pinglun2 = response.css('a[href="#article-comment"] span::text').extract_first('').strip()
        # re_match12 = re.match('.*?(\d+).*', pinglun2)
        # if re_match12:
        #     pinglun2 = re_match12.group(1)
        # else:
        #     pinglun2 = 0
        #
        # content2 = response.css('div.entry').extract_first('')
        #
        # tag_list2 = response.css('.entry-meta-hide-on-mobile a::text').extract()
        # category2 = [element for element in tag_list2 if not element.strip().endswith('评论')]
        # tags = ','.join(category2)
        #
        # article_item = ArticleItem()
        # article_item['title'] = title2
        # try:
        #     date = datetime.strptime(datatime2,'%Y/%m/%d').date()
        # except Exception as e:
        #     date = datetime.now().date()
        # article_item['date'] = date
        # article_item['url'] = response.url
        # article_item['url_md5'] = get_md5(response.url)
        # article_item['dianzan'] = dianzan2
        # article_item['shoucang'] = shoucang2
        # article_item['pinglun'] = pinglun2
        # article_item['content'] = content2
        # article_item['tag'] = tags
        # article_item['font_image_url'] = [font_image_url]
        # # article_item['font_image_path'] = font_image_path

        #通过Itemloader
        font_image_url = response.meta.get('font_image_url', '')
        item_loader = ArticleItemloader(item = ArticleItem(),response= response)
        item_loader.add_css('date','p.entry-meta-hide-on-mobile ::text')
        item_loader.add_css('title','div.entry-header h1::text')
        item_loader.add_value('url',response.url)
        item_loader.add_value('url_md5', get_md5(response.url))
        item_loader.add_css('dianzan', '.vote-post-up h10::text')
        item_loader.add_css('shoucang', 'span.bookmark-btn ::text')
        item_loader.add_css('pinglun', 'a[href="#article-comment"] span::text')
        item_loader.add_css('content', 'div.entry')
        # item_loader.add_xpath()
        item_loader.add_value('font_image_url',[font_image_url])
        item_loader.add_css('tag','.entry-meta-hide-on-mobile a::text')
        article_item = item_loader.load_item()
        yield article_item
