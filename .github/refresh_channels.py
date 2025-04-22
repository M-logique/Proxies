import json
from telethon import TelegramClient
from datetime import datetime, timedelta
import aiohttp
import asyncio
import re
from os import environ
from telethon.sessions import StringSession

API_ID = int(environ.get("API_ID"))
API_HASH = environ.get("API_HASH")
SESSION = environ.get("SESSION")

CHATS = [
    -1001796213998,
    -1002080200970,
    -1001222417086
]


async def main():
    configs = []
    sub_urls = []
    async with TelegramClient(StringSession(SESSION), API_ID, API_HASH) as client:
        scraped = await load_previous_channels()
        for chat in CHATS:
            print('getting messages from group', chat) 
            group = await client.get_entity(chat)
            offset_date_filter = datetime.now() - timedelta(days=1)

            async for message in client.iter_messages(group, limit=3000, offset_date=offset_date_filter):
                if not message.text:
                    continue

                if re.search(r'https?://\S+|www\.\S+', message.text):
                    url = re.findall(r'https?://\S+|www\.\S+', message.text)
                    sub_urls.extend(url)

                if not re.search(r'\b(vless|vmess|ss|trojan|hystria|wg)\b', message.text, re.IGNORECASE):
                    continue

                configs.extend(re.findall(r"(?:vless|vmess|ss|trojan)://[^\s#]+(?:#[^\s]*)?", message.text))

                if message.forward and hasattr(message.forward, 'chat') and hasattr(message.forward.chat, 'username') and message.forward.chat.broadcast:
                    scraped.add(message.forward.chat.username)
                if message.text:
                    matches = re.findall(r'(?:t\.me/|@)(\w+)', message.text)
                    for match in matches:
                        scraped.add(match)

            print(f'found {len(scraped)} channels')
            configs = list(set(configs))



            scraped = {channel.lower() for channel in scraped if channel is not None}

            verified_channels = set()
            
            async with aiohttp.ClientSession() as session:
                await asyncio.gather(*(check_channel(channel, session, verified_channels) for channel in scraped))

            print(f'found {len(verified_channels)} working channels')

            with open("data/tgchannels.json", "w") as fp:
                data = {}
                for k in verified_channels:
                    data[k] = {
                        "limit": 100
                    }
                
                json.dump(data, fp, indent=4)
            
            print("Saving %d configs" % len(configs))
            print("Saving %d sub urls" % len(sub_urls))

            with open("additional_configs.txt", "w") as ac_fp, open("additional_urls.txt", "w") as au_fp:
                ac_fp.write("\n".join(configs))
                au_fp.write("\n".join(sub_urls))
            


async def check_channel(channel, session, verified_channels):
    try:
        url = f"https://t.me/s/{channel}"
        async with session.get(url, allow_redirects=False) as response:
            if response.status == 200:
                verified_channels.add(channel)
                print('found the channel', channel)
            else:
                print('invalid channel', channel)
    except Exception as e:
        print(f'error checking channel {channel}: {e}')

async def load_previous_channels():
    with open("data/tgchannels.json", "r") as fp:
        data = json.load(fp)

    channels = {i.lower() for i in data.keys()}
    
    async with aiohttp.ClientSession() as session:
        async with session.get("https://raw.githubusercontent.com/M-logique/V2ray-Channel-Submit/refs/heads/main/channels.txt") as resp:
            text = await resp.text()

            for channel_id in text.splitlines():
                channels.add(channel_id.lower())

    return set(data.keys())

if __name__ == "__main__":
    start_time = datetime.now()
    asyncio.run(main())
    end_time = datetime.now()
    print(f"Execution time: {end_time - start_time}")
