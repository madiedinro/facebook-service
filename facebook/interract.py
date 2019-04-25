from band import logger, rpc
from typing import Coroutine

def digitalgod_get_user(phone=None, user_id=None, fb_id=None) -> Coroutine:
    return rpc.request('digitalgod', 'get_user', phone=phone, user_id=user_id, fb_id=fb_id)

def digitalgod_get_page_tag(page_url) -> Coroutine:
    return rpc.request('digitalgod', 'get_page_tag', page_url=page_url)

def id_user_tags_add(service_id, tag, lst) -> Coroutine:
    return rpc.request('id', 'user_tags_add', data={'service_id': service_id, 'tag': tag, 'list': lst})

def id_get_redir_data(key) -> Coroutine:
    return rpc.request('id', 'get_redir_data', key=key)

