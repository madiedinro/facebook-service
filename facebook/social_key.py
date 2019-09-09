from typing import Coroutine
from .main import client_page
from band import expose, settings as cfg

@expose()
def get_post(id) -> Coroutine:
    params = {
        'fields': 'child_attachments,created_time,description,from,full_picture,link,message,name,to'
    }
    return client_page.fbgraph_query(f'/{id}', extra_params=params)
    

@expose()
def get_profile(id) -> Coroutine:
    return client_page.fbgraph_query(f'/{id}')
