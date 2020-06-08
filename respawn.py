import argparse
import json
import tqdm
import pickle
from typing import Dict, Any, List
from time import sleep
from datetime import datetime, timedelta
import random
import re

from weibo.weibo_message import WeiboMessage
from weibo.weibo_sender import WeiboSender
from weibo.weibo_login import wblogin
from logger import logger

parser = argparse.ArgumentParser(description='Fack weibo!')
parser.add_argument(
    '-f', '--json-file',
    dest='json_file',
    type=str,
    help='Path to json file storing weibo data.'
    )
parser.add_argument(
    '-s', '--session-file',
    dest='session_file',
    type=str,
    required=False,
    default="",
    help='Path to pickle file storing session.'
    )
parser.add_argument(
    '-u', '--uid',
    dest='uid',
    type=str,
    required=True,
    help='UID of the weibo account.'
)
parser.add_argument(
    '-c', '--continue-from',
    dest='ctnue',
    type=int,
    required=False,
    default=0,
    help='Continue from thie $ctnue-th weibo of current $json-file'
)
parser.add_argument(
    '-ft', '--force-tweet',
    dest='ft',
    action='store_true',
    help='Force to tweet msg instead of retweet.'
)
args = parser.parse_args()

# Retweet this tweet if the origin one is deleted
DELETED_MID = '4381041336992680'


def cleanhtml(raw_html):
    # Extract webpage links from <a></a>
    # a_tags = re.findall(r'<a .*?/a>', raw_html)
    # Extract urls from <a /> tags
    # urls = [re.search(r"<a .*?(data-url)?.*?(?(1)=|href=)(['\"])(.*?)(\2).*?/a>", a_tag) for a_tag in a_tags]
    # for a_tag, url in zip(a_tags, urls):
    #     raw_html = raw_html.replace(a_tag, url[3]+' ')

    # Replace emoji
    cleantext = re.sub(r"<span class=\"url-icon\"><img alt=(\[.+?\]).+?</span>", r'\1', raw_html)
    # Remove @username links
    cleantext = re.sub(r"<a [^>]*?href='\/n\/.*?'>(@.+?)<.*?/a>", r'\1', cleantext)
    # Remove tag links
    cleantext = re.sub(r"<a .*href=['\"].+ .*>(#.+#)<.+?/a>", r'\1', cleantext)
    # Remove links
    cleantext = re.sub(r"<a .*?(data-url)?.*?(?(1)=|href=)(['\"])(.*?)(\2).*?/a>", r'\3', cleantext)
    # cleantext = re.sub(r"<a .*href=(['\"])([^']+)(\1) .*>网页链接<.+?/a>", r'\2', cleantext)
    # cleantext = re.sub('<.*?>', '', raw_html)
    cleantext = cleantext.replace('<br />', '\n')
    return cleantext


def gen_msg(card: Dict[str, Any], force_tweet: bool) -> WeiboMessage:
    '''
    Generate message from a weibo card.
    Arguments:
        mblog: [Dict], information about this weibo. Generally
               this function set the text. Add the 'create_at' date
               before the text. Keep it shorter than 140 for rt.
               If there is key of 'raw_text', use it instead of text.
               If there is key of 'pics' in mblog, read the list
               of pics, generate pids and pass it to the message.
               If there is key of 'retweeted_status', set msg.rt as
               true, and set the msg.rt_mid.
               If the retweeted_status['deleted'] is '1', use DELETED_MID
               instead of the rt_mid.
    Return:
        msg: [WeiboMessage].
    '''
    mblog: Dict = card['mblog']
    date: str = mblog['created_at']
    if len(date.split('-')) == 2:
        date = '2019-' + date
    text: str = date + '\n' + mblog.get('raw_text', mblog['text'])
    text = cleanhtml(text)
    msg = WeiboMessage(text)
    pics: Dict[str, Any] = dict()
    pids: List[str] = list()
    if 'pics' in mblog:
        pics = mblog.get('pics')
    if 'retweeted_status' in mblog:
        msg.rt = True
        rt = mblog['retweeted_status']
        rt_user = rt.get('user', {})
        deleted = rt.get('deleted', 0)
        rt_exist = not (deleted == '1' or not rt_user)
        if (force_tweet
                or not rt_user
                or str(rt_user.get('id', None)) == '1870470367'):
            msg.rt = False  # the retweeted msg is not exist. Tweet this message instead
            if rt_exist:
                msg.text += '//@'+ u'\ufeff' \
                            + rt['user']['screen_name'] \
                            + ':' + rt['text'].replace('@', '@'+u'\ufeff')
                msg.text = cleanhtml(msg.text)
                if 'pics' in rt:
                    pics = rt['pics']
            else:
                msg.text += '//原微博已被删除'
        else:
            msg.rt_mid = rt.get('idstr', rt['mid'])
            if not rt_exist:
                msg.rt_mid = DELETED_MID
            if len(msg.text) > 140:
                msg.text = msg.text[:135] + "[...]"
    for pic in pics:
        pids.append(pic['pid'])
    msg.pids = "|".join(pids)
    return msg


