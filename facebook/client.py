import aiohttp
from urllib.parse import urlencode
from band import logger


API_3_2 = 'v3.2/'


class FBClient():
    def __init__(self, app_id, app_secret, redirect_uri, scopes=None, access_token=None, **rest):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes or ['email']
        self.access_token = access_token

    async def self_test(self):
        test = await self.fbgraph_query('/6510235916185894912')
        logger.debug('self_test 1', result=test)
        test = await self.debug_token('EAAOJ05PIHRYBAAd5GdY9hZAGJgnVGq8O68ZBFTMn6OzSoCW2WL2aQVooQxfPGZCIhH7Vnid3DKRtVwZBJtCrH0MDbaIbe50j4G9U6ZBvVrh26DZC4noZBANIUprk4kuPt3vCLfpXbb6KQaY7JEx8i3QtvZAZBPhZCZBdZCmwcIP0nXVk0vM9LrmKUfGXeCC4ZCVn3arUY8UZAp7P9LdAZDZD')
        logger.debug('self_test 2', result=test)

    def auth_link(self, state=None, auth_type='rerequest'):
        login_params = {
            'scope': ','.join(self.scopes),
            'client_id': self.app_id,
            'redirect_uri': self.redirect_uri,
            'auth_type': auth_type,
            'state': state
        }

        login_url = f'https://www.facebook.com/v3.2/dialog/oauth?' + urlencode(login_params)
        logger.debug('fb_redir', url=self.redirect_uri)
        return login_url

    async def fbgraph_query(self, resource, extra_params={}, credentials=None, version_segment='v3.2/'):

        """
        graph.facebook.com/debug_token?
            input_token={token-to-inspect}
            &access_token={app-token-or-admin-token}
        """
        params = {}

        if credentials is None:
            params['access_token'] = self.access_token
        if credentials:
            params['access_token'] = credentials.get('access_token')

        params.update(extra_params)

        async with aiohttp.ClientSession() as session:
            url = f'https://graph.facebook.com/{version_segment}' + resource
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                logger.error('fbgraph_query error', status=response.status, text=(await response.text()))

    async def exchange_code(self, code):
        """
        Change received code to access token
        """
        query = {
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'redirect_uri': self.redirect_uri,
            'code': code
        }
        return await self.fbgraph_query('oauth/access_token', query)

    async def me(self, credentials=None):
        """
        Request /me information using provided token
        """
        query = {
            'fields': 'email,name'
        }
        return await self.fbgraph_query('me', query, credentials)

    async def debug_token(self, input_token):
        """
        check provided token
        """
        query = {
            'input_token': input_token
        }
        return await self.fbgraph_query('debug_token', query, version_segment='')
