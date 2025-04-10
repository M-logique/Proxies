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
    async with TelegramClient(StringSession(SESSION), API_ID, API_HASH) as client:
        scraped = load_previous_channels()
        for chat in CHATS:
            print('getting messages from group', chat) 
            group = await client.get_entity(chat)
            offset_date_filter = datetime.now() - timedelta(days=1)

            async for message in client.iter_messages(group, limit=3000, offset_date=offset_date_filter):
                if not message.text or re.search(r'\b(vless|vmess|ss|trojan|hystria|wg)\b', message.text, re.IGNORECASE):
                    continue
                if message.forward and hasattr(message.forward, 'chat') and hasattr(message.forward.chat, 'username') and message.forward.chat.broadcast:
                    scraped.add(message.forward.chat.username)
                if message.text:
                    matches = re.findall(r'(?:t\.me/|@)(\w+)', message.text)
                    for match in matches:
                        scraped.add(match)

            print(f'found {len(scraped)} channels')

            scraped = {channel.lower() for channel in scraped}

            verified_channels = set()
            
            async with aiohttp.ClientSession() as session:
                chunk_size = 100
                channel_chunks = [list(scraped)[i:i + chunk_size] for i in range(0, len(scraped), chunk_size)]

                for chunk in channel_chunks:
                    await asyncio.gather(*(check_channel(channel, session, verified_channels) for channel in chunk))
                    await asyncio.sleep(2)

            print(f'found {len(verified_channels)} working channels')

            with open("data/tgchannels.json", "w") as fp:
                data = {}
                for k in verified_channels:
                    data[k] = 100
                
                json.dump(data, fp, indent=4)


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

def load_previous_channels():
    with open("data/tgchannels.json", "r") as fp:
        data = json.load(fp)

    return set(data.keys())

if __name__ == "__main__":
    start_time = datetime.now()
    asyncio.run(main())
    end_time = datetime.now()
    print(f"Execution time: {end_time - start_time}")
