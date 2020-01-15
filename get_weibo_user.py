# -*- coding: utf-8 -*-

import requests, pyquery, pymongo
import re, time, json, logging

logging.getLogger('urllib3').setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s")
handler = logging.StreamHandler()
handler.setFormatter(formatter)
mylog = logging.getLogger('x')
mylog.propagate = 0
mylog.addHandler(handler)

db_mg = pymongo.MongoClient(host='127.0.0.1', port=27017)['spider']
mg_wu = db_mg['weibo_user']
mg_wu.create_index([('uid', 1)], unique=True)


cookies = {'Cookie': '_T_WM=18408538387; SUB=_2A25wmDwnDeRhGeRI71EQ8CbNyz-IHXVQY0RvrDV6PUJbktAKLVrRkW1NUrumEWS4IP7xh37khZhh6GYRDpYZajik; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9W5OqQxUe0pZAYaR58UXSHFS5JpX5KzhUgL.FozcShepehnpehe2dJLoIEBLxKqLBoeL1K-LxK-LB-BLBKqLxK-LB.eL1K2LxK.LB-BL1hzt; SUHB=0btt_506OB7mj8; SSOLoginState=1570524280; MLOGIN=1; M_WEIBOCN_PARAMS=lfid%3D102803%26luicode%3D20000174'}
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.221 Safari/537.36 SE 2.X MetaSr 1.0"}
def get_user(uid="210926262"):
    content = requests.get('https://weibo.com/%s' % uid, timeout=20, headers=headers, cookies=cookies).content.decode('utf-8')
    html = "\n\n".join([json.loads(d).get('html', "") for d in re.findall('FM.view\(({[\s\S]+?})\)', content)])
    pq = pyquery.PyQuery(html)
    other = dict([[x.find('span[class="item_ico W_fl"] em').text(), x.find('span[class="item_text W_fl"]').text()] for x in pq.find('div[class="WB_innerwrap"] ul[class="ul_detail"] li').items()])
    userInfo = {
        'uid': uid,
        'page_id': re.search("\$CONFIG\['page_id'\]='(\d+)'", content).group(1),
        "name": pq.find('div[class="pf_username"] h1').text(),
        'photo': pq.find('div[class="pf_photo"] img').attr("src"),
        'intro': pq.find('div[class="pf_intro"]').text(),
        'sex': {'W_icon icon_pf_female': '女', 'W_icon icon_pf_male': '男'}.get(pq.find('div[class="pf_username"] span[class="icon_bed"] a i').attr('class'), None),
        'member_grade': re.sub('.*icon_member_?(\d+|dis)$', r'\1', pq.find('div[class="pf_username"] a[title="微博会员"] em').attr('class') or ""),
        'area': other.get("2"),
        'wb': dict([(it.find('span').text(), int(it.find('strong').text())) for it in pq.find('table[class="tb_counter"] td[class="S_line1"]').items()]),
        'background_image': re.sub('background-image:url\((.+?)\)', r"https:\1" , pq.find('div[class="cover_wrap"]').attr("style") or ""),
        'update_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    }
    return userInfo


def get_guanzhu(page_id='1006051259110474', page=1, uids=None):
    uids = uids or []
    content = requests.get('https://weibo.com/p/%s/follow?page=%s&ajaxpagelet=1&ajaxpagelet_v6=1' % (page_id, page), timeout=20, headers=headers, cookies=cookies).content.decode('utf-8')
    html = "\n\n".join([json.loads(d).get('html', "") for d in re.findall('FM.view\(({[\s\S]+?})\)', content)])
    pq = pyquery.PyQuery(html)
    for it in pq.find('ul[class="follow_list"] li[class="follow_item S_line2"]').items():
        g = re.search('uid=(\d+)&', it.attr('action-data'))
        if g:
            uids.append(g.group(1))
    if page < 6 and pq.find('div[class="W_pages"] a').eq(-2).text() and int(pq.find('div[class="W_pages"] a').eq(-2).text()) > page:
        return get_guanzhu(page_id, page+1, uids)
    return uids

def main():
    for d in list(mg_wu.find({}, {"_id": 0, 'crawl_count': 0}).sort([("crawl_count", 1)]).limit(10)) or [get_user()]:
        try:
            uids = get_guanzhu(d['page_id'])
            noUids = [x['uid'] for x in mg_wu.find({"uid": {'$in': uids}, 'update_time': {'$gt': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() - 30*24*3600))}}, {"uid": 1})]
        except Exception as e:
            mylog.exception(e)
        else:
            for uid in set(uids).difference(set(noUids)):
                try:
                    data = get_user(uid)
                    mg_wu.update({"uid": data['uid']}, {"$set": data, "$inc": {'crawl_count': 1}}, upsert=True)
                except Exception as e:
                    mylog.exception(uid + " %s" % e)
            mg_wu.update({"uid": d['uid']}, {"$set": d, "$inc": {'crawl_count': 1}}, upsert=True)

if __name__ == '__main__':
    while 1:
        try:
            main()
        except Exception as e:
            mylog.exception(e)
        time.sleep(60 * 10)
