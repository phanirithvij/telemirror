# import asyncio

# from telethon.sessions import StringSession
# from telethon.sync import TelegramClient
# from telethon.tl.types import MessageService, PeerChannel

# from app.settings import (API_HASH, API_ID, SESSION_STRING)

# client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# async def do_full_copy():
#     SOURCE_CHAT = await client.get_entity(PeerChannel( -1001393493900))
#     x = 0
#     async for message in client.iter_messages(SOURCE_CHAT, reverse=False):
#         # skip if service messages
#         if isinstance(message, MessageService):
#             continue
#         print(message)

# async def get_owned_channels():
#     # https://stackoverflow.com/a/62849271/8608146
#     async for dialog in client.iter_dialogs():
#         if dialog.is_channel and dialog.entity.admin_rights is not None:
#             print(dialog.name, dialog.id)

# async def main():
#     try:
#         await client.connect()
#     except OSError:
#         print('Failed to connect')
#     await get_owned_channels()
#     await do_full_copy()
#     await client.disconnect()


# if __name__ == "__main__":
#     loop = asyncio.get_event_loop()
#     loop.run_until_complete(main())
