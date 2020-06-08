import pickle

from weibo.weibo_login import wblogin
import requests

session, uid = wblogin()
print('uid: ', uid)
with open('sender.sess', 'wb') as f:
    pickle.dump(session, f)
url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=7187574079'

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    'Cookie': 'SUB=_2A25x_0VVDeThGedG7FIV9y7PzTuIHXVTAGsdrDV6PUJbkdBeLRPVkW1NUQF4CZzf9Ag0epchJ3CKIyoECMa-sjxZ; SUHB=0id65Rgflywwyy; SCF=Au88ZuxBjIpPpu9Z_OekNKo8NHl5jHEV56ypSRFYm5rg-HLvEzRxi42k61i5Zf9iMJX14hC-Uq-TSK0bsR2zcvg.; SSOLoginState=1559966981; MLOGIN=1; _T_WM=34435402017; M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D1076031870470367; WEIBOCN_FROM=1110106030'
}
json_data = requests.get(url, headers=headers)
container_id = json_data.json()['data']['tabsInfo']['tabs'][1]['containerid']
print('containerID: ', container_id)
