from threading import Thread
import requests
from lxml import etree
import re
import json
import base64
import execjs
import time

"""account.json
{
  "school_num": "11111111", 学号
  "jwxt_pwd": "666666" 密码
}
"""

# COOKIE = {"JSESSIONID": "E9784AE4E4E449C91535472834EE33A2"}
def net_protect(func):
    def inner(*args, **kwargs):
        # 因为网络问题 不知道会失败多少次 所以写个死循环
        while True:
        # for i in range(5):
            try:
                ret = func(*args, **kwargs)
                return ret  # 访问成功了就停止尝试

            except requests.exceptions.ConnectTimeout or TimeoutError or requests.exceptions.ReadTimeout as e:
                print(e)

            except TypeError as e:
                print(e)
                print("还没到选课时间")
                input("任意键继续>>>")

            # except IndexError as e:
            #     print(e, "登录失效,请更新cookie或检查账号密码")
            #     sys.exit()
    return inner

class SelectionSystem(object):
    def __init__(self, njdm_id_1, zyh_id_1, zyh_id, zyfx_id, njdm_id, bh_id, xsbj, xkxnm, xkxqm, xkkz_id):
        self.njdm_id_1 = njdm_id_1
        self.zyh_id_1 = zyh_id_1
        self.zyh_id = zyh_id
        self.zyfx_id = zyfx_id
        self.njdm_id = njdm_id
        self.bh_id = bh_id
        self.xsbj = xsbj
        self.xkxnm = xkxnm
        self.xkxqm = xkxqm
        self.xkkz_id = xkkz_id

    @net_protect
    def get_class_info(self):
        """
        获取课程id和课程名称对应关系
        :return:
        """
        data = {
            'rwlx': '1',
            'xkly': '0',
            'bklx_id': '0',
            'sfkkjyxdxnxq': '0',
            'xqh_id': '1',
            'jg_id': '02',
            'njdm_id_1': self.njdm_id_1,
            'zyh_id_1': self.zyh_id_1,
            'zyh_id': self.zyh_id,
            'zyfx_id': self.zyfx_id,
            'njdm_id': self.njdm_id,
            'bh_id': self.bh_id,
            'xbm': '2',
            'xslbdm': 'wlb',
            'ccdm': 'w',
            'xsbj': self.xsbj,
            'sfkknj': '1',
            'sfkkzy': '1',
            'kzybkxy': '0',
            'sfznkx': '0',
            'zdkxms': '0',
            'sfkxq': '0',
            'sfkcfx': '0',
            'kkbk': '0',
            'kkbkdj': '0',
            'sfkgbcx': '0',
            'sfrxtgkcxd': '0',
            'tykczgxdcs': '0',
            'xkxnm': self.xkxnm,
            'xkxqm': self.xkxqm,
            'kklxdm': '01',
            'rlkz': '0',
            'xkzgbj': '0',
            'kspage': '1',
            'jspage': '50',
            'jxbzb': '',
        }

        response = session.post(
            'http://*填你自己的/jwglxt/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html',
            params=PARAMS,
            data=data,
            verify=False,
        )
        # print(response.text)

        class_dic = {}
        text = response.text
        ret = eval(text.replace('true', 'True').replace('false', 'False'))
        tmplist = ret["tmpList"]
        print('=========课程目录============')
        for ban in tmplist:
            kcmc = ban["kcmc"]  # 课程名称
            kch_id = ban["kch_id"]  # 课程id
            class_dic[kch_id] = kcmc  # 添加进内存
            print(kcmc, kch_id)  # 可写入文件

    @net_protect
    def get_jxb_id(self, kch_id):
        data = {
            'bklx_id': '0',
            'njdm_id': self.njdm_id,
            'bh_id': self.bh_id,
            'sfkknj': '1',
            'xkxnm': self.xkxnm,
            'xkxqm': self.xkxqm,
            'kklxdm': '01',
            'kch_id': kch_id,
            'xkkz_id': self.xkkz_id,
        }
        response = session.post(
            'http://*填你自己的/jwglxt/xsxk/zzxkyzbjk_cxJxbWithKchZzxkYzb.html',
            # params=params,
            # cookies=cookies,
            # headers=headers,
            data=data,
            verify=False,
        )
        page_source = response.text
        obj = re.compile(r'"do_jxb_id":"(?P<jxb_id>.*?)"', re.S)
        result = obj.search(page_source)
        # print(result.group("jxb_id"))
        jxb_id = result.group("jxb_id")
        return jxb_id

    @net_protect
    def select(self, kch_id, jxb_id):
        data = {
            "jxb_ids": jxb_id,
            "kch_id": kch_id,
            "qz": "0",
            "xkkz_id": self.xkkz_id,
            "njdm_id": self.njdm_id,
            "zyh_id": self.zyh_id,
            "kklxdm": "01",
        }

        response = session.post(
            'http://*填你自己的/jwglxt/xsxk/zzxkyzbjk_xkBcZyZzxkYzb.html',
            data=data,
            verify=False,
        )
        print(response.text+data['kch_id'])  # comment it before running
        json_text = json.loads(response.text)
        flag = json_text['flag']
        msg = json_text['msg']
        return flag

    def monitor(self, kch_id, jxb_id):
        while True:
            time.sleep(2)  # dont send request too frequently
            flag = self.select(kch_id, jxb_id)
            if flag == '1':
                break

