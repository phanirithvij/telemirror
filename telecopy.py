"""
Make full copy of telegram channel
"""
import asyncio
import time
import traceback

from telethon.sessions import StringSession
from telethon.sync import TelegramClient, events
from telethon.tl.custom.button import Button
from telethon.tl.types import MessageService, PeerChannel

from app.settings import (API_HASH, API_ID, BOT_TOKEN, CHANNEL_MAPPING, CHATS,
                          LIMIT_TO_WAIT, SESSION_STRING)

print(CHATS, CHANNEL_MAPPING)

# -1001223189644 -> Distant Lands

# user account
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# TODO separate two bots
# bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Send a message when the command /start is issued."""
    await event.respond('Hi!')
    raise events.StopPropagation


@bot.on(events.NewMessage)
async def echo(event: events.NewMessage.Event):
    """Echo the user message."""
    try:
        print(event.message)
        await event.respond(event.message)
    except Exception as e:
        print(e)


async def get_channels(owned=False):
    # https://stackoverflow.com/a/62849271/8608146
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            if not owned:
                print(dialog.name, dialog.id)
            if owned and dialog.entity.admin_rights is not None:
                print(dialog.name, dialog.id)

async def do_full_copy():
    SRC_CHANNEL = await client.get_entity(PeerChannel(CHATS[0]))
    # TARGET_CHAT = await client.get_entity(PeerChannel(list(CHANNEL_MAPPING.values())[0][0]))
    BOT_CHAT = await client.get_entity("https://t.me/telemirror_test_bot")
    DEST_CHANNEL = await bot.get_entity(PeerChannel(list(CHANNEL_MAPPING.values())[0][0]))
    amount_sent = 0
    albums = {}
    last_album = None
    async for message in client.iter_messages(SRC_CHANNEL, reverse=False):
        # skip if service messages
        if isinstance(message, MessageService):
            continue
        # print(message.message)
        try:
            if message.grouped_id is not None:
                # https://github.com/LonamiWebs/Telethon/issues/1216#issuecomment-507026612
                if message.grouped_id in albums:
                    albums[message.grouped_id].append(message)
                else:
                    albums[message.grouped_id] = [message]

            # add a view origal_url button
            # https://stackoverflow.com/a/67406011/8608146
            origal_url = "https://t.me/c/{}/{}".format(
                SRC_CHANNEL.id, message.id)
            button = Button.url("view original", origal_url)
            buttons = None
            if message.buttons is not None:
                buttons = message.buttons
                # insert as first column
                buttons.insert(0, [button])
            else:
                buttons = button

            sent_message = None

            # print(last_album, message.grouped_id)
            if last_album != None and last_album != message.grouped_id:
                # our group_id is either a new album or it is None
                # no matter which case, as we are progressing sequentially
                # we are finished with this album i.e. got the whole album in memory
                # https://stackoverflow.com/a/64114715/8608146
                # send the album
                # print(albums[last_album])
                sent_message = await bot.send_message(
                    DEST_CHANNEL,
                    # event.messages is a List - meaning we're sending an album
                    file=albums[last_album],
                    # get the caption message from the album
                    message=albums[last_album][0].message,
                    silent=True,
                )
                # print(sent_message.to_dict())

            print(107)
            if message.grouped_id is not None:
                print(message.grouped_id)
                # if album bot can't handle it
                # we have it in memory so skip for now
                last_album = message.grouped_id
                continue
                # sent_message = await client.send_message(BOT_CHAT, message)
            else:
                # send the message to target channel with buttons
                sent_message = await bot.send_message(DEST_CHANNEL, message, buttons=buttons, silent=True)
                # print(sent_message.to_dict())
        except Exception as e:
            print(e)
            traceback.print_exc()
            # pass
        finally:
            amount_sent += 1
            if amount_sent >= LIMIT_TO_WAIT:
                amount_sent = 0
                time.sleep(1)
                await client.disconnect()
                break

    print("Done")


async def main():
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    # await get_channels()
    # await get_channels(True)
    await do_full_copy()
    await bot.run_until_disconnected()
    await client.disconnect()
    await bot.disconnect()


if __name__ == "__main__":
    # executor = ProcessPoolExecutor(2)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # boo = loop.run_in_executor(executor, main)
    # baa = loop.run_in_executor(executor, bot.run_until_disconnected)

    # loop.run_forever()
