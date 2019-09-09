import asyncio
import aiohttp
import re
from itertools import count
from urlextract import URLExtract
from band import expose, cleanup, worker, settings as cfg, logger, response, scheduler, rpc
from .interract import digitalgod_get_user, digitalgod_get_page_tag, id_user_tags_add
from .main import client, mp_get_profile
from .social_key import get_post, get_profile

URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""

page_id = str(cfg.fb.page_id)
list_shares = 'shares'

def find_urls(inp):
    return re.findall(URL_REGEX, inp)


def get_to_id(inp, target):
    data = inp.get('data', {})
    if len(data):
        for to in data:
            id = to.get('id')
            if id == target:
                return id


async def wh_handle_mention(value):
    citem = value.pop('item', None)
    verb = value.pop('verb', None)
    if citem == 'post' and verb == 'add':
        post_id = value.pop('post_id', None)
        message = value.pop('message', None)
        logger.debug('c-item=post', value=value, post_id=post_id, message=message)
        post = await get_post(post_id)
        if not post:
            logger.debug('cant get post', post_id=post_id)
            return
        src_user_fb_id, src_post_id = post.get('id').split('_')
        logger.debug('post', p=post)
        user_fb_id, post_id = post.get('id').split('_')
        user = await digitalgod_get_user(fb_id=user_fb_id)
        logger.debug('user', u=user, fb_user_id=user_fb_id)
        if not user or not user.get('user'):
            logger.debug('cant get user', user_fb_id=user_fb_id, post_id=post_id)
            return
        user = user.get('user')
        if not user.get('phone'):
            logger.warn('user has no phone', user=user)
            return

        # Extracting URLs
        extractor = URLExtract()
        urls = find_urls(message)
        link = post.get('link')
        if link:
            urls.append(link)

        to_id = get_to_id(post.get('to', {}), page_id)
        
        if not len(urls):
            logger.debug('links not found', to_id=to_id, user=user)
            return
        
        page_tag = None
        for url in urls:
            if url.startswith('https://digitalgod.be'):
                print(url)
                page_tag = await digitalgod_get_page_tag(url)
                print(page_tag)
        
        if not page_tag or not page_tag.get('tag'):
            logger.debug('no page tag')
            return
        
        page_tag = page_tag.get('tag')
        logger.debug('adding tag to user', page_tag=page_tag, phone=user.get('phone'), post=post, src_user_fb_id=src_user_fb_id, user_fb_id=user_fb_id)
        await id_user_tags_add(service_id=['phone', user.get('phone')], tag=page_tag, lst=list_shares)
        event = {
            'post': post,
            'profile': await get_profile(src_user_fb_id),
            'fb_id': src_user_fb_id
        }
        logger.debug('event', event)
        await rpc.notify('digitalgodbot', 'fb_share', event=event)


handlers = {'mention': wh_handle_mention}


async def wh_handler(data):
    if data.get('object') == 'page':
        for e in data.get('entry', []):
            for c in e.get('changes', []):
                field = c.pop('field', None)
                value = c.pop('value', {})
                handler = handlers.get(field)
                if handler:
                    await handler(value)
            for m in e.get('messaging', []):
                logger.debug('messaging -> item', m=m)
                # {'recipient': {'id': '1040392926136659'}, 'timestamp': 1554966532345, 'sender': {'id': '1921281307989859'}, 'account_linking': {'authorization_code': 'ab3936a2662e5c6a', 'status': 'linked'}}
                sender_id = m.get('sender', {}).get('id')
                m['profile'] = await mp_get_profile(sender_id)
                if m.get('message'):
                    await rpc.notify('digitalgodbot', 'fb_message', item=m)
                if m.get('account_linking'):
                    # 'account_linking': {'authorization_code': 'ab3936a2662e5c6a', 'status': 'linked'}
                    await rpc.notify('digitalgodbot', 'fb_link', item=m)


@expose.handler()
async def wh(data, **params):
    hvt = data.get('hub.verify_token', None)
    if hvt == 'ololo':
        chl = data.get('hub.challenge', None)
        logger.warn('props', hvt, chl)
        return response.data(chl)
    await scheduler.spawn(wh_handler(data))
    return {}