@net_protect
def get_pub_params():
    """
    初始化data
    """
    response = session.get(
        'http://*填你自己的/jwglxt/xsxk/zzxkyzb_cxZzxkYzbIndex.html',
        params=PARAMS,
        # cookies=COOKIE,
        # headers=HEADER,
        verify=False,
    )
    # print(response.text)

    page_source = etree.HTML(response.text)

    njdm_id_1 = page_source.xpath('//*[@id="njdm_id_1"]/@value')[0]
    zyh_id_1 = page_source.xpath('//*[@id="zyh_id_1"]/@value')[0]
    zyh_id = page_source.xpath('//*[@id="zyh_id"]/@value')[0]
    zyfx_id = page_source.xpath('//*[@id="zyfx_id"]/@value')[0]
    njdm_id = page_source.xpath('//*[@id="njdm_id"]/@value')[0]
    bh_id = page_source.xpath('//*[@id="bh_id"]/@value')[0]
    xsbj = page_source.xpath('//*[@id="xsbj"]/@value')[0]
    xkxnm = page_source.xpath('//*[@id="xkxnm"]/@value')[0]
    xkxqm = page_source.xpath('//*[@id="xkxqm"]/@value')[0]
    xkkz_id = page_source.xpath('//*[@id="firstXkkzId"]/@value')[0]
    print("njdm_id_1:", njdm_id_1)
    print("zyh_id_1:", zyh_id_1)
    print("zyh_id:", zyh_id)
    print("zyfx_id:", zyfx_id)
    print("njdm_id:", njdm_id)
    print("bh_id:", bh_id)
    print("xsbj:", xsbj)
    print("xkxnm:", xsbj)
    print("xkxnm:", xkxnm)
    print("xkxqm:", xkxqm)
    print("xkkz_id:", xkkz_id)
    return njdm_id_1, zyh_id_1, zyh_id, zyfx_id, njdm_id, bh_id, xsbj, xkxnm, xkxqm, xkkz_id

@net_protect
def get_csrf_token():
    resp = session.get('http://*填你自己的/jwglxt/xtgl/login_slogin.html')
    tree = etree.HTML(resp.text)
    csrftoken = tree.xpath('//*[@id="csrftoken"]/@value')[0]
    return csrftoken

def js_encode(mw, pubkey):
    # 调用js
    execjs.get()
    f = open('rsa.js', mode='r', encoding='utf-8')
    js = f.read()
    obj = execjs.compile(js)
    mm = obj.call("encpwd", mw, pubkey)
    # print(mm)
    return mm

def b642hex(base64_data):
    return base64.b64decode(base64_data).hex()

@net_protect
def get_pub_key():
    response = session.get('http://*填你自己的/jwglxt/xtgl/login_getPublicKey.html', verify=False)
    # print(response.text)
    # print(resp.text)  # <class 'str'>
    result = json.loads(response.text)
    modulus = result['modulus']  # N
    pubkey = b642hex(modulus)
    # print(pubkey)
    return pubkey

@net_protect
def log_in(pubkey):
    params = {
        'time': str(int(time.time()*1000)),
    }
    data = {
        'csrftoken': get_csrf_token(),
        'language': 'zh_CN',
        'yhm': school_num,
        'yzm': '*填你自己的',
    }
    data['mm'] = js_encode(jwxt_pwd, pubkey)

    response = session.post('http://*填你自己的/jwglxt/xtgl/login_slogin.html', params=params,data=data, verify=False)
    print(response.text)


def run():
    pubkey = get_pub_key()
    log_in(pubkey)

    njdm_id_1, zyh_id_1, zyh_id, zyfx_id, njdm_id, bh_id, xsbj, xkxnm, xkxqm, xkkz_id = get_pub_params()

    class_info = False
    # -------------------------
    while True:
        selection_system = SelectionSystem(njdm_id_1, zyh_id_1, zyh_id, zyfx_id, njdm_id, bh_id, xsbj, xkxnm, xkxqm,
                                           xkkz_id)

        if not class_info:
            selection_system.get_class_info()
            class_info = True

        kch_id = input(">>>")
        jxb_id = selection_system.get_jxb_id(kch_id)
        flag = selection_system.select(kch_id, jxb_id)
        if flag == "-1":  # test: 0
            # print("人满了,自动进入监测")
            t = Thread(target=selection_system.monitor, args=(kch_id, jxb_id))
            t.start()



if __name__ == '__main__':
    with open(r"你的文件目录") as user_file:
        file_contents = user_file.read()

    parsed_json = json.loads(file_contents)
    # parsed_json = json.loads(r"account.json") fake
    school_num = parsed_json["school_num"]
    jwxt_pwd = parsed_json["jwxt_pwd"]

    HEADER = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    }
    PARAMS = {
        'gnmkdm': '自己填',
        # 'layout': 'default',
        'su': school_num,
    }

    session = requests.Session()
    # session.cookies.update(COOKIE)
    session.headers.update(HEADER)

    run()