if args.session_file:
    with open(args.session_file, 'rb') as f:
        session = pickle.load(f)
    uid = args.uid
else:
    session, uid = wblogin()
    print('uid: ', uid)
    with open('sender.sess', 'wb') as f:
        pickle.dump(session, f)

# load json
json_data: Dict[str, Any] = dict()
with open(args.json_file, 'r') as f:
    json_data = json.load(f)

if not json_data:
    logger.info(f'Failed to laod json data from {args.json_file}.')
    exit(1)

sender = WeiboSender(session, uid)

cards = json_data['data']['cards']

# Send weibo from the oldest one
cards.reverse()
ctnue = args.ctnue
for card in tqdm.tqdm(cards[ctnue:]):
    msg: WeiboMessage = gen_msg(card, force_tweet=False)
    # import ipdb;ipdb.set_trace()
    retry = True
    retry_time = 0
    while retry:
        if msg.is_retweet:
            if args.ft:
                # If force_retweet is set
                # Change the retweet to tweet directly
                msg = gen_msg(card, force_tweet=True)
                succ, res = sender.send_weibo(msg)
                wait = 100
            else:
                # If force_retweet is not set
                # Try to retweet first, and tweet it if failed to retweet
                succ, res = sender.rt_weibo(msg)
                if not succ:
                    wait: int = 15 + random.randint(1, 20)
                    logger.info(f'Wait {wait}s before force retweet')
                    sleep(wait)
                    msg = gen_msg(card, force_tweet=True)
                    succ, res = sender.send_weibo(msg)
                    # sleep(wait)
                wait = 100
                logger.info(f'Wait {wait}s after a retweet.')
            # sleep(wait)
        else:
            succ, res = sender.send_weibo(msg)
            wait: int = 15 + random.randint(1, 20)
            logger.info(f'Wait {wait}s')
        sleep(wait)
        res_msg = res.get('msg', '')
        illegal_msg = '微博社区公约'
        similar_msg = 'similar'
        unsafe_msg = 'This URL is not safe'
        unsafe_msg_ch = '安全'
        unsafe_msg_fail = 'fail'
        if (succ or illegal_msg in res_msg
                or unsafe_msg in res_msg
                or similar_msg in res_msg
                or unsafe_msg_ch in res_msg):
            # Successed to tweet or the tweet is illegal. Pass it.
            retry = False
        else:
            retry = True
            retry_time += 1

            if retry_time == 1:
                wait = 7200 + random.randint(1, 50)
            else:
                wait = 3600 * retry
            if res['code'] == '-1':
                wait = 10
            logger.info(f'Wait {wait}s before the {retry_time}th retry')
            next_time = datetime.now() + timedelta(seconds=wait)
            logger.info(f'Restart at {next_time}')
            sleep(wait)
            if retry_time % 3 == 1:
                # In case the failure is caused by expired session
                session, uid = wblogin()
                sender = WeiboSender(session, uid)
                with open('sender.sess', 'wb') as f:
                    pickle.dump(session, f)

# wait = 200 + 150*random.random()
wait = 30
logger.info(f'Wait {wait}s after 10 tweets')
next_time = datetime.now() + timedelta(seconds=wait)
logger.info(f'Restart at {next_time}')

sleep(wait)
