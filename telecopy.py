"""
Make full copy of telegram channel
"""
import asyncio
import logging
import pickle
import time
import traceback
from pathlib import Path

from telethon.errors.rpcerrorlist import MediaEmptyError
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.custom.button import Button
from telethon.tl.types import MessageService, PeerChannel
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterPhotos, InputMessagesFilterEmpty, InputMessagesFilterPhotoVideo, InputMessagesFilterDocument

from app.settings import (API_HASH, API_ID, BOT_TOKEN, CHANNEL_MAPPING, CHATS,
                          LIMIT_TO_WAIT, LOG_LEVEL, SESSION_STRING)

logging.basicConfig(level=logging.getLevelName(LOG_LEVEL))

print(CHATS, CHANNEL_MAPPING)

DistantLands = -1001223189644
DistantLandsBackup = -1001235606765
Currenttestchannel = -1001393493900  # (telemirror)

# user account
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# TODO separate two bots
# bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


# @bot.on(events.NewMessage(pattern='/start'))
# async def start(event):
#     """Send a message when the command /start is issued."""
#     await event.respond('Hi!')
#     raise events.StopPropagation


# @bot.on(events.NewMessage)
# async def echo(event: events.NewMessage.Event):
#     """Echo the user message."""
#     try:
#         pass
#         # ignore for now
#         # print("bot new msg", event.message)
#         # await event.respond(event.message)
#     except Exception as e:
#         print(e)


async def get_channels(owned=False):
    # https://stackoverflow.com/a/62849271/8608146
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            if not owned:
                print(dialog.name, dialog.id)
            if owned and dialog.entity.admin_rights is not None:
                print(dialog.name, dialog.id)


def write_last_message(message):
    with open("lastf.bin", "wb+") as lastf:
        pickle.dump(message.id, lastf)


def read_last_message():
    if not Path("lastf.bin").exists():
        # default for min_id is 0 but not None
        return 0
    with open("lastf.bin", "rb") as lastf:
        return pickle.load(lastf)


async def do_full_copy():
    SRC_CHANNEL = await client.get_entity(PeerChannel(CHATS[0]))
    # BOT_CHAT = await client.get_entity("https://t.me/telemirror_test_bot")
    DEST_CHANNEL = await bot.get_entity(PeerChannel(list(CHANNEL_MAPPING.values())[0][0]))
    CLIENT_DEST_CHANNEL = await client.get_entity(PeerChannel(list(CHANNEL_MAPPING.values())[0][0]))
    amount_sent = 0
    albums = {}
    sent = {}
    last_album = None
    min_id = read_last_message()

    # https://stackoverflow.com/a/47967446/8608146
    # photos = await client(SearchRequest(
    #     SRC_CHANNEL,  # peer
    #     '',  # q
    #     # InputMessagesFilterEmpty(),  # filter
    #     # InputMessagesFilterPhotos(),  #   filter
    #     InputMessagesFilterDocument(),  #   filter
    #     # InputMessagesFilterPhotoVideo(),  # filter
    #     None,  # min_date
    #     None,  # max_date
    #     0,  # offset_id
    #     0,  # add_offset
    #     0,  # limit
    #     0,  # max_id
    #     0,  # min_id
    #     0  # hash
    # ))
    # print(photos.count)

    # stats = await client.get_stats(SRC_CHANNEL)
    # print(stats)

    async for message in client.iter_messages(SRC_CHANNEL, reverse=True, min_id=min_id):
        # skip if service messages
        if isinstance(message, MessageService):
            continue
        print(message.id, min_id)
        try:
            if message.restriction_reason is not None:
                print(message.restriction_reason, message.media)
                # continue
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
            if last_album is not None and last_album != message.grouped_id:
                # our group_id is either a new album or it is None
                # no matter which case, as we are progressing sequentially
                # we are finished with this album i.e. got the whole album in memory
                # https://stackoverflow.com/a/64114715/8608146
                # send the album
                # print(albums[last_album])
                if last_album in sent:
                    # TODO duplicate?
                    # print("Duplicate album?", last_album, message.grouped_id)
                    sent_message = await try_bot_send(DEST_CHANNEL, CLIENT_DEST_CHANNEL, message, buttons)
                    continue
                # no need to sort if reverse = True
                albums[last_album] = sorted(
                    albums[last_album], key=lambda a: a.id)
                captions = list(
                    map(lambda a: str(a.message), albums[last_album]))
                # the next line was useful when debugging for send_file with album
                # captions[-1] += "\nset via `client.send_file`"
                # https://stackoverflow.com/a/67411533/8608146
                sent_message = await client.send_file(
                    CLIENT_DEST_CHANNEL,
                    # event.messages is a List - meaning we're sending an album
                    file=albums[last_album],
                    # get the caption message from the album
                    caption=captions,
                    silent=True,
                )
                write_last_message(albums[last_album][-1])
                # TODO pickle this? with an OrderedDict
                # then at the beginning if exists in pickled dict continue
                sent[last_album] = True
                del albums[last_album]
                print("Sent album", last_album)
                # print(sent_message.to_dict())

            print("Need to send message", (message.message[:75] + '...') if len(
                message.message) > 75 else message.message)
            if message.grouped_id is not None:
                # if album bot can't handle it
                # we have it in memory so skip for now
                last_album = message.grouped_id
                continue
                # sent_message = await client.send_message(BOT_CHAT, message)
            else:
                sent_message = await try_bot_send(DEST_CHANNEL, CLIENT_DEST_CHANNEL, message, buttons)
                # send the message to target channel with buttons
                # sent_message = await bot.send_message(DEST_CHANNEL, message, buttons=buttons, silent=True)
                # https://stackoverflow.com/a/2872519/8608146
                # print(sent_message.to_dict())
        except Exception:
            print(type(message), message.media)
            traceback.print_exc()
            # pass
        finally:
            amount_sent += 1
            if amount_sent >= LIMIT_TO_WAIT:
                amount_sent = 0
                time.sleep(1)
                # await client.disconnect()
                # break

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


async def try_bot_send(DEST_CHANNEL, CLIENT_DEST_CHANNEL, message, buttons=None):
    sent_message = None
    try:
        sent_message = await bot.send_message(DEST_CHANNEL, message, silent=True, buttons=buttons)
    except MediaEmptyError as e:
        # https://docs.pyrogram.org/faq#can-i-use-the-same-file-id-across-different-accounts
        # will occur because of bot not having access to the file_id
        print(e, message.media)
        sent_message = await client.send_message(CLIENT_DEST_CHANNEL, message, silent=True)
    except Exception as e:
        print("general error", e, type(e))
    write_last_message(message)
    return sent_message

if __name__ == "__main__":
    # executor = ProcessPoolExecutor(2)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # boo = loop.run_in_executor(executor, main)
    # baa = loop.run_in_executor(executor, bot.run_until_disconnected)

    # loop.run_forever()
