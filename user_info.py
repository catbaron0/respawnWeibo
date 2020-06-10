import pickle

from weibo.weibo_login import wblogin
from urllib.parse import unquote
from config import SUB

session, uid = wblogin()
session.headers['cookie'] = f'SUB={SUB}'
print('uid: ', uid)
with open('sender.sess', 'wb') as f:
    pickle.dump(session, f)
# try:
#     import ipdb
#     ipdb.set_trace()
#     cookie = session.cookies._cookies['.weibo.cn']['/']['M_WEIBOCN_PARAMS']
#     value = unquote(cookie.value)
#     container_id = value.split('fid=')[1].split('&')[0]
# except Exception:
#     container_id = f'107603{uid}'


url = f'https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}'
try:
    json_data = session.get(url)
    container_id = json_data.json()['data']['tabsInfo']['tabs'][1]['containerid']
except Exception:
    container_id = f'107603{uid}'
print('containerID: ', container_id)
