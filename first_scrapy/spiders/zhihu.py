# -*- coding: utf-8 -*-
import scrapy

import re
import json
import time
import hashlib
import hmac
from urllib import parse
from datetime import datetime

from parsel import Selector
from scrapy.loader import ItemLoader

from first_scrapy.items import ZhihuAnswerItem,ZhihuQuestionItem
# from scrapy.http import Request


headers = {
    'Connection': 'keep-alive',
    'Origin': 'https://www.zhihu.com',
    'Referer': 'https://www.zhihu.com/signup?next=%2F',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
}

Login_url = 'https://www.zhihu.com/signup'
Login_api = 'https://www.zhihu.com/api/v3/oauth/sign_in'
Form_data = {
    'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
    'grant_type': 'password',
    'source': 'com.zhihu.web',
    'username': '13093729859',
    'password': 'whf454545[]',
    # 'lang':'cn',
    'lang': 'en',
    'ref_source': 'homepage',
    # 'utm_source':'baidu',
}

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default' \
                       '&include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info' \
                       '%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason' \
                       '%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment' \
                       '%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings' \
                       '%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info' \
                       '%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized' \
                       '%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees' \
                       '%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count' \
                       '%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}'

    def parse(self, response):
        # 提取出页面中所有的url，并跟踪
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls if 'question' in url ]
        for url in all_urls:
            match_obj = re.match('(.*/question/(\d+))/answer.*', url)
            if match_obj:
                request_url = match_obj.group(1)
                question_id = match_obj.group(2)
                yield scrapy.Request(request_url, headers=headers, meta={'question_id': question_id}, callback=self.parse_question)
            else:
                yield scrapy.Request(url,headers=headers)

    def parse_question(self,response):
        # 处理question页面，提取信息
        resp = response.meta.get('question_id')
        item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
        item_loader.add_css('title', 'h1.QuestionHeader-title::text')
        item_loader.add_css('content', '.QuestionHeader-detail')
        item_loader.add_value('url', response.url)
        item_loader.add_value('zhihu_id', resp)
        item_loader.add_css('answer_num', 'h4.List-headerText span::text')
        item_loader.add_css('comments_num', 'div.QuestionHeader-Comment button::text')
        item_loader.add_css('watch_user_num', '.NumberBoard-itemValue::attr(title)')
        item_loader.add_css('topics', '.QuestionHeader-topics .Popover div::text')

        question_item = item_loader.load_item()
        url = self.start_answer_url.format(int(resp), 5, 0)
        yield scrapy.Request(url, headers=headers, callback=self.parse_answer)
        yield question_item

    def parse_answer(self, response):
        ans_json = json.loads(response.text)
        is_end = ans_json['paging']['is_end']
        next_url = ans_json['paging']['next']
        for answer in ans_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item['zhihu_id'] = answer['id']
            answer_item['url'] = answer['url']
            answer_item['question_id'] = answer['question']['id']
            answer_item['author_id'] = answer['author']['id'] if 'id' in answer['author'] else None
            answer_item['content'] = answer['content'] if 'content' in answer else None
            answer_item['praise_num'] = answer['voteup_count']
            answer_item['comments_num'] = answer['comment_count']
            answer_item['create_time'] = answer['created_time']
            answer_item['update_time'] = answer['updated_time']
            answer_item['crawl_time'] = datetime.now().strftime('%Y-%m-%d %X')
            yield  answer_item
        if not is_end:
            yield scrapy.Request(next_url, headers=headers, callback=self.parse_answer)







    def start_requests(self):
        return [scrapy.Request('https://www.zhihu.com/signup', headers=headers, callback=self.login)]

    def login(self, response):
        xsrf = re.findall(r'_xsrf=([\w|-]+)', str(response.headers.getlist('Set-Cookie')[1]))[0]
        sel = Selector(response.text).css('div::attr(data-state)').extract_first('')
        udid = json.loads(sel)['token']['xUDID']
        headers.update({
            'x-xsrftoken':xsrf,
            'x-udid':udid
        })

        # username,password = self._check_user_password()

        # Form_data.update({
        #     'username':username,
        #     'password':password
        # })

        lang = headers.get('lang','en')
        if lang == 'en':
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        else:
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'

        yield scrapy.Request(api,headers= headers,callback=self.login_after_captcha)


    def login_after_captcha(self,response):
        show_captcha = re.search(r'true', response.text)
        if show_captcha:
            pass
        else:
            captcha = ''
        timestamp = str(int(time.time()*1000))
        signature = self._get_signature(timestamp)
        Form_data.update({
            'captcha': captcha,
            'timestamp': timestamp,
            'signature': signature
        })
        return [scrapy.FormRequest(
            url=Login_api,
            formdata=Form_data,
            headers=headers,
            callback= self.check_login
        )]
    def check_login(self,response):
        status = response.status
        if status == 201:
            for url in self.start_urls:
                yield scrapy.Request(url, dont_filter=True, headers= headers)

    def _get_signature(self, timestamp):
        ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)
        grant_type = Form_data['grant_type']
        client_id = Form_data['client_id']
        source = Form_data['source']
        ha.update(bytes((grant_type + client_id + source + timestamp), 'utf-8'))
        return ha.hexdigest()

    # def _check_user_password(self,username,password):
    #     if username is None:
    #         username = Form_data.get('username')
    #         if not username:
    #             username = input('请输入手机号:')
    #     if '+86' not in username:
    #         username = '+86' + username
    #     if password is None:
    #         password = Form_data.get('password')
    #         if not password:
    #             password = input('请输入密码:')
    #     return username,password

    # def _get_captcha(self, headers):
    #     lang = headers.get('lang', 'en')
    #     if lang == 'en':
    #         api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
    #     else:
    #         api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'
    #
    #     resp = self.session.get(api, headers=headers)
    #     show_captcha = re.search(r'true', resp.text)
    #     if show_captcha:
    #         put_resp = self.session.put(api, headers=headers)
    #         img_base64 = re.findall(r'"img_base64":"(.+)', put_resp.text, re.S)[0].replace(r'\n', '')
    #         with open('./captcha.jpg', 'wb') as f:
    #             f.write(base64.b64decode(img_base64))
    #         img = Image.open('./captcha.jpg')
    #
    #         if lang == 'cn':
    #             plt.imshow(img)
    #             print('点击所有倒立的文字，按回车提交')
    #             points = plt.ginput(7)
    #             capt = json.dumps({'img_size': [200, 44], 'input_points': [
    #                 [i[0] / 2, i[1] / 2] for i in points
    #             ]})
    #         else:
    #             img.show()
    #             capt = input('请输入验证码:')
    #         self.session.post(api, data={'input_text': capt}, headers=headers)
    #         return capt
    #     return ''




