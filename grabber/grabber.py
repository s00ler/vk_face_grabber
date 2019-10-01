import os
import asyncio
import logging

logger = logging.getLogger('vk_grabber')


class Grabber:
    def __init__(self, api, detector, profiles, save_dir, **filters):
        self._api = api
        self._detector = detector

        self._save_dir = save_dir
        self._profiles = profiles
        self._filters = filters

        self.__run = True

        self._user_queue = asyncio.Queue()
        self._photo_queue = asyncio.Queue()

    async def user_fetcher(self, start, stop):
        logger.info('User fetcher started')

        for user_id in range(start, stop):
            if not self.__run:
                break
            user = await self._api.get_user(user_id)

            if user and self._filter_user(user):
                await self._user_queue.put(user_id)
                logger.info(f'User {user_id} got into users queue.')

        logger.info('User fetcher finished')

    async def photo_fetcher(self):
        logger.info('Photo fetcher started')

        while self.__run:
            if not self._user_queue.qsize():
                # NOTE: manual switch task
                await asyncio.sleep(0.1)
                continue
            user_id = await self._user_queue.get()
            photos = await self._api.get_photos(user_id)
            photos_to_crop_urls = self._process_and_filter_photos(photos)
            if photos_to_crop_urls:
                await self._photo_queue.put((user_id, photos_to_crop_urls))
                logger.info(f'User {user_id} photos got into photos queue.')
            else:
                logger.info(f'User {user_id} photos ignored. Incorrect amount.')

        logger.info('Photo fetcher finished')

    async def cropper(self):
        logger.info('Cropper started')
        cropped = 0

        while self.__run:
            if not self._photo_queue.qsize():
                # NOTE: manual switch task
                await asyncio.sleep(0.1)
                continue
            user_id, photos_urls = await self._photo_queue.get()
            profile_crops_saved = False

            for photo_id, url in enumerate(photos_urls):
                response = await self._api.download_photo(url)
                image = self._detector.get_image(response)
                crops = self._detector.get_crops(image, self._filters['MIN_CROP_SIZE'])
                crop_count = len(crops)
                if self._filters['MIN_CROPS'] <= crop_count <= self._filters['MAX_CROPS']:
                    self._write_crops(user_id, photo_id, image, crops)
                    profile_crops_saved = True
                    logger.info(f'Stored crops for user {user_id}, photo {photo_id}, url: {url}')
                else:
                    logger.info(
                        f'Crops for user {user_id}, photo {photo_id}, url {url} ignored. Incorrect amount: {crop_count}'
                    )

            if profile_crops_saved:
                cropped += 1
                logger.info(f'Total profiles cropped: {cropped}')

            if self._profiles == cropped:
                self.__run = False

        logger.info('Cropper finished')

    def _write_crops(self, user_id, photo_id, image, crops):
        user_dir = os.path.join(self._save_dir, str(user_id))
        os.makedirs(user_dir, exist_ok=True)

        for crop_id, (x, y, w, h) in enumerate(crops):
            crop_frame = image[y:y + h, x:x + w]
            crop_name = f'prt_{photo_id:09d}_{crop_id:09d}.jpg'
            self._detector.write_crop(os.path.join(user_dir, crop_name), crop_frame)

    def _process_and_filter_photos(self, photos):
        res = []
        if len(photos) <= self._filters['MAX_PHOTOS']:
            for photo in photos:
                target = None
                for size in photo['sizes']:
                    if size['width'] < self._filters['MIN_PHOTO_W'] or size['height'] < self._filters['MIN_PHOTO_H']:
                        continue
                    if target is None:
                        target = size
                        continue
                    if size['width'] > target['width'] or size['height'] > target['height']:
                        continue
                if target is not None:
                    res.append(target['url'])
            if len(res) < self._filters['MIN_PHOTOS']:
                res = []
        return res

    def _filter_user(self, user):
        return 'photo_id' in user and 'country' in user and user['country']['id'] in self._filters['COUNTRY_CODES']
