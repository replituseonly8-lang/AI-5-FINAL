import io
import re
import requests
import config
from utils import AnimatedLoader

# ---------- MarkdownV2 escaping ----------
# Per Telegram MarkdownV2 rules, escape: _ * [ ] ( ) ~ ` > # + - = | { } . !
MDV2_CHARS = r'_\*\[\]\(\)~`>#+\-=|{}\.!'

def escape_markdown_v2(text: str) -> str:
    if not text:
        return ""
    # First escape backslashes, then the rest
    text = text.replace("\\", "\\\\")
    return re.sub(f"([{MDV2_CHARS}])", r"\\\1", text)

def truncate(text: str, limit: int = 1024) -> str:
    if text is None:
        return ""
    return text if len(text) <= limit else text[: limit - 3] + "..."

# ---------- API call ----------
def generate_image(full_prompt: str, bot=None, chat_id=None):
    """
    Always send the FULL prompt to the API.
    Returns image bytes or None.
    """
    loader = None
    try:
        if bot and chat_id:
            loader = AnimatedLoader(bot, chat_id, "Creating your masterpiece", "image")
            loader.start()

        params = {"prompt": full_prompt, "render": "true"}

        # Try GET
        resp = requests.get(config.IMAGE_API_URL, params=params, timeout=120)
        if _looks_like_image(resp):
            return resp.content

        # Fallback to POST JSON
        resp = requests.post(
            config.IMAGE_API_URL,
            json=params,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        if _looks_like_image(resp):
            return resp.content

        return None
    except requests.exceptions.Timeout:
        print("[DEBUG] Image generation timeout")
        return None
    except requests.exceptions.ConnectionError:
        print("[DEBUG] Image generation connection error")
        return None
    except Exception as e:
        print(f"[DEBUG] Image generation error: {e}")
        return None
    finally:
        if loader:
            loader.stop()

def _looks_like_image(resp: requests.Response) -> bool:
    if not resp or resp.status_code != 200:
        return False
    ctype = (resp.headers.get("Content-Type") or "").lower()
    if ctype.startswith("image/"):
        return True
    # Accept large binary that is not JSON
    return len(resp.content or b"") > 1000 and not ctype.startswith("application/json")

# ---------- Telegram send helpers ----------
def safe_send_photo(bot, chat_id, image_bytes: bytes, caption: str, reply_to=None):
    try:
        bot.send_photo(
            chat_id,
            io.BytesIO(image_bytes),
            caption=caption,
            parse_mode="MarkdownV2",
            reply_to_message_id=reply_to,
        )
    except Exception as e:
        print(f"[DEBUG] Failed to send photo: {e}")
        # Fallback: send without parse_mode
        try:
            bot.send_photo(
                chat_id,
                io.BytesIO(image_bytes),
                caption=caption.replace("\\", ""),  # loosen escaping on fallback
                reply_to_message_id=reply_to,
            )
        except Exception as e2:
            print(f"[DEBUG] Fallback photo send failed: {e2}")
            bot.send_message(chat_id, f"❌ Failed to send image\nError: {e2}")

# ---------- Handlers ----------
def handle_image_command(bot, message, user_waiting_for_image, usage_tracker):
    from utils import log_user_interaction, is_premium_user

    user_id = message.from_user.id
    log_user_interaction(message.from_user, "/image", "DM" if message.chat.type == "private" else "Group")

    text = (message.text or "").strip()
    if len(text.split()) <= 1:
        bot.reply_to(
            message,
            "🎨 Image Generation Help\n\nUsage: `/image [description]`\n\nExamples:\n• `/image cyberpunk samurai warrior`\n• `/image sunset over mountains`\n• `/image cute cat in space suit`\n\nTip: Be descriptive for better results!",
            parse_mode="Markdown",
        )
        return

    full_prompt = text[6:].strip()  # FULL prompt goes to API

    # Usage gates
    if not is_premium_user(user_id):
        if not usage_tracker.can_use_image(user_id):
            bot.reply_to(
                message,
                "🚫 Daily Image Limit Reached\n\nUpgrade to Premium for unlimited generations.\nContact @Rystrix to upgrade!",
                parse_mode="Markdown",
            )
            return
        remaining = usage_tracker.get_remaining_images(user_id)
        if remaining <= 10:
            bot.reply_to(message, f"⚠️ Only {remaining} image generations left today!", parse_mode="Markdown")

    img = generate_image(full_prompt, bot, message.chat.id)
    if not img:
        bot.reply_to(message, "❌ Image Generation Failed\nPlease try a different prompt.", parse_mode="Markdown")
        return

    shown = truncate(full_prompt, 900)  # leave headroom for the rest of caption after escaping
    safe_shown = escape_markdown_v2(shown)

    if not is_premium_user(user_id):
        usage_tracker.use_image(user_id)
        remaining = usage_tracker.get_remaining_images(user_id)
        tail = f"\n\n📊 Remaining today: {remaining}/100"
    else:
        tail = "\n\n💎 Premium User - Unlimited Access!"

    cap = f"🎨 *Generated Image*\n\n📝 *Prompt:* `{safe_shown}`\n\n✨ *Created by BrahMos AI*{escape_markdown_v2(tail)}"
    safe_send_photo(bot, message.chat.id, img, cap, reply_to=message.message_id)

def handle_image_input(bot, message, user_waiting_for_image, usage_tracker):
    from utils import is_premium_user

    uid = message.from_user.id
    if uid not in user_waiting_for_image:
        return
    user_waiting_for_image.discard(uid)

    full_prompt = (message.text or "").strip()
    img = generate_image(full_prompt, bot, message.chat.id)
    if not img:
        bot.send_message(message.chat.id, "❌ Image Generation Failed\nPlease try a different prompt.", parse_mode="Markdown")
        return

    shown = truncate(full_prompt, 900)
    safe_shown = escape_markdown_v2(shown)

    if not is_premium_user(uid):
        usage_tracker.use_image(uid)
        remaining = usage_tracker.get_remaining_images(uid)
        tail = f"\n\n📊 Remaining today: {remaining}/100"
    else:
        tail = "\n\n💎 Premium User - Unlimited Access!"

    cap = f"🎨 *Generated Image*\n\n📝 *Prompt:* `{safe_shown}`\n\n✨ *Created by BrahMos AI*{escape_markdown_v2(tail)}"
    safe_send_photo(bot, message.chat.id, img, cap, reply_to=message.message_id)
