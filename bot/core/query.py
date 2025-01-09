import random
import re
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

from bot.config import settings
from bot.utils import logger
from bot.utils.town import build_town
from bot.utils.scripts import escape_html, extract_chq, fetch_username, extract_gap
from bot.exceptions import InvalidSession
from .agents import fetch_version
from .headers import headers
from ..utils.ps import check_base_url


class Tapper:
    def __init__(self, query: str, lock: asyncio.Lock, account_gap: dict):
        self.query = query
        try:
            fetch_data = unquote(query).split("user=")[1].split("&chat_instance=")[0]
            json_data = json.loads(fetch_data)
            self.session_name = json_data['username']
            self.user_id = json_data['id']
        except:
            try:
                fetch_data = unquote(query).split("user=")[1].split("&auth_date=")[0]
                json_data = json.loads(fetch_data)
                self.session_name = json_data['username']
                self.user_id = json_data['id']
            except:
                try:
                    fetch_data = unquote(unquote(query)).split("user=")[1].split("&auth_date=")[0]
                    json_data = json.loads(fetch_data)
                    self.session_name = json_data['username']
                    self.user_id = json_data['id']
                except:
                    try:
                        fetch_data = unquote(unquote(query)).split("user=")[1].split("&auth_date=")[0]
                        json_data = json.loads(fetch_data)
                        self.session_name = json_data['id']
                        self.user_id = json_data['id']
                    except:
                        logger.warning(f"Invaild query: {query}")
                        self.session_name = ""
                        self.user_id = 0

        self.lock = lock
        self.account_gap = account_gap
        self.chr_gap = 0

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
                    # chq_key = "fbe8f3fee9f4f2f3bdf9b5b4e6ebfcefbdd6a0c6baf3e9ffd0d8d6a8a8e8acf8bab1bae4aeefa9bab1bae7afebadefeac5d1dfeaebc8d9f8f7a8eeeaecbab1baebfaebcee7ead9c4e4eaadbab1baebafebd4ece5ffcabab1badceaa8cdd9f8efd5d9fafbebdfd3f3d5e7d0e8bab1bad9e5f3d1dedabab1baedfaefcdd9d7a9a5e7fad1aff4fad1d6edeef7dbe9eaacdbf0fef4dae5aee4a4f4d7daa8f0d7e8a9f4d7a9a5e7fad1aff4fad1d6edeef7dbf2faacdbf0eef4dae5aee4a4f4d7d6caf0f9f8a9f4d7a9a5e7fad1aff4fad1d6edeef7dbe4e8f7dbf0d4f4dae5aee4a4f4d7e8aef3d7fcaef4d7a9a5e7fad1aff4fad1d6edeef7dbeeaeebdbf0c4f4dae5aee4a4f4d7d6aff3e9f4aff4d7a9a5e7fad1aff4fad1d6edeef7dbd8d6e7dbf3fef4dae5aee4a4f4d7d6c5f0f9d6c4f4d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9bab1bae4e5ffcdbab1badeafebadeefaebd5e7faebc4decabab1bae7afebadece5efadded0d1d4d9e5efd1bab1bae5aff3d2ded1a5bab1badceaecbab1badcfaebd5e7faebc4decabab1bad8feacd7d9dabab1baf0e5d9aee9ebfbd6dedabab1baf3e9f8adf0f9fcafd9faa4fadfafe7cbbab1baf0e9e4c4f3e9f8caf3d0d1ead8d0c5ccebfcbab1baf3e9fcc5f3d3fffbeed6eff7e8cabab1baf2f9e4acdcf5d9dceeaed5f4bab1baf2e9fcaef3d7f0c4deaffbf8ecebd5d1bab1baf0c7f4c4f0e9dec4f0d3e7f0deacd1f9eeecbab1baf0c7f8a9f0d7f0a8f0d3f7eddcd6f3d7e9fcbab1baf0e9fca9f2e9d6c4f3aed5f2dff8cdafdffcbac0a6f9a0fbe8f3fee9f4f2f3b5b4e6eff8e9e8eff3bdd6a6e0a6eff8e9e8eff3bdf9b5b4a6e0fbe8f3fee9f4f2f3bdf8b5fcb1ffb4e6ebfcefbdfea0f9b5b4a6eff8e9e8eff3bdf8a0fbe8f3fee9f4f2f3b5fbb1fab4e6fba0fbb0ade5aaada6ebfcefbdf5a0fec6fbc0a6f4fbb5f8c6baf8f5f9cdd0ecbac0a0a0a0e8f3f9f8fbf4f3f8f9b4e6ebfcefbdf4a0fbe8f3fee9f4f2f3b5f0b4e6ebfcefbdf3a0bafcfffef9f8fbfaf5f4f7f6f1f0f3f2edecefeee9e8ebeae5e4e7dcdfded9d8dbdad5d4d7d6d1d0d3d2cdcccfcec9c8cbcac5c4c7adacafaea9a8abaaa5a4b6b2a0baa6ebfcefbdf2a0babab1eda0babab1eca0f2b6f4a6fbf2efb5ebfcefbdefa0ade5adb1eeb1e9b1e8a0ade5ada6e9a0f0c6bafef5fcefdce9bac0b5e8b6b6b4a6e3e9bbbbb5eea0efb8ade5a9a2eeb7ade5a9adb6e9a7e9b1efb6b6b8ade5a9b4a2f2b6a0ecc6bafef5fcefdef2f9f8dce9bac0b5e8b6ade5fcb4b0ade5fcbca0a0ade5ada2cee9eff4f3fac6bafbeff2f0def5fcefdef2f9f8bac0b5ade5fbfbbbeea3a3b5b0ade5afb7efbbade5abb4b4a7efa7ade5adb4e6e9a0f3c6baf4f3f9f8e5d2fbbac0b5e9b4a6e0fbf2efb5ebfcefbdeba0ade5adb1eaa0f2c6baf1f8f3fae9f5bac0a6eba1eaa6ebb6b6b4e6edb6a0bab8bab6b5baadadbab6f2c6bafef5fcefdef2f9f8dce9bac0b5ebb4c6bae9f2cee9eff4f3fabac0b5ade5acadb4b4c6baeef1f4fef8bac0b5b0ade5afb4a6e0eff8e9e8eff3bdf9f8fef2f9f8c8cfd4def2f0edf2f3f8f3e9b5edb4a6e0a6f8c6bacdeaebd2e4f7bac0a0f4b1fca0fceffae8f0f8f3e9eeb1f8c6baf8f5f9cdd0ecbac0a0bcbcc6c0a6e0ebfcefbdf7a0fec6ade5adc0b1f6a0fbb6f7b1f1a0fcc6f6c0a6f4fbb5bcf1b4e6ebfcefbdf0a0fbe8f3fee9f4f2f3b5f3b4e6e9f5f4eec6baf2ebdbfec7d0bac0a0f3b1e9f5f4eec6bac5f9faf9ccc4bac0a0c6ade5acb1ade5adb1ade5adc0b1e9f5f4eec6bad7dad8fef6e9bac0a0fbe8f3fee9f4f2f3b5b4e6eff8e9e8eff3baf3f8eacee9fce9f8baa6e0b1e9f5f4eec6bacbfbe5e4f6d7bac0a0bac1e5a8feeab6c1e5afadb7c1e5a8feb5c1e5a8feb4c1e5afadb7e6c1e5a8feeab6c1e5afadb7bab1e9f5f4eec6bafcd3e7c5f5cbbac0a0bac6c1e5afaae1c1e5afafc0b3b6c6c1e5afaae1c1e5afafc0a6a2c1e5afadb7e0baa6e0a6f0c6baedeff2e9f2e9e4edf8bac0c6bafbeff5efd5d3bac0a0fbe8f3fee9f4f2f3b5b4e6ebfcefbdf3a0f3f8eabdcff8fad8e5edb5e9f5f4eec6bacbfbe5e4f6d7bac0b6e9f5f4eec6bafcd3e7c5f5cbbac0b4b1f2a0f3c6bae9f8eee9bac0b5e9f5f4eec6bad7dad8fef6e9bac0c6bae9f2cee9eff4f3fabac0b5b4b4a2b0b0e9f5f4eec6bac5f9faf9ccc4bac0c6ade5acc0a7b0b0e9f5f4eec6bac5f9faf9ccc4bac0c6ade5adc0a6eff8e9e8eff3bde9f5f4eec6bad9f0eff0f5d6bac0b5f2b4a6e0b1f0c6baedeff2e9f2e9e4edf8bac0c6bad9f0eff0f5d6bac0a0fbe8f3fee9f4f2f3b5f3b4e6f4fbb5bcdff2f2f1f8fcf3b5e3f3b4b4eff8e9e8eff3bdf3a6eff8e9e8eff3bde9f5f4eec6bad6e5d4d0d6d1bac0b5e9f5f4eec6baf2ebdbfec7d0bac0b4a6e0b1f0c6baedeff2e9f2e9e4edf8bac0c6bad6e5d4d0d6d1bac0a0fbe8f3fee9f4f2f3b5f3b4e6fbf2efb5ebfcefbdf2a0ade5adb1eda0e9f5f4eec6bac5f9faf9ccc4bac0c6baf1f8f3fae9f5bac0a6f2a1eda6f2b6b6b4e6e9f5f4eec6bac5f9faf9ccc4bac0c6baede8eef5bac0b5d0fce9f5c6baeff2e8f3f9bac0b5d0fce9f5c6baeffcf3f9f2f0bac0b5b4b4b4b1eda0e9f5f4eec6bac5f9faf9ccc4bac0c6baf1f8f3fae9f5bac0a6e0eff8e9e8eff3bdf3b5e9f5f4eec6bac5f9faf9ccc4bac0c6ade5adc0b4a6e0b1f3f8eabdf0b5f8b4c6bafbeff5efd5d3bac0b5b4b1f5a0f8c6bacdeaebd2e4f7bac0b5f5b4b1fcc6f6c0a0f5a6e0f8f1eef8bdf5a0f1a6eff8e9e8eff3bdf5a6e0b1f8b5fcb1ffb4a6e0b5fbe8f3fee9f4f2f3b5fcb1ffb4e6ebfcefbdd4a0f8b1fea0fcb5b4a6eaf5f4f1f8b5bcbcc6c0b4e6e9efe4e6ebfcefbdfba0b0edfcefeef8d4f3e9b5d4b5ade5aaadb4b4b2ade5acb7b5b0edfcefeef8d4f3e9b5d4b5ade5aaacb4b4b2ade5afb4b6b0edfcefeef8d4f3e9b5d4b5ade5aaafb4b4b2ade5aeb6edfcefeef8d4f3e9b5d4b5ade5aaaeb4b4b2ade5a9b7b5edfcefeef8d4f3e9b5d4b5ade5aaa9b4b4b2ade5a8b4b6b0edfcefeef8d4f3e9b5d4b5ade5aaa8b4b4b2ade5abb6b0edfcefeef8d4f3e9b5d4b5ade5aaabb4b4b2ade5aab6edfcefeef8d4f3e9b5d4b5ade5aaaab4b4b2ade5a5b6edfcefeef8d4f3e9b5d4b5ade5aaa5b4b4b2ade5a4b7b5edfcefeef8d4f3e9b5d4b5ade5aaa4b4b4b2ade5fcb4a6f4fbb5fba0a0a0ffb4ffeff8fcf6a6f8f1eef8bdfec6baede8eef5bac0b5fec6baeef5f4fbe9bac0b5b4b4a6e0fefce9fef5b5fab4e6fec6baede8eef5bac0b5fec6baeef5f4fbe9bac0b5b4b4a6e0e0e0b5f9b1ade5a9fbacfeaab4b1b5fbe8f3fee9f4f2f3b5b4e6ebfcefbdd7a0f8b1f5a0e6baeeedd8d8d1baa7bab5b5b5b3b6b4b6b4b6b4b6b9bab1bae8f8ceecf7baa7fbe8f3fee9f4f2f3b5d9b1d8b1dbb4e6eff8e9e8eff3bdd9b5d8b1dbb4a6e0b1bad6c8d4feecbaa7fbe8f3fee9f4f2f3b5d9b4e6eff8e9e8eff3bdd9b5b4a6e0b1bac7eedac7cdbaa7d7b5ade5aafcb4b1bacefef3d2f5baa7badefcfef5f8b0d4f9bab1baf5e4eafffebaa7baafd3eed9f4dcfbf3bab1bac8d3dfd6fbbaa7d7b5ade5aaffb4b1bad3d7dad3e8baa7fbe8f3fee9f4f2f3b5d9b1d8b4e6eff8e9e8eff3bdd9b5d8b4a6e0b1bac5d7cff4ccbaa7d7b5ade5aafeb4b1baf8ece7d0edbaa7d7b5ade5aaf9b4b1bafefecbc9f7baa7d7b5ade5aaf8b4b1baf2f4def4f6baa7d7b5ade5aafbb4b1badff5e9ead8baa7baf4f3f3f8efd5c9d0d1bab1baedd7fef0efbaa7d7b5ade5a5adb4b1badef0eeeff8baa7bac2d6e8c2aebab1baeec8cbc7f5baa7bac2d0f0c2adbab1bad7e5f9dcf9baa7fbe8f3fee9f4f2f3b5d9b1d8b4e6eff8e9e8eff3bdd9b6d8a6e0e0b1f4a0b5fbe8f3fee9f4f2f3b5b4e6ebfcefbdd9a0bcbcc6c0a6eff8e9e8eff3bdfbe8f3fee9f4f2f3b5d8b1dbb4e6ebfcefbddaa0d9a2fbe8f3fee9f4f2f3b5b4e6f4fbb5dbb4e6ebfcefbdd5a0dbc6bafcededf1e4bac0b5d8b1fceffae8f0f8f3e9eeb4a6eff8e9e8eff3bddba0f3e8f1f1b1d5a6e0e0a7fbe8f3fee9f4f2f3b5b4e6e0a6eff8e9e8eff3bdd9a0bcc6c0b1daa6e0a6e0b5b4b4b1f7a0f5c6bae8f8ceecf7bac0b5f4b1e9f5f4eeb1fbe8f3fee9f4f2f3b5b4e6eff8e9e8eff3bdf7c6bae9f2cee9eff4f3fabac0b5b4c6baeef8fceffef5bac0b5f5c6baeeedd8d8d1bac0b4c6bae9f2cee9eff4f3fabac0b5b4c6bafef2f3eee9efe8fee9f2efbac0b5f7b4c6baeef8fceffef5bac0b5bab5b5b5b3b6b4b6b4b6b4b6b9bab4a6e0b4a6f5c6bad6c8d4feecbac0b5f7b4a6e9efe4e6f8ebfcf1b5baf9f2fee8f0f8f3e9c6c1bafaf8e9d8f1f8f0f8f3e9dfe4d4f9c1bac0a6bab4a6e0fefce9fef5e6eff8e9e8eff3bdade5feadfbf8fffcfff8a6e0ebfcefbdf6a0f5c6bac7eedac7cdbac0b1f1a0d7b5ade5a5acb4b1f0a0d7b5ade5a5afb4b1f3a0f5c6bacefef3d2f5bac0a6e9efe4e6ebfcefbdf2a0e6e0a6f2c6f3c0a0f5c6baf5e4eafffebac0b1eaf4f3f9f2eac6f6c0c6f1c0c6f0c0b5f2b4a6e0fefce9fef5e6e0ebfcefbdeda0f9f2fee8f0f8f3e9b1eca0f5c6bac8d3dfd6fbbac0b1efa0d7b5ade5a5aeb4b1eea0edc6ecc0b5d7b5ade5a5a9b4b4b1e9a0baeaf4f3f9f2eabab1e4a0f5c6bad3d7dad3e8bac0b5f8ebfcf1b1e9b4c6f5c6bac5d7cff4ccbac0c0a2b3c6f5c6baf8ece7d0edbac0c0a2b3c6f5c6bafefecbc9f7bac0c0a2b3c6f5c6baf2f4def4f6bac0c0a2b3c6d7b5ade5a5a8b4c0e1e1ade5adb1e7a0f5c6bad3d7dad3e8bac0b5f8ebfcf1b1e9b4c6d7b5ade5aafcb4c0a2b3c6d7b5ade5a5acb4c0a2b3c6d7b5ade5a5abb4c0a2b3c6bafaf8e9bac0b5d7b5ade5a5aab4b4e1e1baadbaa6eec6f5c6badff5e9ead8bac0c0a0f5c6baedd7fef0efbac0a6ebfcefbddca0edc6ecc0b5f5c6badef0eeeff8bac0b4c6efc0b5bac2ebbab4b1dfa0edc6ecc0b5f5c6baeec8cbc7f5bac0b4c6efc0b5bac2ebbab4b1dea0b6dca6eff8e9e8eff3bddeb7a0deb1deb7a0b6dfb1deb8a0ade5aaa9aca8adb1deb6a0e4b8f5c6bad7e5f9dcf9bac0b5ade5afaaacadb1d3e8f0fff8efb5e7b4b4b1dea6e0b5b4b4b4a6"
                    chr_key, cache_id = await extract_chq(chq_key, self.chr_gap)
                    # print(chr_key)
                    payload1 = {
                        "init_data": tg_web_data,
                        "referrer": "r_1092680235",
                        "bot_key": settings.BOT_KEY,
                        "chr": chr_key,
                    }
                    headers = {'Cache-Id': cache_id}
                    res = await http_client.post(url='https://api.tapswap.club/api/account/challenge',
                                                 json=payload1, headers=headers)
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
            logger.error(
                f"{self.session_name} | Unknown error when Apply {boost_type} Boost: {escape_html(str(error))} | "
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
            logger.error(
                f"{self.session_name} | Unknown error when Upgrade {boost_type} Boost: {escape_html(str(error))} | "
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
            logger.error(
                f"{self.session_name} | Unknown error when Claim {task_id} Reward: {escape_html(str(error))} | "
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
                logger.success(
                    f"{self.session_name} | <green>Successfully joined <cyan>'{task.get('title')}'</cyan></green>")
                return False

            await asyncio.sleep(2)
            # print(await response.text())
            if response.status == 201 or (
                    response.status == 400 and response_json.get("message") == "mission_already_joined"):
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
                            logger.info(
                                f"{self.session_name} | <green>Reward claimed successfully for task <cyan>'{task.get('title')}'</cyan>.</green>")
                            return True
                        else:
                            logger.error(
                                f"{self.session_name} | Failed to claim reward for task '{task.get('title')}'.")
                    else:
                        # print(response_text)
                        logger.warning(
                            f"{self.session_name} | Failed to finish mission for task '{task.get('title')}'. "
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
            logger.error(
                f"{self.session_name} | Unknown error during task '{task.get('title')}': {escape_html(str(error))}. "
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
        global profile_data, balance, tap_prices, energy_prices, charge_prices
        access_token_created_time = 0
        turbo_time = 0
        active_turbo = False

        headers['User-Agent'] = ua
        chrome_ver = fetch_version(headers['User-Agent'])
        headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not.A/Brand";v="99"'

        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        self.chr_gap = await extract_gap(chq=self.account_gap['chq'], chr=self.account_gap['chr'])

        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        if proxy:
            await self.check_proxy(http_client=http_client, proxy=proxy)

        tg_web_data = self.query

        if not tg_web_data:
            return

        while True:
            can_run = True
            if check_base_url() is False:
                can_run = False
                if settings.ADVANCED_ANTI_DETECTION:
                    logger.warning(
                        "<yellow>Detected index js file change. Contact me to check if it's safe to continue: https://t.me/airdrophuntersieutoc</yellow>")
                else:
                    logger.warning(
                        "<yellow>Detected api change! Stopped the bot for safety. Contact me here to update the bot: https://t.me/airdrophuntersieutoc</yellow>")

            try:
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


async def run_query_tapper(query: str, proxy: str | None, lock: asyncio.Lock, account_gap: dict, ua: str, wait=False):
    # print("run_query_tapper")
    try:
        if wait:
            sleep_time = random.randint(settings.RANDOM_SLEEP_BEFORE_START[0], settings.RANDOM_SLEEP_BEFORE_START[1])
            logger.info(f"{fetch_username(query)} | Sleep <c>{sleep_time}</c> seconds before start.")
            await asyncio.sleep(sleep_time)

        await Tapper(query=query, lock=lock, account_gap=account_gap).run(proxy=proxy, ua=ua)
    except InvalidSession:
        logger.error(f"{query} | Invalid Query")
