"""
Band service skeleton
(c) Dmitry Rodin 2018
---------------------
"""
import asyncio
import aiohttp
from itertools import count
from band import expose, cleanup, worker, settings as cfg, logger, response, scheduler, rpc
from .interract import digitalgod_get_user
from .client import FBClient

client = FBClient(**cfg.fb_app)
client_page = FBClient(**cfg.fb_page)

class state:
    events = 0


@worker()
async def worker_work():
    for i in count():
        await asyncio.sleep(60*5)
        logger.debug('fb status', i=i, e=state.events)


async def do_query(url, params, json=None):
    method = 'post' if json else 'get'
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, params=params, json=json) as resp:
            resp_data = await resp.json()
            if resp.status == 200:
                logger.debug('resp data', rd=resp_data, code=resp.status)
                return resp_data
            else:
                logger.error('wrong response', rd=resp_data, code=resp.status)

# https://developers.facebook.com/docs/messenger-platform/introduction/conversation-components

profiles = {}

@expose()
async def mp_get_profile(recipient):
    """
    Messenger Platform get Profile
    """
    cahed_id = str(recipient)
    cached_profile = profiles.get(cahed_id)
    if cached_profile:
        return cached_profile
    url = f'https://graph.facebook.com/{recipient}'
    query = {
        'fields': 'first_name,last_name,profile_pic',
        'access_token': cfg.fb.app_page_token
    }
    resp = await do_query(url, query)
    if resp:
        profiles[cahed_id] = resp
    logger.debug('mp_get_profile', resp=resp)
    return resp


@expose()
async def mp_message(recipient, message):
    """
    Send Messenger Platform message
    """
    request_body = {
        "recipient": {
            "id":  recipient
        },
        "message": message,
        'persona_id': '2273017849617414'
    }

    url = 'https://graph.facebook.com/v2.6/me/messages'
    qs = {
        'access_token': cfg.fb.app_page_token
    }
    await do_query(url, qs, request_body)


@expose()
async def create_persona():
    """
    Messenger Platform create Persona
    """
    request_body = {
        'name': "Alena Mayer",
        'profile_picture_url': "http://bolt.rstat.org/public/images/bot-rounded.png"
    }

    url = 'https://graph.facebook.com/me/personas'
    qs = {
        'access_token': cfg.fb.app_page_token
    }
    return await do_query(url, qs, request_body)


@expose()
async def personas():
    """
    Messenger Platform get Personas
    """
    url = 'https://graph.facebook.com/me/personas'
    qs = {
        'access_token': cfg.fb.app_page_token
    }
    return await do_query(url, qs)


@expose()
async def mp_set_get_started():
    """
    Messenger Platform set "get_started" button
    """
    url = 'https://graph.facebook.com/v2.6/me/messenger_profile'
    qs = {
        'access_token': cfg.fb_page.access_token
    }
    json = {
        'get_started': {
            'payload': 'start'
        }
    }
    return await do_query(url, qs)



@expose()
async def mp_set_greeting():
    """
    Messenger Platform set "get_started" button
    """
    url = 'https://graph.facebook.com/v2.6/me/messenger_profile'
    qs = {
        'access_token': cfg.fb_page.access_token
    }
    json = {
        'greeting': [
            {
                "locale":"default",
                "text":"Hello!" 
            }, {
                "locale":"ru_RU",
                "text":"Привет ! Я "
            }
        ]
    }
    return await do_query(url, qs)


@expose()
async def mp_set_menu():
    """
    Messenger Platform set persistent menu
    """
    url = 'https://graph.facebook.com/v2.6/me/messenger_profile'
    qs = {
        'access_token': cfg.fb_page.access_token
    }

    
    json = {
        "persistent_menu":[
        {
            "locale":"default",
            "composer_input_disabled": True,
            "call_to_actions":[
                {
                "title":"My Account",
                "type":"nested",
                "call_to_actions":[
                    {
                    "title":"Pay Bill",
                    "type":"postback",
                    "payload":"PAYBILL_PAYLOAD"
                    },
                    {
                    "title":"History",
                    "type":"postback",
                    "payload":"HISTORY_PAYLOAD"
                    },
                    {
                    "title":"Contact Info",
                    "type":"postback",
                    "payload":"CONTACT_INFO_PAYLOAD"
                    }
                ]
                },
                # {
                #     "type":"web_url",
                #     "title":"Latest News",
                #     "url":"http://www.messenger.com/",
                #     "webview_height_ratio":"full"
                # }
            ]
        }
        ]
    }
        
    return await do_query(url, qs)


@expose()
async def token_debug(token):
    return await client.debug_token(token)


@expose()
async def me(token):
    return await client.me(token)


@expose()
async def graph(path, params={}):
    creds = {}
    app = params.get('app')
    if app:
        creds = {'access_token': cfg.fb.get(app)}
    return await client.fbgraph_query(path, extra_params=params, credentials=creds)
