"""
Telgram forward removal for all messages in a thread
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

from app.settings import (API_HASH, API_ID, BOT_TOKEN, CHANNEL_MAPPING, CHATS,
                          LIMIT_TO_WAIT, LOG_LEVEL, SESSION_STRING)

logging.basicConfig(level=logging.getLevelName(LOG_LEVEL))

print(CHATS, CHANNEL_MAPPING)

DISTANT_LANDS = -1001223189644
DISTANT_LANDS_BACKUP = -1001235606765
CURRENT_TEST_CHANNEL = -1001393493900  # (telemirror)
SAVED_MESSAGES_EXTREME = -1001179463665
GAUTHAMS_LEECH = -1001463024136

# user account
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# TODO separate two bots
# bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


async def get_channels(owned=False):
    # https://stackoverflow.com/a/62849271/8608146
    async for dialog in client.iter_dialogs():
        if dialog.is_channel:
            if not owned:
                print(dialog.name, dialog.id)
            if owned and dialog.entity.admin_rights is not None:
                print(dialog.name, dialog.id)


async def get_groups(owned=False):
    # https://stackoverflow.com/a/62849271/8608146
    async for dialog in client.iter_dialogs():
        if dialog.is_group:
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
    src_channel = await client.get_entity("https://t.me/c/1463024136")
    # BOT_CHAT = await client.get_entity("https://t.me/telemirror_test_bot")
    dest_channel = await bot.get_entity(PeerChannel(list(CHANNEL_MAPPING.values())[0][0]))
    client_dest_channel = await client.get_entity(PeerChannel(list(CHANNEL_MAPPING.values())[0][0]))
    amount_sent = 0
    albums = {}
    sent = {}
    last_album = None
    min_id = read_last_message()

    thread_url = "https://t.me/c/1463024136/26211?thread=25347"
    reply_to = thread_url.split("=")[-1]
    print(int(reply_to))

    async for message in client.iter_messages(src_channel, reverse=True, min_id=min_id):
        # skip if service messages
        if isinstance(message, MessageService):
            continue
        print(message.id, min_id)
        continue
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
                src_channel.id, message.id)
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
                    sent_message = await try_bot_send(dest_channel, client_dest_channel, message, buttons)
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
                    client_dest_channel,
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
                # send the message to target channel with buttons
                sent_message = await try_bot_send(dest_channel, client_dest_channel, message, buttons)
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

    print("Done")


async def main():
    try:
        await client.connect()
    except OSError:
        print('Failed to connect')
    # await get_groups()
    # await get_groups(True)
    # await get_channels()
    # await get_channels(True)
    # exit(0)
    await do_full_copy()
    await bot.run_until_disconnected()
    await client.disconnect()
    await bot.disconnect()


async def try_bot_send(dest_channel, client_dest_channel, message, buttons=None):
    sent_message = None
    try:
        sent_message = await bot.send_message(dest_channel, message, silent=True, buttons=buttons)
    except MediaEmptyError as e:
        # https://stackoverflow.com/q/66178276/8608146
        # https://docs.pyrogram.org/faq#can-i-use-the-same-file-id-across-different-accounts
        # will occur because of bot not having access to the file_id
        print(e, message.media)
        sent_message = await client.send_message(client_dest_channel, message, silent=True)
    except Exception as e:
        print("general error", e, type(e))
    write_last_message(message)
    return sent_message

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
