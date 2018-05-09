# -*-coding:utf-8-*-
__author__: 'McEachen'
__date__: '2018/4/6 9:08'

import requests
import re
import hmac
from parsel import Selector
import json
import time
import hashlib
import base64
from PIL import Image
import matplotlib.pyplot as plt
from http import cookiejar

headers = {
    'Connection': 'keep-alive',
    'Origin': 'https://www.zhihu.com',
    'Referer': 'https://www.zhihu.com/signup?next=%2F',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36',
    'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20'
}
# r = requests.get('https://www.zhihu.com',headers=headers)
# t1 = Selector(r.text)
# jsr1 = t1.css('div#data::attr(data-state)').extract_first('')
# udid = json.loads(jsr1)['token']['xUDID']
# print(r.text.encode('utf-8'))
# print(r.status_code)


Login_url = 'https://www.zhihu.com/signup'
Login_api = 'https://www.zhihu.com/api/v3/oauth/sign_in'
Form_data = {
    'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
    'grant_type': 'password',
    'source': 'com.zhihu.web',
    'username': '',
    'password': '',
    # 'lang':'cn',
    'lang': 'en',
    'ref_source': 'homepage',
    # 'utm_source':'baidu',
}


class AccountZhihu(object):
    def __init__(self):
        self.login_url = Login_url
        self.login_api = Login_api
        self.login_data = Form_data.copy()
        self.session = requests.session()
        self.session.headers = headers.copy()
        self.session.cookies = cookiejar.LWPCookieJar(filename='cookies.txt')

    def login(self, username=None, password=None, load_cookies=True):
        if load_cookies and self.load_cookies():
            if self.check_login():
                return True

        headers = self.session.headers.copy()
        udid_cookies = self._get_token()
        headers.update({
            'x-xsrftoken': udid_cookies[0],
            'x-udid': udid_cookies[1]
        })

        username, password = self._check_user_password(username, password)

        self.login_data.update({
            'username': username,
            'password': password
        })

        timestamp = str(int(time.time() * 1000))
        self.login_data.update({
            'captcha': self._get_captcha(headers),
            'timestamp': timestamp,
            'signature': self._get_signature(timestamp)
        })

        resp = self.session.post(self.login_api, data=self.login_data, headers=headers)
        if 'error' in resp.text:
            print(re.findall(r'"message":"(.+)"', resp.text)[0])
        elif self.check_login():
            return True
        print('登陆失败')
        return False

    def check_login(self):
        resp = self.session.get(self.login_url, allow_redirects=False)
        if resp.status_code == 302:
            self.session.cookies.save()
            print('登陆成功')
            return True
        return False

    def _get_signature(self, timestamp):
        ha = hmac.new(b'd1b964811afb40118a12068ff74a12f4', digestmod=hashlib.sha1)
        grant_type = self.login_data['grant_type']
        client_id = self.login_data['client_id']
        source = self.login_data['source']
        ha.update(bytes((grant_type + client_id + source + timestamp), 'utf-8'))
        return ha.hexdigest()

    def _get_captcha(self, headers):
        lang = headers.get('lang', 'en')
        if lang == 'en':
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=en'
        else:
            api = 'https://www.zhihu.com/api/v3/oauth/captcha?lang=cn'

        resp = self.session.get(api, headers=headers)
        show_captcha = re.search(r'true', resp.text)
        if show_captcha:
            put_resp = self.session.put(api, headers=headers)
            img_base64 = re.findall(r'"img_base64":"(.+)', put_resp.text, re.S)[0].replace(r'\n', '')
            with open('./captcha.jpg', 'wb') as f:
                f.write(base64.b64decode(img_base64))
            img = Image.open('./captcha.jpg')

            if lang == 'cn':
                plt.imshow(img)
                print('点击所有倒立的文字，按回车提交')
                points = plt.ginput(7)
                capt = json.dumps({'img_size': [200, 44], 'input_points': [
                    [i[0] / 2, i[1] / 2] for i in points
                ]})
            else:
                img.show()
                capt = input('请输入验证码:')
            self.session.post(api, data={'input_text': capt}, headers=headers)
            return capt
        return ''

    def load_cookies(self):
        try:
            self.session.cookies.load(ignore_discard=True)
            return True
        except FileNotFoundError:
            return False

    def _get_token(self):
        resp = self.session.get(self.login_url)
        cookie = re.findall(r'_xsrf=([\w|-]+)', resp.headers.get('Set-Cookie'))[0]
        sel = Selector(resp.text).css('div::attr(data-state)').extract_first('')
        udid = json.loads(sel)['token']['xUDID']
        return (cookie, udid)

    def _check_user_password(self, username, password):
        if username is None:
            username = self.login_data.get('username')
            if not username:
                username = input('请输入手机号:')
        if '+86' not in username:
            username = '+86' + username
        if password is None:
            password = self.login_data.get('password')
            if not password:
                password = input('请输入密码：')
        return username, password


if __name__ == '__main__':
    account = AccountZhihu()
    account.login(username='13093xxxxx', password='whf45xxxxx', load_cookies=True)
