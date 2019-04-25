from band import expose, cleanup, worker, settings as cfg, logger, response


from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adset import AdSet


my_app_id = cfg.fb_app_id
my_app_secret = cfg.fb_app_secret
my_access_token = cfg.fb_token



auth_url = f"https://graph.facebook.com/oauth/access_token?client_id={cfg.fb_app_id}&client_secret={my_app_secret}&redirect_uri={cfg.redirect}&grant_type=client_credentials"
logger.info(f'auth url: {auth_url}')


FacebookAdsApi.init(my_app_id, my_app_secret, my_access_token)

id = 'act_207528810141959'
account = AdAccount(id)
adsets = account.get_ad_sets(fields=[AdSet.Field.name])

for adset in adsets:
    print(adset[AdSet.Field.name])

# my_accounts = list(me.get_ad_accounts())
# print(my_accounts)

# campaigns = my_account
# print(campaigns)



