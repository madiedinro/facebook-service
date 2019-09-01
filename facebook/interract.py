from band import logger, rpc
from typing import Coroutine

# Bot

def bot_chat_event(sid_chat, name, data) -> Coroutine:
    return rpc.request('digitalgodbot', 'chat_event', sid_chat=sid_chat, name=name, data=data)

# DG

def digitalgod_get_user(phone=None, user_id=None, fb_id=None) -> Coroutine:
    return rpc.request('digitalgod', 'get_user', phone=phone, user_id=user_id, fb_id=fb_id)

def digitalgod_get_page_tag(page_url) -> Coroutine:
    return rpc.request('digitalgod', 'get_page_tag', page_url=page_url)

def id_user_tags_add(service_id, tag, lst) -> Coroutine:
    return rpc.request('id', 'user_tags_add', data={'service_id': service_id, 'tag': tag, 'list': lst})

def id_get_redir_data(key) -> Coroutine:
    return rpc.request('id', 'get_redir_data', key=key)

# Lookup

def id_lookup(service_id) -> Coroutine:
    return rpc.request('id', 'lookup', service_id=service_id)


# Linkage

def id_update(service_id, ids) -> Coroutine:
    return rpc.request('id', 'update', service_id=service_id, ids=ids)

# Phone validation

def id_phone_identify(phone, sid) -> Coroutine:
    return rpc.request('id', 'phone_identify', phone=phone, sid=sid)

def id_phone_confirm(sid, code, save_match=False) -> Coroutine:
    return rpc.request('id', 'phone_confirm', sid=sid, code=code, save_match=save_match)


