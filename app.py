"""
MIT License

Copyright (c) 2021 Janindu Malshan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os
import glob
import logging
import asyncio
from pytgcalls import StreamType
from pytube import YouTube
from youtube_search import YoutubeSearch
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import Update
from pytgcalls.types import AudioPiped, AudioVideoPiped
from pytgcalls.types import (
    HighQualityAudio,
    HighQualityVideo,
    LowQualityVideo,
    MediumQualityVideo
)
from pytgcalls.types.stream import StreamAudioEnded, StreamVideoEnded
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helpers.queues import QUEUE, add_to_queue, get_queue, clear_queue, pop_an_item

bot = Client(
    "Music Stream Bot",
    bot_token = os.environ["BOT_TOKEN"],
    api_id = int(os.environ["API_ID"]),
    api_hash = os.environ["API_HASH"]
)

client = Client(os.environ["SESSION_NAME"], int(os.environ["API_ID"]), os.environ["API_HASH"])

app = PyTgCalls(client)

OWNER_ID = int(os.environ["OWNER_ID"])

START_TEXT = """
Hi <b>{}</b> 👋

I can play music & stream videos in Telegram group voice chats. 

<i>Only my owner can operate me. Make your own bot from the source code.</i>
"""

START_BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("📨 Support", url="https://t.me/JaguarBots"),
            InlineKeyboardButton("📚 Source Code", url="https://github.com/ImJanindu/47MusicPlayerBot")
        ]
    ]
)

BUTTONS = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("⏸", callback_data="pause"),
            InlineKeyboardButton("▶️", callback_data="resume"),
            InlineKeyboardButton("⏹", callback_data="stop"),
            InlineKeyboardButton("🔇", callback_data="mute"),
            InlineKeyboardButton("🔊", callback_data="unmute")
        ],
        [
            InlineKeyboardButton("🗑 Close Menu", callback_data="close")
        ]
    ]
)

async def skip_current_song(chat_id):
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        if len(chat_queue) == 1:
            await app.leave_group_call(chat_id)
            clear_queue(chat_id)
            return 1
        else:
            title = chat_queue[1][0]
            duration = chat_queue[1][1]
            link = chat_queue[1][2]
            playlink = chat_queue[1][3]
            type = chat_queue[1][4]
            Q = chat_queue[1][5]
            if type == "Audio":
                await call_py.change_stream(
                    chat_id,
                    AudioPiped(
                        playlink,
                    ),
                )
            elif type == "Video":
                if Q == "high":
                    hm = HighQualityVideo()
                elif Q == "mid":
                    hm = MediumQualityVideo()
                elif Q == "low":
                    hm = LowQualityVideo()
                else:
                    hm = MediumQualityVideo()
                await app.change_stream(
                    chat_id, AudioVideoPiped(playlink, HighQualityAudio(), hm)
                )
            pop_an_item(chat_id)
            return [title, link, type]
    else:
        return 0


async def skip_item(chat_id, lol):
    if chat_id in QUEUE:
        chat_queue = get_queue(chat_id)
        try:
            x = int(lol)
            title = chat_queue[x][0]
            chat_queue.pop(x)
            return title
        except Exception as e:
            print(e)
            return 0
    else:
        return 0


@app.on_stream_end()
async def on_end_handler(_, update: Update):
    if isinstance(update, StreamAudioEnded):
        chat_id = update.chat_id
        await skip_current_song(chat_id)


@app.on_stream_end()
async def on_end_handler(_, update: Update):
    if isinstance(update, StreamVideoEnded):
        chat_id = update.chat_id
        await skip_current_song(chat_id)


@app.on_closed_voice_chat()
async def close_handler(client: PyTgCalls, chat_id: int):
    if chat_id in QUEUE:
        clear_queue(chat_id)
        

async def yt_video(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "bv*[height<=720]+ba/b[height<=720] / wv*+ba/w",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()
    

async def yt_audio(link):
    proc = await asyncio.create_subprocess_exec(
        "yt-dlp",
        "-g",
        "-f",
        "bestaudio",
        f"{link}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        return 1, stdout.decode().split("\n")[0]
    else:
        return 0, stderr.decode()


@bot.on_callback_query()
async def callbacks(_, cq: CallbackQuery): 
    if cq.from_user.id != OWNER_ID:
        return await cq.answer("You aren't the owner of me.")   
    chat_id = cq.message.chat.id
    data = cq.data
    if data == "close":
        return await cq.message.delete()
    if not chat_id in QUEUE:
        return await cq.answer("Nothing is playing.")

    if data == "pause":
        try:
            await app.pause_stream(chat_id)
            await cq.answer("Paused streaming.")
        except:
            await cq.answer("Nothing is playing.")
      
    elif data == "resume":
        try:
            await app.resume_stream(chat_id)
            await cq.answer("Resumed streaming.")
        except:
            await cq.answer("Nothing is playing.")   

    elif data == "stop":
        await app.leave_group_call(chat_id)
        clear_queue(chat_id)
        await cq.answer("Stopped streaming.")  

    elif data == "mute":
        try:
            await app.mute_stream(chat_id)
            await cq.answer("Muted streaming.")
        except:
            await cq.answer("Nothing is playing.")
            
    elif data == "unmute":
        try:
            await app.unmute_stream(chat_id)
            await cq.answer("Unmuted streaming.")
        except:
            await cq.answer("Nothing is playing.")
            

@bot.on_message(filters.command("start") & filters.private)
async def start_private(_, message):
    msg = START_TEXT.format(message.from_user.mention)
    await message.reply_text(text = msg,
                             reply_markup = START_BUTTONS)
    

@bot.on_message(filters.command("start") & filters.group)
async def start_group(_, message):
    await message.reply_text("🎧 <i>Music player is running.</i>")
    
    
@bot.on_message(filters.command(["play", "video"]) & filters.group)
async def video_play(_, message):
    await message.delete()
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    state = message.command[0].lower()
    try:
        query = message.text.split(None, 1)[1]
    except:
        return await message.reply_text(f"<b>Usage:</b> <code>/{state} [query]</code>")
    chat_id = message.chat.id
    m = await message.reply_text("🔄 Processing...")
    if state == "play":
        damn = AudioPiped
        ded = yt_audio
        emj = "🎵"
        doom = "Audio"
    elif state == "video":
        damn = AudioVideoPiped
        ded = yt_video
        emj = "🎬"
        doom = "Video"
    if "low" in query:
        Q = "low"
    elif "mid" in query:
        Q = "mid"
    elif "high" in query:
        Q = "high"
    else:
        Q = "0"
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        link = f"https://youtube.com{results[0]['url_suffix']}"
        thumb = results[0]["thumbnails"][0]
        duration = results[0]["duration"]
        yt = YouTube(link)
        cap = f"{emj} <b>Playing:</b> [{yt.title}]({link}) \n\n⏳ <b>Duration:</b> {duration}"
        ice, playlink = await ded(link)
        if ice == "0":
            return await m.edit("❗️YTDL ERROR !!!")             
    except Exception as e:
        return await m.edit(str(e))
    
    try:
        if chat_id in QUEUE:
            position = add_to_queue(chat_id, yt.title, duration, link, playlink, doom, Q)
            caps = f"{emj} <b>Playing:</b> [{yt.title}]({link}) \n\n⏳ <b>Duration:</b> {duration} \n#️⃣ <b>Queued at position:</b> {position}"
            await message.reply_photo(thumb, caption=caps)
            await m.delete()
        else:            
            await app.join_group_call(
                chat_id,
                damn(playlink),
                stream_type=StreamType().pulse_stream
            )
            add_to_queue(chat_id, yt.title, duration, link, playlink, doom, Q)
            await message.reply_photo(thumb, caption=cap, reply_markup=BUTTONS)
            await m.delete()
    except Exception as e:
        return await m.edit(str(e))
    
    
"""@bot.on_message(filters.command(["saudio", "svideo"]) & filters.group)
async def stream_func(_, message):
    await message.delete()
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    state = message.command[0].lower()
    try:
        link = message.text.split(None, 1)[1]
    except:
        return await message.reply_text(f"<b>Usage:</b> <code>/{state} [link]</code>")
    chat_id = message.chat.id
    
    if state == "saudio":
        damn = AudioPiped
        emj = "🎵"
    elif state == "svideo":
        damn = AudioVideoPiped
        emj = "🎬"
    m = await message.reply_text("🔄 Processing...")
    try:
        if chat_id in QUEUE:
            position = add_to_queue(chat_id, yt.title, duration, link, playlink)
            caps = f"{emj} <b>Playing:</b> [{yt.title}]({link}) \n\n⏳ <b>Duration:</b> {duration} \n#️⃣ <b>Queued at position:</b> {position}"
            await message.reply_photo(thumb, caption=caps)
            await m.delete()
        else:    
            await app.join_group_call(
                chat_id,
                damn(link),
                stream_type=StreamType().pulse_stream)
            add_to_queue(chat_id, yt.title, duration, link, playlink)
            await m.edit(f"{emj} Started streaming...")
    except Exception as e:
        return await m.edit(str(e))"""


@bot.on_message(filters.command("skip") & filters.group)
async def skip(_, message):
    await message.delete()
    chat_id = message.chat.id
    if len(m.command) < 2:
        op = await skip_current_song(chat_id)
        if op == 0:
            await message.reply_text("❗️Nothing in the queue to skip.")
        elif op == 1:
            await message.reply_text("❗️Empty queue.")
        else:
            await message.reply_text(
                f"⏭ <b>Skipped \n\n🎧 Now playing:</b> [{op[0]}]({op[1]}) | `{op[2]}`",
                disable_web_page_preview=True,
            )
    else:
        skip = message.text.split(None, 1)[1]
        out = "🗑 <b>Removed the following songs from the queue:</b> \n\n"
        if chat_id in QUEUE:
            items = [int(x) for x in skip.split(" ") if x.isdigit()]
            items.sort(reverse=True)
            for x in items:
                if x == 0:
                    pass
                else:
                    hm = await skip_item(chat_id, x)
                    if hm == 0:
                        pass
                    else:
                        out = out + f"<b>#️⃣ {x}</b> - {hm}"
            await message.reply_text(out)
    

@bot.on_message(filters.command("stop") & filters.group)
async def end(_, message):
    await message.delete()
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    chat_id = message.chat.id
    if chat_id in QUEUE:
        await app.leave_group_call(chat_id)
        clear_queue(chat_id)
        await message.reply_text("⏹ Stopped streaming.")
    else:
        await message.reply_text("❗Nothing is playing.")
        

@bot.on_message(filters.command("pause") & filters.group)
async def pause(_, message):
    await message.delete()
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.pause_stream(chat_id)
            await message.reply_text("⏸ Paused streaming.")
        except:
            await message.reply_text("❗Nothing is playing.")
    else:
        await message.reply_text("❗Nothing is playing.")
        
        
@bot.on_message(filters.command("resume") & filters.group)
async def resume(_, message):
    await message.delete()
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.resume_stream(chat_id)
            await message.reply_text("⏸ Resumed streaming.")
        except:
            await message.reply_text("❗Nothing is playing.")
    else:
        await message.reply_text("❗Nothing is playing.")
        
        
@bot.on_message(filters.command("mute") & filters.group)
async def mute(_, message):
    await message.delete()
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.mute_stream(chat_id)
            await message.reply_text("🔇 Muted streaming.")
        except:
            await message.reply_text("❗Nothing is playing.")
    else:
        await message.reply_text("❗Nothing is playing.")
        
        
@bot.on_message(filters.command("unmute") & filters.group)
async def unmute(_, message):
    await message.delete()
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    chat_id = message.chat.id
    if chat_id in QUEUE:
        try:
            await app.unmute_stream(chat_id)
            await message.reply_text("🔊 Unmuted streaming.")
        except:
            await message.reply_text("❗Nothing is playing.")
    else:
        await message.reply_text("❗Nothing is playing.")
        
        
@bot.on_message(filters.command("restart"))
async def restart(_, message):
    user_id = message.from_user.id
    if user_id != OWNER_ID:
        return
    await message.reply_text("🛠 <i>Restarting Music Player...</i>")
    os.system(f"kill -9 {os.getpid()} && python3 app.py")
            

app.start()
bot.run()
idle()
