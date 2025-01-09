import json
import os
import asyncio
import glob
from urllib.parse import unquote
from aiofile import AIOFile
from better_proxy import Proxy
from bot.config import settings
from bot.core.agents import generate_random_user_agent
from bot.utils import logger


def fetch_username(query):
    try:
        fetch_data = unquote(query).split("user=")[1].split("&chat_instance=")[0]
        json_data = json.loads(fetch_data)
        return json_data['id']
    except:
        try:
            fetch_data = unquote(query).split("user=")[1].split("&auth_date=")[0]
            json_data = json.loads(fetch_data)
            return json_data['id']
        except:
            try:
                fetch_data = unquote(unquote(query)).split("user=")[1].split("&auth_date=")[0]
                json_data = json.loads(fetch_data)
                return json_data['id']
            except:
                logger.warning(f"Invaild query: {query}")
                return ""


async def get_user_agent(session_name):
    async with AIOFile('user_agents.json', 'r') as file:
        content = await file.read()
        user_agents = json.loads(content)

    if session_name not in list(user_agents.keys()):
        logger.info(f"{session_name} | Doesn't have user agent, Creating...")
        ua = generate_random_user_agent(device_type='android', browser_type='chrome')
        user_agents.update({session_name: ua})
        async with AIOFile('user_agents.json', 'w') as file:
            content = json.dumps(user_agents, indent=4)
            await file.write(content)
        return ua
    else:
        logger.info(f"{session_name} | Loading user agent from cache...")
        return user_agents[session_name]

def get_un_used_proxy(used_proxies):
    proxies = get_proxies()
    for proxy in proxies:
        if proxy not in used_proxies:
            return proxy
    return None

def get_user_name_list():
    folder_path = "profiles/"
    json_files = [file for file in os.listdir(folder_path) if file.endswith(".json")]
    return json_files

async def get_proxy(session_name):
    if settings.USE_PROXY_FROM_FILE:
        async with AIOFile('proxy.json', 'r') as file:
            content = await file.read()
            proxies = json.loads(content)

        if session_name not in list(proxies.keys()):
            logger.info(f"{session_name} | Doesn't bind with any proxy, binding to a new proxy...")
            used_proxies = [proxy for proxy in proxies.values()]
            proxy = get_un_used_proxy(used_proxies)
            proxies.update({session_name: proxy})
            async with AIOFile('proxy.json', 'w') as file:
                content = json.dumps(proxies, indent=4)
                await file.write(content)
            return proxy
        else:
            logger.info(f"{session_name} | Loading proxy from cache...")
            return proxies[session_name]
    else:
        return None
def get_session_names() -> list[str]:
    return [os.path.splitext(os.path.basename(file))[0] for file in glob.glob("sessions/*.session")]


def escape_html(text: str) -> str:
    text = str(text)
    return text.replace('<', '\\<').replace('>', '\\>')


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies

import subprocess

async def extract_gap(chq: str, chr):
    a, b = await extract_chq(chq, 0)
    return chr-a

