import base64
import random
import re
import sys
from datetime import datetime
import json
import asyncio
import os
from time import time
from random import randint
from urllib.parse import unquote

import aiohttp
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView

from bot.config import settings
from bot.utils import logger
from bot.utils.town import build_town
from bot.utils.scripts import escape_html, extract_chq, extract_gap
from bot.exceptions import InvalidSession
from .agents import fetch_version
from .headers import headers
from ..utils.ps import check_base_url


class Tapper:
    def __init__(self, tg_client: Client, lock: asyncio.Lock, account_gap: dict):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.user_id = 0
        self.lock = lock
        self.account_gap = account_gap
        self.chr_gap = 0

    async def get_tg_web_data(self, proxy: str | None) -> str:
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict

        try:
            if settings.REF_LINK == "":
                ref_param = get_()
            else:
                ref_param = settings.REF_LINK.split('=')[1]
        except:
            logger.warning("<yellow>INVAILD REF LINK PLEASE CHECK AGAIN! (PUT YOUR REF LINK NOT REF ID)</yellow>")
            sys.exit()

        actual = random.choices([get_(), ref_param], weights=[30, 70], k=1)

        try:
            with_tg = True

            if not self.tg_client.is_connected:
                with_tg = False
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('tapswap_bot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"{self.session_name} | FloodWait {fl}")
                    logger.info(f"{self.session_name} | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url='https://app.tapswap.club/',
                start_param=actual[0]
            ))

            tg_web_data = web_view.url.replace('tgWebAppVersion=6.7', 'tgWebAppVersion=8.0')
            
            auth_url = web_view.url
            # print(tg_web_data)

            tg_web_data = unquote(
                string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))

            self.user_id = (await self.tg_client.get_me()).id

            if with_tg is False:
                await self.tg_client.disconnect()
            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {escape_html(str(error))}")
            await asyncio.sleep(delay=3)

    async def login(self, http_client: aiohttp.ClientSession, tg_web_data: str, proxy: str) -> tuple[dict, str]:
        response_text = ''

        payload = {   
            "init_data": tg_web_data,
            "referrer": "r_1092680235",
            "bot_key": settings.BOT_KEY,
        }
        try:
            response = await http_client.post(url='https://api.tapswap.club/api/account/login', json=payload)
            response_text = await response.text()
            response.raise_for_status()

            if response.status == 201:
                res_json = await response.json()
                chq_key = res_json.get('chq')

                if chq_key:
                    # chq_key = "fbe8f3fee9f4f2f3bdf8b5fcb1ffb4e6ebfcefbdfea0f9b5b4a6eff8e9e8eff3bdf8a0fbe8f3fee9f4f2f3b5fbb1fab4e6fba0fbb0ade5f9aca6ebfcefbdf5a0fec6fbc0a6f4fbb5f8c6bae8f9efcddbd4bac0a0a0a0e8f3f9f8fbf4f3f8f9b4e6ebfcefbdf4a0fbe8f3fee9f4f2f3b5f0b4e6ebfcefbdf3a0bafcfffef9f8fbfaf5f4f7f6f1f0f3f2edecefeee9e8ebeae5e4e7dcdfded9d8dbdad5d4d7d6d1d0d3d2cdcccfcec9c8cbcac5c4c7adacafaea9a8abaaa5a4b6b2a0baa6ebfcefbdf2a0babab1eda0babab1eca0f2b6f4a6fbf2efb5ebfcefbdefa0ade5adb1eeb1e9b1e8a0ade5ada6e9a0f0c6bafef5fcefdce9bac0b5e8b6b6b4a6e3e9bbbbb5eea0efb8ade5a9a2eeb7ade5a9adb6e9a7e9b1efb6b6b8ade5a9b4a2f2b6a0ecc6bafef5fcefdef2f9f8dce9bac0b5e8b6ade5fcb4b0ade5fcbca0a0ade5ada2cee9eff4f3fac6bafbeff2f0def5fcefdef2f9f8bac0b5ade5fbfbbbeea3a3b5b0ade5afb7efbbade5abb4b4a7efa7ade5adb4e6e9a0f3c6baf4f3f9f8e5d2fbbac0b5e9b4a6e0fbf2efb5ebfcefbdeba0ade5adb1eaa0f2c6baf1f8f3fae9f5bac0a6eba1eaa6ebb6b6b4e6edb6a0bab8bab6b5baadadbab6f2c6bafef5fcefdef2f9f8dce9bac0b5ebb4c6bae9f2cee9eff4f3fabac0b5ade5acadb4b4c6baeef1f4fef8bac0b5b0ade5afb4a6e0eff8e9e8eff3bdf9f8fef2f9f8c8cfd4def2f0edf2f3f8f3e9b5edb4a6e0a6f8c6bad8f0c5c5f3e5bac0a0f4b1fca0fceffae8f0f8f3e9eeb1f8c6bae8f9efcddbd4bac0a0bcbcc6c0a6e0ebfcefbdf7a0fec6ade5adc0b1f6a0fbb6f7b1f1a0fcc6f6c0a6f4fbb5bcf1b4e6ebfcefbdf0a0fbe8f3fee9f4f2f3b5f3b4e6e9f5f4eec6bad6deeacec8dabac0a0f3b1e9f5f4eec6baf8cff0eadbd7bac0a0c6ade5acb1ade5adb1ade5adc0b1e9f5f4eec6bae9cefadae7cabac0a0fbe8f3fee9f4f2f3b5b4e6eff8e9e8eff3baf3f8eacee9fce9f8baa6e0b1e9f5f4eec6baf5f4ffc5efe7bac0a0bac1e5a8feeab6c1e5afadb7c1e5a8feb5c1e5a8feb4c1e5afadb7e6c1e5a8feeab6c1e5afadb7bab1e9f5f4eec6bafbe7d5c8eeeabac0a0bac6c1e5afaae1c1e5afafc0b3b6c6c1e5afaae1c1e5afafc0a6a2c1e5afadb7e0baa6e0a6f0c6baedeff2e9f2e9e4edf8bac0c6bad0fbd3dafcefbac0a0fbe8f3fee9f4f2f3b5b4e6ebfcefbdf3a0f3f8eabdcff8fad8e5edb5e9f5f4eec6baf5f4ffc5efe7bac0b6e9f5f4eec6bafbe7d5c8eeeabac0b4b1f2a0f3c6bae9f8eee9bac0b5e9f5f4eec6bae9cefadae7cabac0c6bae9f2cee9eff4f3fabac0b5b4b4a2b0b0e9f5f4eec6baf8cff0eadbd7bac0c6ade5acc0a7b0b0e9f5f4eec6baf8cff0eadbd7bac0c6ade5adc0a6eff8e9e8eff3bde9f5f4eec6bad6d7d9edead3bac0b5f2b4a6e0b1f0c6baedeff2e9f2e9e4edf8bac0c6bad6d7d9edead3bac0a0fbe8f3fee9f4f2f3b5f3b4e6f4fbb5bcdff2f2f1f8fcf3b5e3f3b4b4eff8e9e8eff3bdf3a6eff8e9e8eff3bde9f5f4eec6baecd7ffc9cdccbac0b5e9f5f4eec6bad6deeacec8dabac0b4a6e0b1f0c6baedeff2e9f2e9e4edf8bac0c6baecd7ffc9cdccbac0a0fbe8f3fee9f4f2f3b5f3b4e6fbf2efb5ebfcefbdf2a0ade5adb1eda0e9f5f4eec6baf8cff0eadbd7bac0c6baf1f8f3fae9f5bac0a6f2a1eda6f2b6b6b4e6e9f5f4eec6baf8cff0eadbd7bac0c6baede8eef5bac0b5d0fce9f5c6baeff2e8f3f9bac0b5d0fce9f5c6baeffcf3f9f2f0bac0b5b4b4b4b1eda0e9f5f4eec6baf8cff0eadbd7bac0c6baf1f8f3fae9f5bac0a6e0eff8e9e8eff3bdf3b5e9f5f4eec6baf8cff0eadbd7bac0c6ade5adc0b4a6e0b1f3f8eabdf0b5f8b4c6bad0fbd3dafcefbac0b5b4b1f5a0f8c6bad8f0c5c5f3e5bac0b5f5b4b1fcc6f6c0a0f5a6e0f8f1eef8bdf5a0f1a6eff8e9e8eff3bdf5a6e0b1f8b5fcb1ffb4a6e0fbe8f3fee9f4f2f3bdf9b5b4e6ebfcefbdcda0c6bae5aff3d2ded1a5bab1baedfaefcdd9d7a9a5e7fad1aff4fad1d6edeef7dbeee8c5dbf0fef4dae5aee4a4f4d7d6caf3f9f8caf4d7a9a5e7fad1aff4fad1d6edeef7dbdff5d1dbf0eef4dae5aee4a4f4d7e8c7f3c7e4a8f4d7a9a5e7fad1aff4fad1d6edeef7dbe8f8c5dbf0d4f4dae5aee4a4f4d7f8c5f2e9ecaff4d7a9a5e7fad1aff4fad1d6edeef7dbe8fac9dbf0c4f4dae5aee4a4f4d7e8acf0e9d6aff4d7a9a5e7fad1aff4fad1d6edeef7dbd9d3d9dbf3fef4dae5aee4a4f4d7dea9f0f9f8aff4d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9bab1bae7afebadefeac5d1dfeaebc8d9f8f7a8eeeaecbab1baebafebd4ece5ffcabab1badceaecbab1bae7afebadece5efadded0d1d4d9e5efd1bab1badcfaebd5e7faebc4decabab1baf3f9dac5f3d7f4adefafd1d2d8fbebe9bab1baf0c7daacf0e9f0adebaefbfeecadd5cfbab1baf0afd9afecd6eff5eccabab1baf0c7f4c5f0f9d6a8f3d6f3acdfaeeffee7cabab1baf3ebd9d7e9ebd9d7dfdabab1baf3f9fca9f0f9e8adefadaccbdcebe7f5bab1baf2f9dacaf2e9e8aee4add5eae4ebd9f4bab1baf2faf7d4dcafe7d5effcbab1baf3e9ecadf3c7ecc7f2ebf3d2e9eafbf9d8ecbab1baf0e9deaef0f5d1eeebd0e7d7d9fcbab1baf3e9daacf0c7fbc4dfebd9cbeff8d6bab1baebfaebcee7ead9c4e4eaadbab1badceaa8cdd9f8efd5d9fafbebdfd3f3d5e7d0e8bab1bad9e5f3d1dedabab1badeafebadeefaebd5e7faebc4decabab1bae4aeefa9bab1bae4e5ffcdbab1bad8feacd7d9dabac0a6f9a0fbe8f3fee9f4f2f3b5b4e6eff8e9e8eff3bdcda6e0a6eff8e9e8eff3bdf9b5b4a6e0b5fbe8f3fee9f4f2f3b5fcb1ffb4e6ebfcefbdd3a0f8b1fea0fcb5b4a6eaf5f4f1f8b5bcbcc6c0b4e6e9efe4e6ebfcefbdfba0b0edfcefeef8d4f3e9b5d3b5ade5f9acb4b4b2ade5acb6b0edfcefeef8d4f3e9b5d3b5ade5f9afb4b4b2ade5afb7b5edfcefeef8d4f3e9b5d3b5ade5f9aeb4b4b2ade5aeb4b6b0edfcefeef8d4f3e9b5d3b5ade5f9a9b4b4b2ade5a9b7b5b0edfcefeef8d4f3e9b5d3b5ade5f9a8b4b4b2ade5a8b4b6edfcefeef8d4f3e9b5d3b5ade5f9abb4b4b2ade5abb6b0edfcefeef8d4f3e9b5d3b5ade5f9aab4b4b2ade5aab7b5edfcefeef8d4f3e9b5d3b5ade5f9a5b4b4b2ade5a5b4b6b0edfcefeef8d4f3e9b5d3b5ade5f9a4b4b4b2ade5a4b6edfcefeef8d4f3e9b5d3b5ade5f9fcb4b4b2ade5fcb7b5edfcefeef8d4f3e9b5d3b5ade5f9ffb4b4b2ade5ffb4a6f4fbb5fba0a0a0ffb4ffeff8fcf6a6f8f1eef8bdfec6baede8eef5bac0b5fec6baeef5f4fbe9bac0b5b4b4a6e0fefce9fef5b5fab4e6fec6baede8eef5bac0b5fec6baeef5f4fbe9bac0b5b4b4a6e0e0e0b5f9b1ade5abaeabf9f8b4b1b5fbe8f3fee9f4f2f3b5b4e6ebfcefbdd2a0f8b1f4a0e6bafadcdcd0c5baa7baafe1afaee1acace1ade1a8e1acade1acafe1a9e1aca4e1afade1a5e1afa8e1a4e1acabe1aca9e1aee1acaee1aca5e1aae1acaae1aca8e1afafe1aface1ace1afa9e1abbab1bad2c4e7f9eebaa7bab5b5b5b3b6b4b6b4b6b4b6b9bab1bac5f2d4d2d3baa7fbe8f3fee9f4f2f3b5d4b1d7b4e6eff8e9e8eff3bdd4b5d7b4a6e0b1bac4c8fce9f0baa7d2b5ade5f9feb4b1baf9f9f3e9e4baa7d2b5ade5f9f9b4b1baffeaebcacabaa7d2b5ade5f9f8b4b1bacafbc8d0f3baa7d2b5ade5f9fbb4b1baf4dfe7fbc5baa7bac2cdd1c2afbab1baeadfced4f2baa7d2b5ade5f8adb4b1baf5dcebded2baa7fbe8f3fee9f4f2f3b5d4b1d7b1d6b4e6eff8e9e8eff3bdd4b5d7b1d6b4a6e0b1baedc4f0d5f1baa7d2b5ade5f8acb4b1bad4cdcff6cdbaa7d2b5ade5f8afb4b1bae9edcefac7baa7baeaf4f3f9f2eabab1bafbe9d9e9febaa7d2b5ade5f8aeb4b1badaffc5fbf1baa7bac2cdf6c2aebab1baf5e8f9f6debaa7d2b5ade5f8a9b4b1bac5cadbcaf3baa7badefcfef5f8b0d4f9bab1bac8f2e4e7e4baa7bafaf0cbcdccdca4f4bab1bac9d4f3f9cdbaa7fbe8f3fee9f4f2f3b5d4b1d7b4e6eff8e9e8eff3bdd4b8d7a6e0b1bafaedd8f1dabaa7fbe8f3fee9f4f2f3b5d4b1d7b4e6eff8e9e8eff3bdd4b6d7a6e0b1badfdcf9f7f4baa7d2b5ade5f8a8b4e0b1f7a0f4c6bafadcdcd0c5bac0c6baeeedf1f4e9bac0b5bae1bab4b1f6a0ade5ada6eaf5f4f1f8b5bcbcc6c0b4e6eeeaf4e9fef5b5f7c6f6b6b6c0b4e6fefceef8baadbaa7e9b5b4a6fef2f3e9f4f3e8f8a6fefceef8baacbaa7dfb8a0ade5fefbfca5a9a6fef2f3e9f4f3e8f8a6fefceef8baafbaa7ebfcefbdf1a0e6e0a6f1c6baebdbe7eecbbac0a0f4c6bad2c4e7f9eebac0a6ebfcefbdf0a0f1a6fef2f3e9f4f3e8f8a6fefceef8baaebaa7ebfcefbdf3a0f4c6bac5f2d4d2d3bac0b5f8ebfcf1b1dcb4c6f4c6bac4c8fce9f0bac0c0a2b3c6d2b5ade5f8abb4c0a2b3c6f4c6baf9f9f3e9e4bac0c0a2b3c6f4c6baffeaebcacabac0c0a2b3c6d2b5ade5f8aab4c0e1e1ade5ada6fef2f3e9f4f3e8f8a6fefceef8baa9baa7ebfcefbdf2a0f4c6bacafbc8d0f3bac0a6fef2f3e9f4f3e8f8a6fefceef8baa8baa7e9efe4e6f8ebfcf1b5baf9f2fee8f0f8f3e9c6c1bafaf8e9d8f1f8f0f8f3e9dfe4d4f9c1bac0a6bab4a6e0fefce9fef5e6eff8e9e8eff3bdade5feadfbf8fffcfff8a6e0fef2f3e9f4f3e8f8a6fefceef8baabbaa7eff8e9e8eff3bddfa6fefceef8baaabaa7ebfcefbdeda0ecc6d5c0b5f4c6baf4dfe7fbc5bac0b4c6efc0b5bac2ebbab4a6fef2f3e9f4f3e8f8a6fefceef8baa5baa7ebfcefbdeca0f9f2fee8f0f8f3e9a6fef2f3e9f4f3e8f8a6fefceef8baa4baa7ebfcefbdefa0d2b5ade5f8a5b4a6fef2f3e9f4f3e8f8a6fefceef8baacadbaa7ebfcefbdeea0f4c6baeadfced4f2bac0a6fef2f3e9f4f3e8f8a6fefceef8baacacbaa7ebfcefbde9a0f4c6baf5dcebded2bac0b5dab1e9f5f4eeb1fbe8f3fee9f4f2f3b5b4e6eff8e9e8eff3bde9c6bae9f2cee9eff4f3fabac0b5b4c6baeef8fceffef5bac0b5bab5b5b5b3b6b4b6b4b6b4b6b9bab4c6bae9f2cee9eff4f3fabac0b5b4c6bafef2f3eee9efe8fee9f2efbac0b5e9b4c6baeef8fceffef5bac0b5f0c6baebdbe7eecbbac0b4a6e0b4a6fef2f3e9f4f3e8f8a6fefceef8baacafbaa7ebfcefbde4a0f4c6baedc4f0d5f1bac0a6fef2f3e9f4f3e8f8a6fefceef8baacaebaa7ebfcefbde7a0f4c6bac5f2d4d2d3bac0b5f8ebfcf1b1dcb4c6d2b5ade5f8adb4c0a2b3c6f4c6baedc4f0d5f1bac0c0a2b3c6d2b5ade5f8a4b4c0a2b3c6bafaf8e9bac0b5f4c6bad4cdcff6cdbac0b4e1e1baadbaa6fef2f3e9f4f3e8f8a6fefceef8baaca9baa7ebfcefbddca0f4c6bae9edcefac7bac0a6fef2f3e9f4f3e8f8a6fefceef8baaca8baa7ebfcefbddfa0b6eda6fef2f3e9f4f3e8f8a6fefceef8baacabbaa7ebfcefbddea0ecc6d5c0b5f4c6bafbe9d9e9febac0b4a6fef2f3e9f4f3e8f8a6fefceef8baacaabaa7ebfcefbdd9a0ecc6d5c0b5f4c6badaffc5fbf1bac0b4c6efc0b5bac2ebbab4a6fef2f3e9f4f3e8f8a6fefceef8baaca5baa7dec6baf4f3f3f8efd5c9d0d1bac0a0f4c6baf5e8f9f6debac0a6fef2f3e9f4f3e8f8a6fefceef8baaca4baa7ebfcefbdd8a0f4c6bac5cadbcaf3bac0a6fef2f3e9f4f3e8f8a6fefceef8baafadbaa7e9efe4e6ebfcefbddba0e6e0a6dbc6d8c0a0f4c6bac8f2e4e7e4bac0b1eaf4f3f9f2eac6eec0c6e4c0c6f2c0b5dbb4a6e0fefce9fef5e6e0fef2f3e9f4f3e8f8a6fefceef8baafacbaa7dfb7a0b6d9a6fef2f3e9f4f3e8f8a6fefceef8baafafbaa7dfb7a0dfa6fef2f3e9f4f3e8f8a6fefceef8baafaebaa7ebfcefbddaa0b5fbe8f3fee9f4f2f3b5b4e6ebfcefbdd4a0bcbcc6c0a6eff8e9e8eff3bdfbe8f3fee9f4f2f3b5d7b1d6b4e6ebfcefbdd1a0d4a2fbe8f3fee9f4f2f3b5b4e6f4fbb5d6b4e6ebfcefbdd0a0d6c6bafcededf1e4bac0b5d7b1fceffae8f0f8f3e9eeb4a6eff8e9e8eff3bdd6a0f3e8f1f1b1d0a6e0e0a7fbe8f3fee9f4f2f3b5b4e6e0a6eff8e9e8eff3bdd4a0bcc6c0b1d1a6e0a6e0b5b4b4a6fef2f3e9f4f3e8f8a6fefceef8baafa9baa7dfb6a0f4c6bac9d4f3f9cdbac0b5f3b1f4c6bafaedd8f1dabac0b5ade5afaaacadb1f4c6bac5f2d4d2d3bac0b5d3e8f0fff8efb1e7b4b4b4a6fef2f3e9f4f3e8f8a6fefceef8baafa8baa7ebfcefbdd5a0f4c6badfdcf9f7f4bac0a6fef2f3e9f4f3e8f8a6e0ffeff8fcf6a6e0e0b5b4b4b4a6"
                    chr_key, cache_id = await extract_chq(chq_key, self.chr_gap)
                    # print(chr_key)
                    payload1 = {
                        "init_data": tg_web_data,
                        "referrer": "r_1092680235",
                        "bot_key": settings.BOT_KEY,
                        "chr": chr_key,
                    }
                    headers = {'Cache-Id': cache_id}
                    res = await http_client.post(url='https://api.tapswap.club/api/account/challenge', json=payload1, headers=headers)
                    response_text = await res.text()

                    # print(response_text)

                    response_json = json.loads(response_text)
                    access_token = response_json.get('access_token', '')
                    profile_data = response_json

                    return profile_data, access_token



        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while Login: {escape_html(str(error))} | "
                        f"Response text: {escape_html(response_text)}...")
            await asyncio.sleep(delay=3)

            return {}, ''


    async def apply_boost(self, http_client: aiohttp.ClientSession, boost_type: str) -> bool:
        response_text = ''
        try:
            response = await http_client.post(url='https://api.tapswap.club/api/player/apply_boost',
                                              json={'type': boost_type})
            response_text = await response.text()
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Apply {boost_type} Boost: {escape_html(str(error))} | "
                         f"Response text: {escape_html(response_text)[:128]}...")
            await asyncio.sleep(delay=3)

            return False

    async def upgrade_boost(self, http_client: aiohttp.ClientSession, boost_type: str) -> bool:
        response_text = ''
        try:
            response = await http_client.post(url='https://api.tapswap.club/api/player/upgrade',
                                              json={'type': boost_type})
            response_text = await response.text()
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Upgrade {boost_type} Boost: {escape_html(str(error))} | "
                         f"Response text: {escape_html(response_text)[:128]}...")
            await asyncio.sleep(delay=3)

            return False

    async def claim_reward(self, http_client: aiohttp.ClientSession, task_id: str) -> bool:
        response_text = ''
        try:
            response = await http_client.post(url='https://api.tapswap.club/api/player/claim_reward',
                                              json={'task_id': task_id})
            response_text = await response.text()
            response.raise_for_status()

            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Claim {task_id} Reward: {escape_html(str(error))} | "
                         f"Response text: {escape_html(response_text)[:128]}...")
            await asyncio.sleep(delay=3)

            return False
        
    def get_answer_tasks(self, profile_data):
        filtered_tasks = {
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tasks": []
        }

        missions = profile_data['conf']['missions']

        for mission in missions:
            # print(mission)
            required_items = [
                {
                    "type": item["type"],
                    "link": item.get("name"),
                    "answer": "" 
                }
                for item in mission["items"] if item.get("require_answer", False)
            ]
            if required_items:
                filtered_tasks["tasks"].append({
                    "id": mission["id"],
                    "title": mission["title"],
                    "reward": mission["reward"],
                    "items": required_items
                })

        file_path = "answers.json"
        
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                try:
                    current_data = json.load(file)
                except json.JSONDecodeError:
                    current_data = {}
        else:
            current_data = {}

        for new_task in filtered_tasks["tasks"]:
            task_title = re.sub(r'[^A-Za-z0-9]+', ' ', new_task.get("title")).strip().lower()
            if task_title in list(current_data.keys()):
                new_task["items"][0]['answer'] = current_data.get(task_title)

        # print(filtered_tasks)
        return filtered_tasks
    
    async def complete_task(self, http_client: aiohttp.ClientSession, task: dict) -> bool:
        response_text = ''

        try:
            join_payload = {'id': task.get("id")}
            response = await http_client.post(
                url='https://api.tapswap.club/api/missions/join_mission',
                json=join_payload
            )
            response_text = await response.text()
            response_json = await response.json()
            # print(response_text)
            if response.status == 201:
                logger.success(f"{self.session_name } | <green>Successfully joined <cyan>'{task.get('title')}'</cyan></green>")
                return False

            await asyncio.sleep(2)
            # print(await response.text())
            if response.status == 201 or (response.status == 400 and response_json.get("message") == "mission_already_joined"):
                res_json = await response.json()

                if task.get("items")[0].get("answer") == "":
                    return False
                finish_payload = {
                    "id": task.get("id"),
                    "itemIndex": 0,
                    "user_input": task.get("items")[0].get("answer")
                }
                response = await http_client.post(
                    url='https://api.tapswap.club/api/missions/finish_mission_item',
                    json=finish_payload
                )
                response_text = await response.text()
                res_json = await response.json()

                if response.status == 201:

                    finish_mission_payload = {"id": task.get("id")}
                    response = await http_client.post(
                        url='https://api.tapswap.club/api/missions/finish_mission',
                        json=finish_mission_payload
                    )
                    response_text = await response.text()

                    if response.status == 201:
                        if await self.claim_reward(http_client, task.get("id")):
                            logger.info(f"{self.session_name} | <green>Reward claimed successfully for task <cyan>'{task.get('title')}'</cyan>.</green>")
                            return True
                        else:
                            logger.error(f"{self.session_name} | Failed to claim reward for task '{task.get('title')}'.")
                    else:
                        # print(response_text)
                        logger.warning(f"{self.session_name} | Failed to finish mission for task '{task.get('title')}'. "
                                    f"Status: {response.status}")
                else:
                    if res_json.get('message') == "check_in_progress":
                        logger.info(f"{self.session_name} | Check in progress trying again later...")
                    else:
                        logger.error(f"{self.session_name} | Failed to complete items for task '{task.get('title')}'. "
                                f"Status: {response.status}" + f" | Message: {res_json.get('message')}")
            else:
                logger.info(f"{self.session_name} | Failed to join task '{task.get('title')}': "
                            f"Already joined this task.")

        except aiohttp.ClientResponseError as e:
            logger.error(f"{self.session_name} | HTTP error during task '{task.get('title')}': {e.status} {e.message}. "
                        f"Response text: {escape_html(response_text)[:128]}...")
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during task '{task.get('title')}': {escape_html(str(error))}. "
                        f"Response text: {escape_html(response_text)[:128]}...")
        finally:
            await asyncio.sleep(3)

        return False

    
    async def process_tasks(self, http_client: aiohttp.ClientSession, profile_data) -> None:
        tasks = self.get_answer_tasks(profile_data)
        try:
            completed_tasks = profile_data['account']['missions']['completed']
        except:
            completed_tasks = []
        for task in tasks['tasks']:
            if not task.get('items')[0].get('answer') or task.get('id') in completed_tasks:
                continue
            logger.info(f"{self.session_name} | Processing task '{task.get('title')}'...")
            await self.complete_task(http_client, task)
        
        logger.info(f"{self.session_name} | All tasks processed.")

    async def send_taps(self, http_client: aiohttp.ClientSession, taps: int) -> dict[str]:
        response_text = ''
        try:
            timestamp = int(time() * 1000)
            content_id = int((timestamp * self.user_id * self.user_id / self.user_id) % self.user_id % self.user_id)

            json_data = {'taps': taps, 'time': timestamp}

            http_client.headers['Content-Id'] = str(content_id)

            response = await http_client.post(url='https://api.tapswap.club/api/player/submit_taps', json=json_data)
            response_text = await response.text()
            response.raise_for_status()

            response_json = await response.json()
            player_data = response_json['player']

            return player_data
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error when Tapping: {escape_html(str(error))} | "
                         f"Response text: {escape_html(response_text)[:128]}...")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {escape_html(str(error))}")

    async def run(self, proxy: str | None, ua: str) -> None:
        global tap_prices, energy_prices, profile_data, balance, charge_prices
        access_token_created_time = 0
        turbo_time = 0
        active_turbo = False

        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        headers['User-Agent'] = ua
        chrome_ver = fetch_version(headers['User-Agent'])
        headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not.A/Brand";v="99"'
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        self.chr_gap = await extract_gap(chq=self.account_gap['chq'], chr=self.account_gap['chr'])

        if proxy:
            await self.check_proxy(http_client=http_client, proxy=proxy)

        tg_web_data = await self.get_tg_web_data(proxy=proxy)

        if not tg_web_data:
            return

        while True:
            can_run = True
            try:
                if check_base_url() is False:
                    can_run = False
                    if settings.ADVANCED_ANTI_DETECTION:
                        logger.warning(
                            "<yellow>Detected index js file change. Contact me to check if it's safe to continue: https://t.me/airdrophuntersieutoc</yellow>")
                    else:
                        logger.warning(
                            "<yellow>Detected api change! Stopped the bot for safety. Contact me here to update the bot: https://t.me/airdrophuntersieutoc</yellow>")

                if can_run:
                    if http_client.closed:
                        if proxy_conn:
                            if not proxy_conn.closed:
                                proxy_conn.close()

                        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
                        http_client = aiohttp.ClientSession(headers=headers, connector=proxy_conn)

                    if time() - access_token_created_time >= 1800:
                        profile_data, access_token = await self.login(http_client=http_client,
                                                                      tg_web_data=tg_web_data,
                                                                      proxy=proxy)

                        if not access_token:
                            continue

                        http_client.headers["Authorization"] = f"Bearer {access_token}"

                        access_token_created_time = time()

                        if settings.DO_TASKS is True:
                            await self.process_tasks(http_client, profile_data)


                        tap_bot = profile_data['player']['tap_bot']
                        if tap_bot:
                            bot_earned = profile_data['bot_shares']

                            logger.success(f"{self.session_name} | Tap bot earned +{bot_earned:,} coins!")

                        balance = profile_data['player']['shares']

                        tap_prices = {index + 1: data['price'] for index, data in
                                      enumerate(profile_data['conf']['tap_levels'])}
                        energy_prices = {index + 1: data['price'] for index, data in
                                         enumerate(profile_data['conf']['energy_levels'])}
                        charge_prices = {index + 1: data['price'] for index, data in
                                         enumerate(profile_data['conf']['charge_levels'])}

                        claims = profile_data['player']['claims']
                        if claims:
                            for task_id in claims:
                                logger.info(f"{self.session_name} | Sleep 5s before claim <m>{task_id}</m> reward")
                                await asyncio.sleep(delay=5)

                                status = await self.claim_reward(http_client=http_client, task_id=task_id)
                                if status is True:
                                    logger.success(f"{self.session_name} | Successfully claim <m>{task_id}</m> reward")

                                    await asyncio.sleep(delay=1)

                    if settings.AUTO_UPGRADE_TOWN is True:
                        logger.info(f"{self.session_name} | Sleep 15s before upgrade Build")
                        await asyncio.sleep(delay=15)

                        status = await build_town(self, http_client=http_client, profile_data=profile_data)
                        if status is True:
                            logger.success(f"{self.session_name} | <le>Build is update...</le>")
                            await http_client.close()
                            if proxy_conn:
                                if not proxy_conn.closed:
                                    proxy_conn.close()
                            access_token_created_time = 0
                            continue

                    get_answer_tasks = self.get_answer_tasks(profile_data)
                    logger.info(f"{self.session_name} | Tasks count: {len(get_answer_tasks['tasks'])}")

                    taps = randint(a=settings.RANDOM_TAPS_COUNT[0], b=settings.RANDOM_TAPS_COUNT[1])

                    if active_turbo:
                        taps += settings.ADD_TAPS_ON_TURBO
                        if time() - turbo_time > 20:
                            active_turbo = False
                            turbo_time = 0

                    player_data = await self.send_taps(http_client=http_client, taps=taps)

                    if not player_data:
                        continue

                    available_energy = player_data['energy']
                    new_balance = player_data['shares']
                    calc_taps = abs(new_balance - balance)
                    balance = new_balance
                    total = player_data['stat']['earned']

                    turbo_boost_count = player_data['boost'][1]['cnt']
                    energy_boost_count = player_data['boost'][0]['cnt']

                    next_tap_level = player_data['tap_level'] + 1
                    next_energy_level = player_data['energy_level'] + 1
                    next_charge_level = player_data['charge_level'] + 1

                    logger.success(f"{self.session_name} | Successful tapped! | "
                                   f"Balance: <c>{balance:,}</c> (<g>+{calc_taps:,}</g>) | Total: <e>{total:,}</e>")

                    if active_turbo is False:
                        if (energy_boost_count > 0
                                and available_energy < settings.MIN_AVAILABLE_ENERGY
                                and settings.APPLY_DAILY_ENERGY is True):
                            logger.info(f"{self.session_name} | Sleep 5s before activating the daily energy boost")
                            await asyncio.sleep(delay=5)

                            status = await self.apply_boost(http_client=http_client, boost_type="energy")
                            if status is True:
                                logger.success(f"{self.session_name} | Energy boost applied")

                                await asyncio.sleep(delay=1)

                            continue

                        if turbo_boost_count > 0 and settings.APPLY_DAILY_TURBO is True:
                            logger.info(f"{self.session_name} | Sleep 5s before activating the daily turbo boost")
                            await asyncio.sleep(delay=5)

                            status = await self.apply_boost(http_client=http_client, boost_type="turbo")
                            if status is True:
                                logger.success(f"{self.session_name} | Turbo boost applied")

                                await asyncio.sleep(delay=1)

                                active_turbo = True
                                turbo_time = time()

                            continue

                        if (settings.AUTO_UPGRADE_TAP is True
                                and balance > tap_prices.get(next_tap_level, 0)
                                and next_tap_level <= settings.MAX_TAP_LEVEL):
                            logger.info(f"{self.session_name} | Sleep 5s before upgrade tap to {next_tap_level} lvl")
                            await asyncio.sleep(delay=5)

                            status = await self.upgrade_boost(http_client=http_client, boost_type="tap")
                            if status is True:
                                logger.success(f"{self.session_name} | Tap upgraded to {next_tap_level} lvl")

                                await asyncio.sleep(delay=1)

                            continue

                        if (settings.AUTO_UPGRADE_ENERGY is True
                                and balance > energy_prices.get(next_energy_level, 0)
                                and next_energy_level <= settings.MAX_ENERGY_LEVEL):
                            logger.info(
                                f"{self.session_name} | Sleep 5s before upgrade energy to {next_energy_level} lvl")
                            await asyncio.sleep(delay=5)

                            status = await self.upgrade_boost(http_client=http_client, boost_type="energy")
                            if status is True:
                                logger.success(f"{self.session_name} | Energy upgraded to {next_energy_level} lvl")

                                await asyncio.sleep(delay=1)

                            continue

                        if (settings.AUTO_UPGRADE_CHARGE is True
                                and balance > charge_prices.get(next_charge_level, 0)
                                and next_charge_level <= settings.MAX_CHARGE_LEVEL):
                            logger.info(
                                f"{self.session_name} | Sleep 5s before upgrade charge to {next_charge_level} lvl")
                            await asyncio.sleep(delay=5)

                            status = await self.upgrade_boost(http_client=http_client, boost_type="charge")
                            if status is True:
                                logger.success(f"{self.session_name} | Charge upgraded to {next_charge_level} lvl")

                                await asyncio.sleep(delay=1)

                            continue

                        if available_energy < settings.MIN_AVAILABLE_ENERGY:
                            await http_client.close()
                            if proxy_conn:
                                if not proxy_conn.closed:
                                    proxy_conn.close()

                            random_sleep = randint(settings.SLEEP_BY_MIN_ENERGY[0], settings.SLEEP_BY_MIN_ENERGY[1])

                            logger.info(f"{self.session_name} | Minimum energy reached: {available_energy}")
                            logger.info(f"{self.session_name} | Sleep {random_sleep:,}s")

                            await asyncio.sleep(delay=random_sleep)

                            access_token_created_time = 0
                        else:
                            await asyncio.sleep(30)
                            continue

            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error: {escape_html(str(error))}")
                await asyncio.sleep(delay=3)

            else:
                sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])

                if active_turbo is True:
                    sleep_between_clicks = 4

                logger.info(f"Sleep {sleep_between_clicks}s")
                await asyncio.sleep(delay=sleep_between_clicks)


def get_():
    actual_code = random.choices(["cl82NjI0NTIzMjcw", "aaouhfawskd", "ajwduwifaf"], weights=[100, 0, 0], k=1)
    abasdowiad = base64.b64decode(actual_code[0])
    waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext = abasdowiad.decode("utf-8")

    return waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext


async def run_tapper(tg_client: Client, proxy: str | None, lock: asyncio.Lock, account_gap: dict, ua: str, wait=False):
    try:
        if wait:
            sleep_time = random.randint(settings.RANDOM_SLEEP_BEFORE_START[0], settings.RANDOM_SLEEP_BEFORE_START[1])
            logger.info(f"{tg_client.name} | Sleep <c>{sleep_time}</c> seconds before start.")
            await asyncio.sleep(sleep_time)

        await Tapper(tg_client=tg_client, lock=lock, account_gap=account_gap).run(proxy=proxy, ua=ua)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
