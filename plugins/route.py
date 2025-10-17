from aiohttp import web
from database.database import save_channel, delete_channel, get_channels, save_channel_photo
from pyrogram import filters, Client
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant, FloodWait, RPCError
import asyncio

from config import OWNER_ID, ADMINS

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("CodeXBotz")

DISABLE_SETCHANNEL_HANDLER = True

@Client.on_message(filters.command('setchannel') & filters.private & filters.user([OWNER_ID, *ADMINS]))
async def set_channel(client: Client, message: Message):
    if DISABLE_SETCHANNEL_HANDLER:
        return  # handled in plugins/newpost.py
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
            return await message.reply(f"✅ Channel-({chat.title})-({channel_id}) add ho gya ha maharaj.\n🖼️ Custom photo set.")
        return await message.reply(f"✅ Channel-({chat.title})-({channel_id}) add ho gya ha maharaj.")
    
    except UserNotParticipant:
        return await message.reply("I am not a member of this channel. Please add me and try again.")
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await set_channel(client, message)
    except RPCError as e:
        return await message.reply(f"RPC Error: {str(e)}")
    except Exception as e:
        return await message.reply(f"Unexpected Error: {str(e)}")
