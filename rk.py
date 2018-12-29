#!/usr/bin/env python
# coding:utf-8

import requests
from hashlib import md5
from user import CodeName, CodePass


class RClient(object):

    def __init__(self, username, password, soft_id, soft_key):
        self.username = username
        self.password = md5(password).hexdigest()
        self.soft_id = soft_id
        self.soft_key = soft_key
        self.base_params = {
            'username': self.username,
            'password': self.password,
            'softid': self.soft_id,
            'softkey': self.soft_key,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'Expect': '100-continue',
            'User-Agent': 'ben',
        }

    def rk_create(self, im, im_type, timeout=60):
        """
        im: 图片字节
        im_type: 题目类型
        """
        params = {
            'typeid': im_type,
            'timeout': timeout,
        }
        params.update(self.base_params)
        files = {'image': ('a.jpg', im)}
        r = requests.post('http://api.ruokuai.com/create.json', data=params, files=files, headers=self.headers)
        return r.json()

    def rk_report_error(self, im_id):
        """
        im_id:报错题目的ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://api.ruokuai.com/reporterror.json', data=params, headers=self.headers)
        return r.json()


def getCode():
    rc = RClient(CodeName, CodePass, '107587', 'd7e6951479784f2387356a3a6e3cf536')
    im = open('code.png', 'rb').read()

    pos = {
        '1': '45,45', '2': '114,51', '3': '189,48', '4': '256,52',
        '5': '44,125', '6': '117,119', '7': '184,115', '8': '252,123'
    }
    result = rc.rk_create(im, 6113)[u'Result']
    final = ''
    for x in result:
        final = final + ',' + pos[x]

    return final[1:]