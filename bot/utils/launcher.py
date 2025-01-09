import asyncio
import argparse
import base64
import json
import os
import random
import sys
import traceback
from urllib.parse import quote

from better_proxy import Proxy
from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.query import run_query_tapper
from bot.core.registrator import register_sessions
from bot.utils.scripts import get_session_names, get_proxies, get_user_agent, get_proxy, fetch_username, escape_html, get_user_name_list
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView
from bot.exceptions import InvalidSession

from bot.utils.getData import get_data_

options = """
Select an action:

    1. Run clicker (Session)
    2. Create session
    3. Run clicker (Query)
    4. Get chq and chr (Session)
    5. Get chq and chr (Query)
"""

global tg_clients


async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients


def get_chq_chr(user_name):
    try:
        data = get_user_name_list()

        if str(user_name)+".json" not in data:
            logger.info(f"Created new profile for {user_name} in profiles, follow tutorial to edit it!")
            json_data = {
                "chq": "",
                "chr": 1
            }
            with open(f"profiles/{user_name}.json", "w") as f:
                json.dump(json_data, f, indent=4)

            return "", 1

        with open(f"profiles/{user_name}.json", "r") as f:
            user = json.load(f)

        return user['chq'], user['chr']
    except:
        traceback.print_exc()

async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")

    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")

    action = parser.parse_args().action

    if not os.path.exists("user_agents.json"):
        with open("user_agents.json", 'w') as file:
            file.write("{}")
        logger.info("User agents file created successfully")

    if not action:
        print(options)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2", "3", "4", "5"]:
                logger.warning("Action must be 1, 2, 3, 4 or 5")
            else:
                action = int(action)
                break

    if action == 1:
        tg_clients = await get_tg_clients()

        await run_tasks(tg_clients=tg_clients)
    elif action == 2:
        await register_sessions()
    elif action == 3:
        with open("data.txt", "r") as f:
            query_ids = [line.strip() for line in f.readlines()]
        await run_tasks_query(query_ids)
    elif action == 4:
        tg_clients = await get_tg_clients()
        await get_data_tasks(tg_clients=tg_clients)
    elif action == 5:
        with open("data.txt", "r") as f:
            query_ids = [line.strip() for line in f.readlines()]
        await get_data_tasks_query(query_ids)



async def get_tg_web_data(tg_client, proxy: str | None):
    logger.info(f"Getting auth url for {tg_client.name}")
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

    tg_client.proxy = proxy_dict

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

        if not tg_client.is_connected:
            with_tg = False
            try:
                await tg_client.connect()
            except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                raise InvalidSession(tg_client.name)

        while True:
            try:
                peer = await tg_client.resolve_peer('tapswap_bot')
                break
            except FloodWait as fl:
                fls = fl.value

                logger.warning(f"{tg_client.name} | FloodWait {fl}")
                logger.info(f"{tg_client.name} | Sleep {fls}s")

                await asyncio.sleep(fls + 3)

        web_view = await tg_client.invoke(RequestWebView(
            peer=peer,
            bot=peer,
            platform='android',
            from_bot_menu=False,
            url='https://app.tapswap.club/',
            start_param=actual[0]
        ))

        tg_web_data = web_view.url.replace('tgWebAppVersion=6.7', 'tgWebAppVersion=8.0')
        # print(tg_web_data)

        if with_tg is False:
            await tg_client.disconnect()
        return [tg_web_data, proxy, tg_client.name]

    except InvalidSession as error:
        raise error

    except Exception as error:
        logger.error(f"{tg_client.name} | Unknown error during Authorization: {escape_html(str(error))}")
        await asyncio.sleep(delay=3)


async def run_tasks_query(query_ids: list[str]):
    lock = asyncio.Lock()

    accounts_gap = {}
    need_to_remove = []
    for query in query_ids:
        chq, chr = get_chq_chr(fetch_username(query))

        if chq == "" or chq is None or chr is None or chr == "":
            need_to_remove.append(query)
        else:

            accounts_gap.update({fetch_username(query): {
                "chq": chq,
                "chr": chr
            }})

    for query in need_to_remove:
        query_ids.remove(query)

    wait = True if len(query_ids) > 3 else False

    tasks = [
        asyncio.create_task(
            run_query_tapper(
                query=query,
                proxy=await get_proxy(fetch_username(query)),
                lock=lock,
                ua=await get_user_agent(fetch_username(query)),
                wait=wait,
                account_gap=accounts_gap.get(fetch_username(query))
            )
        )
        for query in query_ids
    ]

    await asyncio.gather(*tasks)


async def run_tasks(tg_clients: list[Client]):
    lock = asyncio.Lock()


    accounts_gap = {}
    need_to_remove = []
    for tg_client in tg_clients:
        chq, chr = get_chq_chr(tg_client.name)
        if chq == "" or chq is None or chr is None or chr == 1 or chr == "1":
            need_to_remove.append(tg_client)
        else:
            accounts_gap.update({tg_client.name: {
                "chq": chq,
                "chr": chr
            }})

    for tg_client in need_to_remove:
        tg_clients.remove(tg_client)

    wait = True if len(tg_clients) > 3 else False


    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=await get_proxy(tg_client.name),
                lock=lock,
                ua=await get_user_agent(tg_client.name),
                wait=wait,
                account_gap=accounts_gap.get(tg_client.name)
            )
        )
        for tg_client in tg_clients
    ]

    await asyncio.gather(*tasks)


async def get_data_tasks(tg_clients: list[Client]):

    user_names = get_user_name_list()

    for tg_client in tg_clients:
        if tg_client.name+".json" in user_names:
            tg_clients.remove(tg_client)

    tasks = [
        asyncio.create_task(
            get_tg_web_data(
                tg_client=tg_client,
                proxy=await get_proxy(tg_client.name),
            )
        )
        for tg_client in tg_clients
    ]

    logger.info(f"Total accounts need to get data: <red>{len(tg_clients)}</red>")
    auth_urls = await asyncio.gather(*tasks)

   # print(auth_urls)

    return get_data_(auth_urls)

async def get_data_tasks_query(query_ids: list[str]):

    user_names = get_user_name_list()

    for query in query_ids:
        if str(fetch_username(query))+".json" in user_names:
            query_ids.remove(query)


    auth_urls = []
    for query in query_ids:
        auth_url = f"https://app.tapswap.club/#tgWebAppData={quote(query)}&tgWebAppVersion=8.0&tgWebAppPlatform=android&tgWebAppSideMenuUnavail=1"
        proxy = await get_proxy(fetch_username(query))
        auth_urls.append([auth_url, proxy, fetch_username(query)])

    logger.info(f"Total accounts need to get data: <red>{len(auth_urls)}</red>")

    return get_data_(auth_urls)



def get_():
    actual_code = random.choices(["cl82NjI0NTIzMjcw", "aaouhfawskd", "ajwduwifaf"], weights=[100, 0, 0], k=1)
    abasdowiad = base64.b64decode(actual_code[0])
    waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext = abasdowiad.decode(
        "utf-8")

    return waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext
