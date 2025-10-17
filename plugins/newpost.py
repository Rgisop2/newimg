import asyncio
import base64
from pyrogram import Client as Bot, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.enums import ParseMode
from pyrogram.errors import UserNotParticipant, FloodWait, ChatAdminRequired, RPCError
from pyrogram.errors import InviteHashExpired, InviteRequestSent
from database.database import (
    save_channel,
    delete_channel,
    get_channels,
    save_channel_photo,
    save_encoded_link,
    save_encoded_link2,
)
from config import ADMINS, OWNER_ID
from helper_func import encode
from datetime import datetime, timedelta


# Revoke invite link after 10 minutes
async def revoke_invite_after_10_minutes(client: Bot, channel_id: int, link: str, is_request: bool = False):
    await asyncio.sleep(600)  # 10 minutes
    try:
        if is_request:
            await client.revoke_chat_invite_link(channel_id, link)
            print(f"Join request link revoked for channel {channel_id}")
        else:
            await client.revoke_chat_invite_link(channel_id, link)
            print(f"Invite link revoked for channel {channel_id}")
    except Exception as e:
        print(f"Failed to revoke invite for {channel_id}: {e}")

##----------------------------------------------------------------------------------------------------        
##----------------------------------------------------------------------------------------------------

@Bot.on_message(filters.command('setchannel') & filters.private & filters.user([OWNER_ID, *ADMINS]))
async def set_channel(client: Bot, message: Message):
    try:
        channel_id = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply("Channel id check karo chacha. Example: /setchannel <channel_id> [photo_link]")

    photo_link = None
    if len(message.command) >= 3:
        photo_link = message.command[2]

    try:
        chat = await client.get_chat(channel_id)

        if chat.permissions and not (chat.permissions.can_post_messages or chat.permissions.can_edit_messages):
            return await message.reply(f"Me hoon isme-{chat.title} lekin permission tumhare chacha denge.")

        await save_channel(channel_id)

        if photo_link:
            await save_channel_photo(channel_id, photo_link)

        username = client.username
        if not username:
            me = await client.get_me()
            username = me.username
        
        # Generate normal link
        base64_invite = await save_encoded_link(channel_id)
        normal_link = f"https://t.me/{username}?start={base64_invite}"
        
        # Generate request link
        base64_request = await encode(str(channel_id))
        await save_encoded_link2(channel_id, base64_request)
        request_link = f"https://t.me/{username}?start=req_{base64_request}"
        
        response = f"✅ Channel - ({chat.title}) ({channel_id}) add ho gya ha maharaj.\n"
        response += f"• Normal Link: <code>{normal_link}</code>\n"
        response += f"• Request Link: <code>{request_link}</code>"
        
        if photo_link:
            response += "\n🖼️ Custom photo set."
        
        return await message.reply(response, parse_mode=ParseMode.HTML)

    except UserNotParticipant:
        return await message.reply("I am not a member of this channel. Please add me and try again.")
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await set_channel(client, message)
    except RPCError as e:
        return await message.reply(f"RPC Error: {str(e)}")
    except Exception as e:
        return await message.reply(f"Unexpected Error: {str(e)}")

##----------------------------------------------------------------------------------------------------        
##----------------------------------------------------------------------------------------------------

@Bot.on_message(filters.command('delchannel') & filters.private & filters.user([OWNER_ID, *ADMINS]))
async def del_channel(client: Bot, message: Message):
    try:
        channel_id = int(message.command[1])
    except (IndexError, ValueError):
        return await message.reply("Channel id galat ha mere aaka.")
    
    await delete_channel(channel_id)
    return await message.reply(f"❌ Channel {channel_id} hata dia gaya ha maharaj.")

##----------------------------------------------------------------------------------------------------        
##----------------------------------------------------------------------------------------------------

@Bot.on_message(filters.command('channelpost') & filters.private & filters.user([OWNER_ID, *ADMINS]))
async def channel_post(client: Bot, message: Message):
    channels = await get_channels()
    if not channels:
        return await message.reply("No channels available. Use /setchannel first.")

    buttons = []
    username = client.username
    if not username:
        me = await client.get_me()
        username = me.username
    for channel_id in channels:
        try:
            base64_invite = await save_encoded_link(channel_id)
            button_link = f"https://t.me/{username}?start={base64_invite}"
            chat = await client.get_chat(channel_id)
            buttons.append(InlineKeyboardButton(chat.title, url=button_link))
        except Exception as e:
            print(f"Error for {channel_id}: {e}")

    if buttons:
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        await message.reply("📢 Select a channel to post:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply("No channels available.")

#-------------------------------------------------------------------------------------------------------------------------        
#------------------------------------------------------------------------------------------------------------------------- 

@Bot.on_message(filters.command('reqpost') & filters.private & filters.user([OWNER_ID, *ADMINS]))
async def req_post(client: Bot, message: Message):
    channels = await get_channels()
    if not channels:
        return await message.reply("No channels available. Use /setchannel first.")
    buttons = []
    username = client.username
    if not username:
        me = await client.get_me()
        username = me.username
    for channel_id in channels:
        try:
            base64_request = await encode(str(channel_id))
            await save_encoded_link2(channel_id, base64_request)
            button_link = f"https://t.me/{username}?start=req_{base64_request}"
            chat = await client.get_chat(channel_id)
            buttons.append(InlineKeyboardButton(chat.title, url=button_link))
        except Exception as e:
            print(f"Error generating request link for {channel_id}: {e}")
            continue
    if buttons:
        keyboard = [buttons[i:i+2] for i in range(0, len(buttons), 2)]
        await message.reply("📢 Select a channel to request access:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await message.reply("No channels available.")
