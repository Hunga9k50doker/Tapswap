from bot.config import settings

headers = {
    'Accept': '*/*',
    'Accept-Language': 'en',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://app.tapswap.club',
    'Referer': 'https://app.tapswap.club/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Ch-Ua-Mobile': '?1',
    'Sec-Ch-Ua-Platform': '"Android"',
    'X-App': 'tapswap_server',
    'Cache-Id': '',
    'X-Cv': str(settings.X_CV_KEY),
    'X-Touch': str(settings.X_TOUCH_KEY),
}
