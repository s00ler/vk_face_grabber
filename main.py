import asyncio
import logging

import aiohttp

from grabber import Grabber
from vk_wrapper import VkApi
from face_detection import Detector


# TODO: Move to config.json
VK_TOKEN = '1dd101671dd101671dd10167531dbc298211dd11dd101674043224dc6e80e12629c9ef3'
PATH_TO_WEIGHTS = 'face_detection/haarcascade_frontalface_default.xml'

COUNTRY_CODES = {4}  # Казахстан

MIN_PHOTOS = 3
MAX_PHOTOS = 300

MIN_PHOTO_W = 50
MIN_PHOTO_H = 50

MIN_CROPS = 1
MAX_CROPS = 5

MIN_CROP_SIZE = (30, 30)

DEST_DIR = 'dataset'

PROFILES = 256


logger = logging.getLogger('vk_grabber')
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)


async def main():
    async with aiohttp.ClientSession(headers=VkApi.headers) as session:
        api = VkApi(VK_TOKEN, session)
        detector = Detector(PATH_TO_WEIGHTS)
        grabber = Grabber(
            api=api,
            detector=detector,
            profiles=PROFILES,
            save_dir=DEST_DIR,

            COUNTRY_CODES=COUNTRY_CODES,
            MIN_PHOTOS=MIN_PHOTOS,
            MAX_PHOTOS=MAX_PHOTOS,
            MIN_PHOTO_W=MIN_PHOTO_W,
            MIN_PHOTO_H=MIN_PHOTO_H,
            MIN_CROPS=MIN_CROPS,
            MAX_CROPS=MAX_CROPS,
            MIN_CROP_SIZE=MIN_CROP_SIZE,
        )
        try:
            # TODO: Automate workers start, so main gets start/end ids from argv
            # and all workers mill it together
            # TODO: User concurrent.futures.ProcessPoolExcecutor with loop.run_in_executror(...)
            mil = 10 ** 6
            tasks = [
                asyncio.create_task(grabber.user_fetcher(1, mil)),
                asyncio.create_task(grabber.user_fetcher(mil, 2 * mil)),
                asyncio.create_task(grabber.user_fetcher(2 * mil, 3 * mil)),
                asyncio.create_task(grabber.user_fetcher(3 * mil, 4 * mil)),
                asyncio.create_task(grabber.user_fetcher(4 * mil, 5 * mil)),
                asyncio.create_task(grabber.user_fetcher(5 * mil, 6 * mil)),
                asyncio.create_task(grabber.user_fetcher(6 * mil, 7 * mil)),
                asyncio.create_task(grabber.user_fetcher(7 * mil, 8 * mil)),
                asyncio.create_task(grabber.user_fetcher(8 * mil, 9 * mil)),
                asyncio.create_task(grabber.user_fetcher(9 * mil, 10 * mil)),
                asyncio.create_task(grabber.user_fetcher(10 * mil, 11 * mil)),

                asyncio.create_task(grabber.photo_fetcher()),
                asyncio.create_task(grabber.photo_fetcher()),
                asyncio.create_task(grabber.photo_fetcher()),

                asyncio.create_task(grabber.cropper())
            ]
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info('Manual stop triggered')

if __name__ == '__main__':
    asyncio.run(main())