async def extract_chq(chq: str, chr_gap) -> tuple[int, str]:
    bytes_array = bytearray(len(chq) // 2)
    xor_key = 157
    for i in range(0, len(chq), 2):
        bytes_array[i // 2] = int(chq[i:i + 2], 16)
    xor_bytes = bytearray(t ^ xor_key for t in bytes_array)
    decoded_xor = xor_bytes.decode("utf-8")
    process = subprocess.Popen(['node', 'chq.mjs', decoded_xor], stdout=subprocess.PIPE)
    output, _ = process.communicate()
    eval_result = output.decode('utf-8').strip()
    chr_key = chr_gap
    chr_key += int(eval_result.split("\n")[0])

    cache_id = eval_result.split(":")[1].strip()

    return chr_key, cache_id

async def main():
    chq = "fbe8f3fee9f4f2f3bdf9b5b4e6ebfcefbdd6a0c6baf3e9e8caf0f9e4adf3f5cdacefacd9d6e7ecbab1baf0d7eca9f3f9fca9f0acefebd9accde5dfcabab1baf0e9e7afe4d6d1ceebaedabab1baf0d7e8caf3d7fcaef3add1cfe8d1f3f4ebfcbab1bae4aeefa9bab1bae4e5ffcdbab1badeafebadeefaebd5e7faebc4decabab1bae7afebadefeac5d1dfeaebc8d9f8f7a8eeeaecbab1bae7afebadece5efadded0d1d4d9e5efd1bab1bae5aff3d2ded1a5bab1baebafebd4ece5ffcabab1badceaa8cdd9f8efd5d9fafbebdfd3f3d5e7d0e8bab1bad9e5f3d1dedabab1baedfaefcdd9d7a9a5e7fad1aff4fad1d6edeef7dbeafbd1dbf0fef4dae5aee4a4f4d7dec7f2f9deadf4d7a9a5e7fad1aff4fad1d6edeef7dbefeaacdbf0eef4dae5aee4a4f4d7f0aef2e9e8aff4d7a9a5e7fad1aff4fad1d6edeef7dbd9eaebdbf0d4f4dae5aee4a4f4d7f4acf3d7dec5f4d7a9a5e7fad1aff4fad1d6edeef7dbeaeaf7dbf0c4f4dae5aee4a4f4d7d6a9f2e9f8caf4d7a9a5e7fad1aff4fad1d6edeef7dbe9fbffdbf3fef4dae5aee4a4f4d7f0aef3e9deaef4d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9a5f1afefcdd9d7a9bab1baebfaebcee7ead9c4e4eaadbab1badceaecbab1badcfaebd5e7faebc4decabab1bad8feacd7d9dabab1baf0c7eca8f3d7f4c4dfaffbecefd0e7f9bab1baf0d7e8aef2f9d6c4f2fad1c4eaf8f7ebefecbab1baf0adf7f3efe8d1eaeafcbab1baf0e9f8c4f3d7e4aef3d6f3f8e9adcdf4eecabab1baf3e9e8c4f2e9eca8f0f5d1f0dcade7f9e4dabac0a6f9a0fbe8f3fee9f4f2f3b5b4e6eff8e9e8eff3bdd6a6e0a6eff8e9e8eff3bdf9b5b4a6e0fbe8f3fee9f4f2f3bdf8b5fcb1ffb4e6ebfcefbdfea0f9b5b4a6eff8e9e8eff3bdf8a0fbe8f3fee9f4f2f3b5fbb1fab4e6fba0fbb0ade5acaafca6ebfcefbdf5a0fec6fbc0a6f4fbb5f8c6baeff2dcfcdff8bac0a0a0a0e8f3f9f8fbf4f3f8f9b4e6ebfcefbdf4a0fbe8f3fee9f4f2f3b5f0b4e6ebfcefbdf3a0bafcfffef9f8fbfaf5f4f7f6f1f0f3f2edecefeee9e8ebeae5e4e7dcdfded9d8dbdad5d4d7d6d1d0d3d2cdcccfcec9c8cbcac5c4c7adacafaea9a8abaaa5a4b6b2a0baa6ebfcefbdf2a0babab1eda0babab1eca0f2b6f4a6fbf2efb5ebfcefbdefa0ade5adb1eeb1e9b1e8a0ade5ada6e9a0f0c6bafef5fcefdce9bac0b5e8b6b6b4a6e3e9bbbbb5eea0efb8ade5a9a2eeb7ade5a9adb6e9a7e9b1efb6b6b8ade5a9b4a2f2b6a0ecc6bafef5fcefdef2f9f8dce9bac0b5e8b6ade5fcb4b0ade5fcbca0a0ade5ada2cee9eff4f3fac6bafbeff2f0def5fcefdef2f9f8bac0b5ade5fbfbbbeea3a3b5b0ade5afb7efbbade5abb4b4a7efa7ade5adb4e6e9a0f3c6baf4f3f9f8e5d2fbbac0b5e9b4a6e0fbf2efb5ebfcefbdeba0ade5adb1eaa0f2c6baf1f8f3fae9f5bac0a6eba1eaa6ebb6b6b4e6edb6a0bab8bab6b5baadadbab6f2c6bafef5fcefdef2f9f8dce9bac0b5ebb4c6bae9f2cee9eff4f3fabac0b5ade5acadb4b4c6baeef1f4fef8bac0b5b0ade5afb4a6e0eff8e9e8eff3bdf9f8fef2f9f8c8cfd4def2f0edf2f3f8f3e9b5edb4a6e0a6f8c6bad4ecfaf7ebc7bac0a0f4b1fca0fceffae8f0f8f3e9eeb1f8c6baeff2dcfcdff8bac0a0bcbcc6c0a6e0ebfcefbdf7a0fec6ade5adc0b1f6a0fbb6f7b1f1a0fcc6f6c0a6f4fbb5bcf1b4e6ebfcefbdf0a0fbe8f3fee9f4f2f3b5f3b4e6e9f5f4eec6bad5d4eae7f9fabac0a0f3b1e9f5f4eec6bae5eccadbebeabac0a0c6ade5acb1ade5adb1ade5adc0b1e9f5f4eec6bae7f1d8d8e9eabac0a0fbe8f3fee9f4f2f3b5b4e6eff8e9e8eff3baf3f8eacee9fce9f8baa6e0b1e9f5f4eec6bafce7c5f4ffedbac0a0bac1e5a8feeab6c1e5afadb7c1e5a8feb5c1e5a8feb4c1e5afadb7e6c1e5a8feeab6c1e5afadb7bab1e9f5f4eec6badcccd4dfcfdfbac0a0bac6c1e5afaae1c1e5afafc0b3b6c6c1e5afaae1c1e5afafc0a6a2c1e5afadb7e0baa6e0a6f0c6baedeff2e9f2e9e4edf8bac0c6badfc8f1f1cdf8bac0a0fbe8f3fee9f4f2f3b5b4e6ebfcefbdf3a0f3f8eabdcff8fad8e5edb5e9f5f4eec6bafce7c5f4ffedbac0b6e9f5f4eec6badcccd4dfcfdfbac0b4b1f2a0f3c6bae9f8eee9bac0b5e9f5f4eec6bae7f1d8d8e9eabac0c6bae9f2cee9eff4f3fabac0b5b4b4a2b0b0e9f5f4eec6bae5eccadbebeabac0c6ade5acc0a7b0b0e9f5f4eec6bae5eccadbebeabac0c6ade5adc0a6eff8e9e8eff3bde9f5f4eec6bad7e7f3d4fee4bac0b5f2b4a6e0b1f0c6baedeff2e9f2e9e4edf8bac0c6bad7e7f3d4fee4bac0a0fbe8f3fee9f4f2f3b5f3b4e6f4fbb5bcdff2f2f1f8fcf3b5e3f3b4b4eff8e9e8eff3bdf3a6eff8e9e8eff3bde9f5f4eec6bad5d8d1ecd9c4bac0b5e9f5f4eec6bad5d4eae7f9fabac0b4a6e0b1f0c6baedeff2e9f2e9e4edf8bac0c6bad5d8d1ecd9c4bac0a0fbe8f3fee9f4f2f3b5f3b4e6fbf2efb5ebfcefbdf2a0ade5adb1eda0e9f5f4eec6bae5eccadbebeabac0c6baf1f8f3fae9f5bac0a6f2a1eda6f2b6b6b4e6e9f5f4eec6bae5eccadbebeabac0c6baede8eef5bac0b5d0fce9f5c6baeff2e8f3f9bac0b5d0fce9f5c6baeffcf3f9f2f0bac0b5b4b4b4b1eda0e9f5f4eec6bae5eccadbebeabac0c6baf1f8f3fae9f5bac0a6e0eff8e9e8eff3bdf3b5e9f5f4eec6bae5eccadbebeabac0c6ade5adc0b4a6e0b1f3f8eabdf0b5f8b4c6badfc8f1f1cdf8bac0b5b4b1f5a0f8c6bad4ecfaf7ebc7bac0b5f5b4b1fcc6f6c0a0f5a6e0f8f1eef8bdf5a0f1a6eff8e9e8eff3bdf5a6e0b1f8b5fcb1ffb4a6e0b5fbe8f3fee9f4f2f3b5fcb1ffb4e6ebfcefbdd4a0f8b1fea0fcb5b4a6eaf5f4f1f8b5bcbcc6c0b4e6e9efe4e6ebfcefbdfba0edfcefeef8d4f3e9b5d4b5ade5acaafcb4b4b2ade5acb6edfcefeef8d4f3e9b5d4b5ade5acaaffb4b4b2ade5afb6b0edfcefeef8d4f3e9b5d4b5ade5acaafeb4b4b2ade5aeb7b5b0edfcefeef8d4f3e9b5d4b5ade5acaaf9b4b4b2ade5a9b4b6b0edfcefeef8d4f3e9b5d4b5ade5acaaf8b4b4b2ade5a8b6b0edfcefeef8d4f3e9b5d4b5ade5acaafbb4b4b2ade5abb6edfcefeef8d4f3e9b5d4b5ade5aca5adb4b4b2ade5aab6b0edfcefeef8d4f3e9b5d4b5ade5aca5acb4b4b2ade5a5b7b5b0edfcefeef8d4f3e9b5d4b5ade5aca5afb4b4b2ade5a4b4a6f4fbb5fba0a0a0ffb4ffeff8fcf6a6f8f1eef8bdfec6baede8eef5bac0b5fec6baeef5f4fbe9bac0b5b4b4a6e0fefce9fef5b5fab4e6fec6baede8eef5bac0b5fec6baeef5f4fbe9bac0b5b4b4a6e0e0e0b5f9b1ade5fea8ffa5afb4b1b5fbe8f3fee9f4f2f3b5b4e6ebfcefbdd7a0f8b1f5a0e6bafce7dbeccfbaa7bab5b5b5b3b6b4b6b4b6b4b6b9bab1baf1cbf3d0dfbaa7d7b5ade5aca5aeb4b1bad6e9eedecdbaa7d7b5ade5aca5a9b4b1bae4cadacfedbaa7d7b5ade5aca5a8b4b1bac8d6c7d4d0baa7badefcfef5f8b0d4f9bab1bad5d1c8e7ebbaa7baedc9cfd9efa9f3ffbab1baf8dee7fbfabaa7d7b5ade5aca5abb4b1bad6eadbe7efbaa7d7b5ade5aca5aab4b1bae7eed6fed7baa7d7b5ade5aca5a5b4b1bacfe7f1e8cdbaa7baeaf4f3f9f2eabab1baedfad0edf6baa7fbe8f3fee9f4f2f3b5d9b1d8b4e6eff8e9e8eff3bdd9b5d8b4a6e0b1bae9d2d8f3cabaa7d7b5ade5aca5a4b4b1baeaf5ebf9f6baa7d7b5ade5aca5fcb4b1bafffed7cfffbaa7d7b5ade5aca5ffb4b1badbdee8fcd8baa7baf4f3f3f8efd5c9d0d1bab1baf9f3fad7e8baa7d7b5ade5aca5feb4b1baeed9d6f5fcbaa7bac2d1cdc2a9bab1bad7edd5cedfbaa7fbe8f3fee9f4f2f3b5d9b1d8b4e6eff8e9e8eff3bdd9b8d8a6e0b1badacdfbd6fcbaa7fbe8f3fee9f4f2f3b5d9b1d8b4e6eff8e9e8eff3bdd9b6d8a6e0e0b1f4a0b5fbe8f3fee9f4f2f3b5b4e6ebfcefbdd9a0bcbcc6c0a6eff8e9e8eff3bdfbe8f3fee9f4f2f3b5d8b1dbb4e6ebfcefbddaa0d9a2fbe8f3fee9f4f2f3b5b4e6f4fbb5dbb4e6ebfcefbdd5a0dbc6bafcededf1e4bac0b5d8b1fceffae8f0f8f3e9eeb4a6eff8e9e8eff3bddba0f3e8f1f1b1d5a6e0e0a7fbe8f3fee9f4f2f3b5b4e6e0a6eff8e9e8eff3bdd9a0bcc6c0b1daa6e0a6e0b5b4b4b1f7a0f4b5e9f5f4eeb1fbe8f3fee9f4f2f3b5b4e6eff8e9e8eff3bdf7c6bae9f2cee9eff4f3fabac0b5b4c6baeef8fceffef5bac0b5bab5b5b5b3b6b4b6b4b6b4b6b9bab4c6bae9f2cee9eff4f3fabac0b5b4c6bafef2f3eee9efe8fee9f2efbac0b5f7b4c6baeef8fceffef5bac0b5f5c6bafce7dbeccfbac0b4a6e0b4a6f7b5b4a6e9efe4e6f8ebfcf1b5baf9f2fee8f0f8f3e9c6c1bafaf8e9d8f1f8f0f8f3e9dfe4d4f9c1bac0a6bab4a6e0fefce9fef5e6eff8e9e8eff3bdade5feadfbf8fffcfff8a6e0ebfcefbdf6a0f5c6baf1cbf3d0dfbac0b1f1a0f5c6bad6e9eedecdbac0b1f0a0f5c6bae4cadacfedbac0b1f3a0f5c6bac8d6c7d4d0bac0a6e9efe4e6ebfcefbdf2a0e6e0a6f2c6f3c0a0f5c6bad5d1c8e7ebbac0b1eaf4f3f9f2eac6f6c0c6f1c0c6f0c0b5f2b4a6e0fefce9fef5e6e0ebfcefbdeda0f9f2fee8f0f8f3e9b1eca0f5c6baf8dee7fbfabac0b1efa0f5c6bad6eadbe7efbac0b1eea0edc6ecc0b5f5c6bae7eed6fed7bac0b4b1e9a0f5c6bacfe7f1e8cdbac0b1e4a0f5c6baedfad0edf6bac0b5f8ebfcf1b1e9b4c6d7b5ade5aca5f9b4c0a2b3c6f5c6bae9d2d8f3cabac0c0a2b3c6f5c6baeaf5ebf9f6bac0c0a2b3c6f5c6bafffed7cfffbac0c0a2b3c6d7b5ade5aca5f8b4c0e1e1ade5adb1e7a0f8ebfcf1b5e9b4c6f5c6baf1cbf3d0dfbac0c0a2b3c6f5c6bad6e9eedecdbac0c0a2b3c6d7b5ade5aca5fbb4c0a2b3c6bafaf8e9bac0b5d7b5ade5aca4adb4b4e1e1baadbaa6eec6f5c6badbdee8fcd8bac0c0a0f5c6baf9f3fad7e8bac0a6ebfcefbddca0edc6ecc0b5bac2d1cdc2a9bab4c6efc0b5bac2ebbab4b1dfa0edc6ecc0b5f5c6baeed9d6f5fcbac0b4c6efc0b5bac2ebbab4b1dea0b6dca6eff8e9e8eff3bddeb7a0deb1deb7a0b6dfb1deb8a0ade5a4acaefcabb1deb6a0f5c6bad7edd5cedfbac0b5e4b1f5c6badacdfbd6fcbac0b5ade5afaaacadb1d3e8f0fff8efb5e7b4b4b4b1dea6e0b5b4b4b4a6"
    chr_key, cache_id = await extract_chq(chq, 0)
    print("chr_key:", chr_key)
    print("cache_id:", cache_id)



if __name__ == '__main__':
    
    asyncio.run(main())
