import logging

logger = logging.getLogger('vk_grabber')


class VkApi:
    # got headers from vk_api
    headers = {
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; rv:52.0) '
        'Gecko/20100101 Firefox/52.0'
    }
    _base_url = 'https://api.vk.com/method'
    _version = '5.101'

    def __init__(self, token, session):
        self._token = token
        self._session = session

    async def _fetch(self, url, vk=True):
        async with self._session.get(url) as resp:
            try:
                logger.debug(f'Fetch {resp.url}. Status: {resp.status}')

                if vk:
                    res = await resp.json()
                    res = res['response']
                else:
                    res = await resp.read()

            except Exception as e:
                logger.error(resp, e)
                res = None
            return res

    async def get_user(self, user_id):
        args = {
            'access_token': self._token,
            'v': self._version,
            'user_ids': user_id,
            'fields': 'country,photo_id'
        }

        url = f"{self._base_url}/users.get?{'&'.join([f'{k}={v}' for k, v in args.items()])}"
        resp = await self._fetch(url)

        return None if resp is None else resp[0]

    async def get_photos(self, user_id):
        args = {
            'access_token': self._token,
            'v': self._version,
            'album_id': 'profile',
            'owner_id': user_id,
            'count': 301
        }

        url = f"{self._base_url}/photos.get?{'&'.join([f'{k}={v}' for k, v in args.items()])}"
        resp = await self._fetch(url)

        return None if resp is None else resp['items']

    async def download_photo(self, url):
        # Not related to vk, just uses session
        resp = await self._fetch(url, vk=False)
        return resp
