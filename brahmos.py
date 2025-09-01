import telebot
from telebot import types
import time
import config
import requests
import threading
from utils import *
from chat_handler import handle_chat_message, handle_prompt_command
from image_handler import handle_image_command, handle_image_input
from tts_handler import handle_say_command, handle_tts_input
from callback_handler import *

# Initialize bot
bot = telebot.TeleBot(config.BOT_TOKEN)

# Global state tracking
chat_mode = set()
user_waiting_for_chat = set()
user_waiting_for_image = set()
user_waiting_for_tts = set()
user_database = set()
bot_start_time = time.time()

# Initialize usage tracker
usage_tracker = UsageTracker()

# Start message handler
@bot.message_handler(commands=['start'])
def start_command(message):
    """Enhanced start command with user registration"""
    user_id = message.from_user.id
    username = message.from_user.username or "Friend"
    first_name = message.from_user.first_name or "User"
    
    # Add user to database
    user_database.add(user_id)
    
    # Log interaction
    log_user_interaction(message.from_user, "/start", "DM" if message.chat.type == "private" else "Group")
    
    is_premium = is_premium_user(user_id)
    
    welcome_text = """🚀 Welcome to BrahMos AI!

Hey """ + first_name + """! I'm your advanced AI assistant powered by cutting-edge technology.

🤖 What I can do:
• 💬 Smart Conversations - Chat with advanced AI
• 🎨 Image Generation - Create stunning artwork
• 🎤 Text-to-Speech - Convert text to natural speech
• ⚡ Group Chat Support - Mention me anywhere!

📊 Your Status: """ + ("💎 Premium User - Unlimited Access!" if is_premium else "🆓 Free User - 100 daily generations") + """

🚀 Ready to explore cutting-edge AI technology together!

Powered by the latest in AI innovation."""

    # Simplified 2-row inline keyboard for start menu
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("❓ Help & Features", callback_data="help"),
        types.InlineKeyboardButton("ℹ️ My Info", callback_data="my_info")
    )
    keyboard.row(
        types.InlineKeyboardButton("👨‍💻 Developer", url=config.DEVELOPER_URL),
        types.InlineKeyboardButton("🌐 Community", url=config.Community_URL)
    )
    if not is_premium:
        keyboard.row(
            types.InlineKeyboardButton("💎 Upgrade to Premium", callback_data="upgrade_premium")
        )

    # Try to send with photo
    success = safe_send_photo_with_caption(bot, message.chat.id, "Brahmos.png", welcome_text, keyboard)
    if not success:
        bot.send_message(message.chat.id, welcome_text, reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def help_command(message):
    """Simplified help command with only core features"""
    user_id = message.from_user.id
    log_user_interaction(message.from_user, "/help", "DM" if message.chat.type == "private" else "Group")
    
    is_premium = is_premium_user(user_id)
    
    help_text = """🚀 BrahMos AI - Advanced Features

💬 Chat
• Smart conversations with memory
• Group chat with mentions support
• Context-aware responses
• Usage: `/chat` 

🎨 Image
• High-quality AI artwork
• Creative prompts enhancement
• Multiple style options
• usage: `/image`

🎤 TTS
• Natural voice synthesis
• Multiple voice options
• High-quality audio output
• Usage: `/say`

📊 Your Status: """ + ("💎 Premium User" if is_premium else "🆓 Free User") + """

Use buttons below to start chatting, generating images, or converting text to speech!

🚀 Powered by GPT-4 & BrahMos AI"""

    # Simplified keyboard with only core features
    keyboard = types.InlineKeyboardMarkup()
    keyboard.row(
        types.InlineKeyboardButton("💬 Quick Chat", callback_data="quick_chat"),
        types.InlineKeyboardButton("🎨 Generate Image", callback_data="quick_image"),
        types.InlineKeyboardButton("🎤 Text-to-Speech", callback_data="quick_tts")
    )
    keyboard.row(
        types.InlineKeyboardButton("🔙 Back to Menu", callback_data="back_to_start")
    )
    if not is_premium:
        keyboard.row(
            types.InlineKeyboardButton("💎 Upgrade to Premium", callback_data="upgrade_premium")
        )

    bot.send_message(message.chat.id, help_text, reply_markup=keyboard)

@bot.message_handler(commands=['chat'])
def chat_command(message):
    """Activate chat mode"""
    user_id = message.from_user.id
    log_user_interaction(message.from_user, "/chat", "DM" if message.chat.type == "private" else "Group")
    
    if message.chat.type != 'private':
        bot.reply_to(message, "💬 **Chat mode is only available in direct messages!**\n\nPlease start a private chat with me to use this feature.", parse_mode="Markdown")
        return
    
    chat_mode.add(user_id)
    user_waiting_for_chat.add(user_id)
    
    bot.reply_to(message, """💬 **Chat Mode Activated!**

I'm now ready for a conversation! Just type your message and I'll respond with intelligent answers.

✨ **Features:**
• Contextual conversations
• Memory of our chat
• Smart responses
• No command needed

**What would you like to talk about?**""", parse_mode="Markdown")

@bot.message_handler(commands=['image'])
def image_command(message):
    """Handle image generation command"""
    handle_image_command(bot, message, user_waiting_for_image, usage_tracker)

@bot.message_handler(commands=['say'])
def say_command(message):
    """Handle TTS command"""
    handle_say_command(bot, message, usage_tracker)

@bot.message_handler(commands=['prompt'])
def prompt_command(message):
    """Handle prompt enhancement command"""
    handle_prompt_command(bot, message)

@bot.message_handler(commands=['myinfo'])
def myinfo_command(message):
    """Show user information with usage stats"""
    user_id = message.from_user.id
    user = message.from_user
    log_user_interaction(user, "/myinfo", "DM" if message.chat.type == "private" else "Group")
    
    is_premium = is_premium_user(user_id)
    remaining_images = usage_tracker.get_remaining_images(user_id)
    remaining_tts = usage_tracker.get_remaining_tts(user_id)
    
    info_text = f"""ℹ️ **Your Account Information**

**👤 Profile:**
• Name: {user.first_name or 'Unknown'}
• Username: @{user.username or 'None'}
• User ID: `{user_id}`

**💎 Subscription:** {"Premium" if is_premium else "Free"}

**📊 Daily Usage:**
• Images: {"∞" if is_premium else f"{remaining_images}/100"} remaining
• TTS: {"∞" if is_premium else f"{remaining_tts}/100"} remaining

**⚡ Status:** {"Unlimited Access" if is_premium else "Limited Access"}

💡 **Need more?** {'You have unlimited access!' if is_premium else 'Consider upgrading to Premium!'}"""
    
    keyboard = types.InlineKeyboardMarkup()
    if not is_premium:
        keyboard.row(types.InlineKeyboardButton("💎 Upgrade to Premium", callback_data="upgrade_premium"))
    keyboard.row(types.InlineKeyboardButton("🔙 Back", callback_data="help"))
    
    bot.send_message(message.chat.id, info_text, reply_markup=keyboard, parse_mode="Markdown")

# Premium management commands (owners only)
@bot.message_handler(commands=['addpro'])
def add_premium_command(message):
    """Add user to premium (owners only)"""
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.reply_to(message, "❌ **Access Denied:** This command is for owners only.", parse_mode="Markdown")
        return
    
    try:
        # Get target user ID from command
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, """**Usage:** `/addpro [user_id]`

**Example:** `/addpro 123456789`""", parse_mode="Markdown")
            return
        
        target_user_id = int(parts[1])
        
        if is_premium_user(target_user_id):
            bot.reply_to(message, f"ℹ️ User `{target_user_id}` is already a premium user.", parse_mode="Markdown")
        else:
            add_premium_user(target_user_id)
            bot.reply_to(message, f"✅ **Success!** User `{target_user_id}` has been added to premium.", parse_mode="Markdown")
            
    except ValueError:
        bot.reply_to(message, "❌ **Error:** Please provide a valid user ID.", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ **Error:** {str(e)}", parse_mode="Markdown")

@bot.message_handler(commands=['removepro'])
def remove_premium_command(message):
    """Remove user from premium (owners only)"""
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.reply_to(message, "❌ **Access Denied:** This command is for owners only.", parse_mode="Markdown")
        return
    
    try:
        # Get target user ID from command
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, """**Usage:** `/removepro [user_id]`

**Example:** `/removepro 123456789`""", parse_mode="Markdown")
            return
        
        target_user_id = int(parts[1])
        
        if not is_premium_user(target_user_id):
            bot.reply_to(message, f"ℹ️ User `{target_user_id}` is not a premium user.", parse_mode="Markdown")
        else:
            remove_premium_user(target_user_id)
            bot.reply_to(message, f"✅ **Success!** User `{target_user_id}` has been removed from premium.", parse_mode="Markdown")
            
    except ValueError:
        bot.reply_to(message, "❌ **Error:** Please provide a valid user ID.", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ **Error:** {str(e)}", parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Show bot statistics (owners only)"""
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.reply_to(message, "❌ **Access Denied:** This command is for owners only.", parse_mode="Markdown")
        return
    
    # Calculate stats
    total_users = len(user_database)
    premium_count = len([uid for uid in user_database if is_premium_user(uid)])
    chat_active = len(chat_mode)
    
    stats_text = f"""📊 **BrahMos AI Statistics**

**👥 Users:**
• Total Users: `{total_users}`
• Premium Users: `{premium_count}`
• Free Users: `{total_users - premium_count}`

**🔧 System:**
• Bot Uptime: `{format_uptime(bot_start_time)}`
• Chat Mode Active: `{chat_active}`
• Owners: `{len(config.OWNER_IDS)}`

**📈 Status:** All systems operational ✅"""
    
    bot.reply_to(message, stats_text, parse_mode="Markdown")
    
# ---- /ping: latency + uptime + status ----
from utils import format_uptime

@bot.message_handler(commands=['ping'])
def ping_command(message):
    chat_id = message.chat.id

    # measure Bot API round-trip latency using getMe
    t0 = time.perf_counter()
    api_ok = False
    try:
        resp = requests.get(f"https://api.telegram.org/bot{config.BOT_TOKEN}/getMe", timeout=5)
        api_ok = resp.ok and resp.json().get("ok", False)
    except Exception:
        api_ok = False
    latency_ms = (time.perf_counter() - t0) * 1000.0

    # uptime from existing bot_start_time
    uptime = format_uptime(bot_start_time)

    status = "✅ Operational" if api_ok else "⚠️ Degraded"
    msg = (
        "🎯 Pong!\n\n"
        f"• Latency: {latency_ms:.0f} ms\n"
        f"• Uptime: {uptime}\n"
        f"• Status: {status}\n\n"
        f" Bot Is Fucntional and Ready-To-Use 🚀"
    )
    bot.send_message(chat_id, msg)

@bot.message_handler(commands=['debug'])
def debug_command(message):
    """Debug information (owners only)"""
    user_id = message.from_user.id
    
    if not is_owner(user_id):
        bot.reply_to(message, "❌ **Access Denied:** This command is for owners only.", parse_mode="Markdown")
        return
    
    debug_text = f"""🔧 **BrahMos AI Debug Info**

**🌐 API Endpoints:**
• Chat: `{config.CHAT_API_ENDPOINT}`
• Image: `{config.IMAGE_API_URL}`
• TTS: `{config.TTS_API_ENDPOINT}`

**🤖 Models:**
• Chat: `{config.CHAT_MODEL}`
• TTS: `{config.TTS_MODEL}`

**📊 System Status:**
• Bot Uptime: `{format_uptime(bot_start_time)}`
• Total Users: `{len(user_database)}`
• Premium Users: `{len([uid for uid in user_database if is_premium_user(uid)])}`
• Chat Mode Active: `{len(chat_mode)}`

**🔒 Access Control:**
• Owners: `{config.OWNER_IDS}`
• Your ID: `{user_id}`

**📝 Files:**
• Premium Users: `{config.PREMIUM_USERS_FILE}`
• Usage Data: `{config.USAGE_DATA_FILE}`

✅ **All systems operational!**"""
    
    bot.reply_to(message, debug_text, parse_mode="Markdown")

# Callback handlers for inline keyboards
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Handle all inline keyboard callbacks"""
    user_id = call.from_user.id
    
    try:
        if call.data == "help":
            handle_help_callback(bot, call, usage_tracker)
        elif call.data == "my_info":
            handle_my_info_callback(bot, call, usage_tracker)
        elif call.data == "back_to_start":
            handle_back_to_start_callback(bot, call)
        elif call.data == "quick_chat":
            handle_quick_chat_callback(bot, call, chat_mode, user_waiting_for_chat)
        elif call.data == "quick_image":
            handle_quick_image_callback(bot, call, user_waiting_for_image)
        elif call.data == "quick_tts":
            handle_quick_tts_callback(bot, call, user_waiting_for_tts)
        elif call.data == "upgrade_premium":
            handle_upgrade_premium_callback(bot, call)
            
        # Answer the callback query
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        print(f"[DEBUG] Callback handler error: {e}")
        bot.answer_callback_query(call.id, "Error processing request.")

# Message handlers
@bot.message_handler(func=lambda message: message.from_user.id in user_waiting_for_image)
def handle_image_waiting(message):
    """Handle image generation when user is waiting"""
    handle_image_input(bot, message, user_waiting_for_image, usage_tracker)

@bot.message_handler(func=lambda message: message.from_user.id in user_waiting_for_tts)
def handle_tts_waiting(message):
    """Handle TTS when user is waiting"""
    handle_tts_input(bot, message, user_waiting_for_tts, usage_tracker)

@bot.message_handler(func=lambda message: message.from_user.id in chat_mode)
def handle_chat_mode(message):
    """Handle chat mode messages"""
    handle_chat_message(bot, message, chat_mode, user_waiting_for_chat)

@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
def handle_group_messages(message):
    """Handle group messages - only respond if mentioned or replied to"""
    # Check if bot is mentioned or if message is a reply to bot
    is_mentioned = False
    is_reply_to_bot = False
    
    # Check for mentions
    if message.text:
        is_mentioned = is_bot_mentioned(message.text)
    
    # Check if reply to bot
    if message.reply_to_message and message.reply_to_message.from_user.is_bot:
        is_reply_to_bot = True
    
    if is_mentioned or is_reply_to_bot:
        handle_chat_message(bot, message, chat_mode, user_waiting_for_chat)

@bot.message_handler(func=lambda message: message.chat.type == 'private')
def handle_private_messages(message):
    """Handle private messages that don't match other handlers"""
    user_id = message.from_user.id
    
    # If user is not in any special mode, treat as chat
    if (user_id not in user_waiting_for_image and 
        user_id not in user_waiting_for_tts and 
        user_id not in chat_mode):
        # Auto-activate chat mode for private messages
        chat_mode.add(user_id)
        handle_chat_message(bot, message, chat_mode, user_waiting_for_chat)
        
if __name__ == "__main__":
    print("🚀 BrahMos AI Bot Starting...")
    print(f"📊 Bot Token: {config.BOT_TOKEN[:10]}...")
    print(f"👥 Owners: {config.OWNER_IDS}")
    print("✅ Bot is running! Press Ctrl+C to stop.")
    
    try:
        bot.infinity_polling(none_stop=True, interval=0)
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
    except Exception as e:
        print(f"❌ Bot error: {e}")