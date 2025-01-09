## Table of Contents

- [Recommendation before use](#recommendation-before-use)
- [Features](#features)
- [Settings](#settings)
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Obtaining API Keys](#obtaining-api-keys)
- [Installation](#installation)
- [Get chq and chr](#Get-chq-and-chr)

> [!WARNING]
> ⚠️ I do my best to avoid detection of bots, but using bots is forbidden in all airdrops. i cannot guarantee that you will not be detected as a bot. Use at your own risk. I am not responsible for any consequences of using this software.

# 🔥🔥 Use PYTHON 3.10 - 3.11 🔥🔥

## Features

| Feature                                                        | Supported |
| -------------------------------------------------------------- | :-------: |
| Multithreading                                                 |    ✅     |
| Proxy binding to session                                       |    ✅     |
| Auto-purchase of items if you have coins (tap, energy, charge) |    ✅     |
| Auto tasks                                                     |    ✅     |
| Auto click                                                     |    ✅     |
| Auto upgrade town                                              |    ✅     |
| Support for pyrogram .session / Query                          |    ✅     |

## [Settings]

| Settings                    |                                Description                                 |
| --------------------------- | :------------------------------------------------------------------------: |
| **API_ID / API_HASH**       |  Platform data from which to run the Telegram session (default - android)  |
| **REF_LINK**                |                    Put your ref link here (default: "")                    |
| **AUTO_TASK**               |                       Auto do tasks (default: True)                        |
| **AUTO_GAME**               |                       Auto play game (default: True)                       |
| **MAX_POINTS**              |               Maximum points to get each game (default: 220)               |
| **MAX_POINTS**              |               Minimum points to get each game (default: 180)               |
| **DELAY_EACH_ACCOUNT**      |         Random delay bewteen accounts (default: [20, 30] seconds)          |
| **ADVANCED_ANTI_DETECTION** |            Add more protection for your account (default: True)            |
| **USE_PROXY_FROM_FILE**     | Whether to use a proxy from the bot/config/proxies.txt file (True / False) |

## Quick Start

To install libraries and run bot - open run.bat on Windows

## Prerequisites

Before you begin, make sure you have the following installed:

- [Python](https://www.python.org/downloads/) **IMPORTANT**: Make sure to use **3.10 - 3.11**.
- [Nodejs](https://nodejs.org/en) Make sure to use nodejs 20+

## Obtaining API Keys

1. Go to my.telegram.org and log in using your phone number.
2. Select "API development tools" and fill out the form to register a new application.
3. Record the API_ID and API_HASH provided after registering your application in the .env file.

## Installation

You can download the [**repository**](https://github.com/Hunga9k50doker/Tapswap) by cloning it to your system and installing the necessary dependencies:

```shell
git clone https://github.com/Hunga9k50doker/Tapswap.git
cd Tapswap
```

Then you can do automatic installation by typing:

Windows:

```shell
run.bat
```

Linux:

```shell
run.sh
```

# Linux manual installation

```shell
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
cp .env-example .env
nano .env  # Here you must specify your API_ID and API_HASH, the rest is taken by default
npm install jsdom
python3 main.py
```

You can also use arguments for quick start, for example:

```shell
~/Tapswap >>> python3 main.py --action (1/2)
# Or
~/Tapswap >>> python3 main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

# Windows manual installation

```shell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env-example .env
# Here you must specify your API_ID and API_HASH, the rest is taken by default
npm install jsdom

python main.py
```

You can also use arguments for quick start, for example:

```shell
~/Tapswap >>> python3 main.py --action (1/2)
# Or
~/Tapswap >>> python3 main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

# Termux manual installation

```
> pkg update && pkg upgrade -y
> pkg install python nodejs rust git -y
> git clone https://github.com/Hunga9k50doker/Tapswap.git
> cd Tapswap
> npm install jsdom --no-bin-links
> pip install -r requirements.txt
> python main.py
```

You can also use arguments for quick start, for example:

```termux
~/Tapswap > python main.py --action (1/2)
# Or
~/Tapswap > python main.py -a (1/2)

# 1 - Run clicker
# 2 - Creates a session
```

# Get chq and chr

**Untill i upload tool for auto get this data you need to get it manually by yourself.**

Before start you need to install this [extension](https://chromewebstore.google.com/detail/bypass-telegram-web/jheaicmfgoefbdmadnhigbpdldafaokb)
Then run the bot for the first time it will create profiles for your query or sessions. Open file [profiles.json](https://github.com/Hunga9k50doker/Tapswap/blob/main/profiles.json) to edit chq and chr

After you run the bot for the first time profiles.json file should look like this:
![image](https://github.com/user-attachments/assets/b297499a-849c-4aec-99dd-e4c83d1947b6)

# Get chq

- Open tapswap in telegram web and press Ctrl + Shift + i to open dev tool
- Then turn this on like in this image
  ![image](https://github.com/user-attachments/assets/a9af7308-1add-42dd-9f47-e0d72984e970)
- Find something named "login" like this and click on it
  ![image](https://github.com/user-attachments/assets/3bdbe872-065e-49b6-a2ef-5ef70534c23a)
- Click on response tab and copy chq value then put it in profiles.json:
  ![image](https://github.com/user-attachments/assets/3b5c0cce-e49f-4af4-bc87-13e64e436f5c)
  Put chq value between ""
  ![image](https://github.com/user-attachments/assets/8e1c51af-3596-4617-9f63-ca19fb5bb747)

# Get chr

- Find something named "challenge" like this and click on it
  ![image](https://github.com/user-attachments/assets/d15d1f08-c85f-412a-8205-72027cf60271)
- Click on payload tab and copy chr value then put it in profiles.json:
  ![image](https://github.com/user-attachments/assets/56d66d3f-118c-41f0-acc9-1dcebdd773e8)
  replace 123 by chr value you copied
  ![image](https://github.com/user-attachments/assets/20d17b8f-fce1-4bc7-895e-3ce5980d9679)

Now you can start the bot again, Enjoy!
