import json
import os
import pathlib
import shutil
import random
import subprocess
import sys
import threading
import time
from bot.core.agents import generate_random_user_agent
from bot.utils import logger
from contextlib import contextmanager
import importlib.util
from importlib.metadata import version, PackageNotFoundError




def get_user_name_list():
    folder_path = "profiles/"
    json_files = [file for file in os.listdir(folder_path) if file.endswith(".json")]
    return json_files

def init_driver():
    from seleniumwire import webdriver

    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from webdriver_manager.chrome import ChromeDriverManager

    web_options = ChromeOptions
    web_manager = ChromeDriverManager

    web_service = ChromeService
    web_driver = webdriver.Chrome

    if not pathlib.Path("webdriver").exists() or len(list(pathlib.Path("webdriver").iterdir())) == 0:
        logger.info("Downloading webdriver. It may take some time...")
        pathlib.Path("webdriver").mkdir(parents=True, exist_ok=True)
        webdriver_path = pathlib.Path(web_manager().install())
        shutil.move(webdriver_path, f"webdriver/{webdriver_path.name}")
        logger.info("Webdriver downloaded successfully")

    webdriver_path = next(pathlib.Path("webdriver").iterdir()).as_posix()

    device_metrics = {"width": 375, "height": 812, "pixelRatio": 3.0}
    user_agent = generate_random_user_agent()

    mobile_emulation = {
        "deviceMetrics": device_metrics,
        "userAgent": user_agent,
    }

    options = web_options()

    options.add_experimental_option("mobileEmulation", mobile_emulation)

    options.add_argument("--headless=old")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_argument("--disable-logging")

    if os.name == 'posix':
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

    return web_driver, web_service, webdriver_path, options


@contextmanager
def create_webdriver(web_driver, web_service, webdriver_path, options):
    driver = web_driver(service=web_service(webdriver_path), options=options)
    try:
        yield driver
    finally:
        driver.quit()


def login_in_browser(auth_url: str, proxy: str, web_driver, web_service, webdriver_path, options):
    from selenium.webdriver.common.by import By
    with create_webdriver(web_driver, web_service, webdriver_path, options) as driver:
        if proxy:
            proxy_options = {
                'proxy': {
                    'http': proxy,
                    'https': proxy,
                }
            }
        else:
            proxy_options = None

        driver = web_driver(service=web_service(webdriver_path), options=options,
                            seleniumwire_options=proxy_options)

        driver.get(auth_url)

        time.sleep(random.randint(7, 15))

        try:
            skip_button = driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/button')
            if skip_button:
                skip_button.click()
                time.sleep(random.randint(2, 5))
        except:
            ...

        time.sleep(5)

        response_text = '{}'

        chr = None

        for request in driver.requests:
            request_body = request.body.decode('utf-8')
            if request.url == "https://api.tapswap.club/api/account/challenge" and 'chr' in request_body:
                chr = request_body

            if request.url == "https://api.tapswap.club/api/account/login":
                response_body = request.response.body.decode('utf-8')


    try:
        chq = json.loads(response_body).get("chq")
        chr = json.loads(chr).get("chr")
    except:
        return None, None

    return chq, chr




def get_chq_and_chr(auth_url, proxy):
    web_driver, web_service, webdriver_path, options = init_driver()

    return login_in_browser(auth_url, proxy, web_driver, web_service, webdriver_path, options)


def update(chq, chr, user_name):
    data = get_user_name_list()

    if str(user_name)+".json" not in data:
        logger.info(f"Created new profile for {user_name} in profile")
        user_json = {
                "chq": chq,
                "chr": chr
        }
        with open(f"profiles/{user_name}.json", "w") as f:
            json.dump(user_json, f, indent=4)

    else:
        user = {
            "chq": chq,
            "chr": chr
        }
        with open(f"profiles/{user_name}.json", "w") as f:
            json.dump(user, f, indent=4)


def process_task(thread_name, tasks):
    for url in tasks:
        logger.info(f"<red>{thread_name}</red> is getting data for {url[2]}...")
        chq ,chr = get_chq_and_chr(url[0], url[1])

        if chq is None or chr is None:
            logger.warning(f"{url[2]} query expired or invaild query.")
        else:
            logger.success(f"<red>{thread_name}</red> Successfully got chq and chr for {url[2]}")

            update(chq, chr, url[2])


def check_and_install_blinker():
    try:
        installed_version = version("blinker")
        if installed_version == "1.7.0":
            logger.info(f"blinker {installed_version} is already installed.")
        else:
            logger.info(f"blinker {installed_version} is installed but not 1.7.0. Installing the correct version.")
            os.system(f"{sys.executable} -m pip install blinker==1.7.0")
            logger.success("blinker 1.7.0 has been installed.")
    except PackageNotFoundError:
        logger.info("blinker is not installed. Installing...")
        os.system(f"{sys.executable} -m pip install blinker==1.7.0")
        logger.info("blinker 1.7.0 has been installed.")


def get_data_(auth_urls):
    num_threads = int(input("Enter the number of threads: "))
    check_and_install_blinker()
    if importlib.util.find_spec("selenium") is None:
        print("Selenium is not installed. Installing")
        os.system(f"{sys.executable} -m pip install selenium")
        print(f"Selenium has been installed.")

    if importlib.util.find_spec("webdriver_manager") is None:
        print("webdriver-manager is not installed. Installing")
        os.system(f"{sys.executable} -m pip install webdriver-manager")
        print(f"webdriver-manager has been installed.")

    if importlib.util.find_spec("seleniumwire") is None:
        print("Selenium-wire is not installed. Installing")
        os.system(f"{sys.executable} -m pip install selenium-wire")
        print(f"Selenium-wire has been installed.")

    num_threads = min(len(auth_urls), num_threads)
    task_chunks = [auth_urls[i::num_threads] for i in range(num_threads)]
    threads = []

    for i in range(num_threads):
        thread_name = f"Thread-{i + 1}"
        thread = threading.Thread(target=process_task, args=(thread_name, task_chunks[i]))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()



if __name__ == "__main__":
    print("ok")
