

import aiohttp
from band import response, expose, logger, settings as cfg, rpc
from .helpers import msec, xxhasher
from urllib.parse import urlencode
from .main import client
from .interract import id_get_redir_data


xhash = xxhasher(cfg.xxseed)


@expose.handler()
async def auth(data, **params):
    url = client.auth_link(state=data.get('token'))
    return response.redirect(url)


@expose.handler(timeout=5000)
async def account_linking(data, **params):
    """
    https://bolt.rstat.org/alena/fblogin?
        account_linking_token=ARQPHBqhe51U6rtHHhRCiyQDNF8eoMgRG8GhLtgbzb-75nDP4lS9CPElE7Kg2R70qLcW57hcnXiil4HOKFtFC6ZMn4i6XDboP9AzbtHyaHkjcw&
        redirect_uri=https%3A%2F%2Ffacebook.com%2Fmessenger_platform%2Faccount_linking%2F%3Faccount_linking_token%3DARQPHBqhe51U6rtHHhRCiyQDNF8eoMgRG8GhLtgbzb-75nDP4lS9CPElE7Kg2R70qLcW57hcnXiil4HOKFtFC6ZMn4i6XDboP9AzbtHyaHkjcw
        ...
        phone
    """

    raw_phone = data.get('phone')
    code = data.get('code')
    account_linking_token = data.get('account_linking_token')
    id_req = None

    if account_linking_token:
        # Temp Service id; auth code
        auth_code = xhash(account_linking_token)
        sid = ('fblink', auth_code,)

        if not code and raw_phone:
            # request confirmation
            id_req = await rpc.request('id', 'phone_identify', phone=raw_phone, sid=sid)
            logger.debug('id req', resp=id_req)
            if id_req and 'success' in id_req:
                return {'phone_status': 1}

        if code:
            # confirm
            id_req = await rpc.request('id', 'phone_confirm', sid=sid, code=code, save_match=False)
            logger.debug('id req', resp=id_req)
            # Success auth
            if id_req and 'success' in id_req:
                return {'phone_status': 1, 'code_status': 1, 'auth_code': auth_code}
    if id_req and 'error' in id_req:
        return id_req
    logger.warn('smth went wrong', id_req=id_req)
    return {}


@expose.handler(timeout=10000)
async def redirback(uid, data, **params):
    """
    
    """
    logger.debug('fb login', u=uid, d=data, p=params)
    code = data.get('code')
    redir_state = data.get('state')


    if not code:
        return response.error('Code is absent')
    
    if not redir_state:
        return response.error('Invalid state')

    credentials = await client.exchange_code(code)
    if not credentials:
        return response.error('Couldn\'t get credentials')

    me = await client.me(credentials)

    if not me:
        return response.error('Couldn\'t get user info (me)')

    token_debug = await client.debug_token(credentials.get('access_token'))
    logger.debug('debug token; me resp', debresp=token_debug, meresp=me)

    stored_data = await id_get_redir_data(redir_state)
    if not stored_data or not stored_data.get('redir_data'):
        logger.warn('absent redir state', uid=uid, data=data)
    
    redir_data = stored_data.get('redir_data')
    source_sids = redir_data.get('sids')

    if not source_sids:
        logger.error('Invalid state contents', state=redir_data)
        return response.error('Invalid state contents')

    base_vars = {
        'ctime': msec(),
        'source': 'fbauth',
        'event_id': params.get('id')
    }

    fb_params = {
        'access_token': credentials.get('access_token'), 
        **base_vars
    }

    logger.debug('redir data', r=redir_data)
    source_sids_with_params = [(v, {**base_vars},) for k, v in source_sids.items()]
    
    uid_id = ('uid', uid,)
    uid_id_with_params = (uid_id, base_vars,)
    fb_id = ('fb', me.get('id'),)
    fb_id_with_params = (fb_id, fb_params,)
    
    additional_ids = [uid_id_with_params, fb_id_with_params]

    # save fb-to-phone,tg
    await rpc.request('id', 'update', service_id=fb_id, ids=source_sids_with_params)
    
    # save uid-to-fb-tg-phone
    uid_sids = [*source_sids_with_params, fb_id_with_params]
    logger.debug('uid sids', uid_id=uid_id, usids=uid_sids)
    await rpc.request('id', 'update', service_id=uid_id, ids=uid_sids)

    # save phone-to-uid,fb
    if source_sids.get('phone'):
        await rpc.request('id', 'update', service_id=source_sids['phone'], ids=additional_ids)
        profile = await rpc.request('id', 'lookup', service_id=source_sids['phone'])
        logger.debug('new profile', profile)
    

    return response.redirect(cfg.urls.alena_success.url)

