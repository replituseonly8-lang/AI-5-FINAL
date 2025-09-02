import os

# ==============================================
# 🔑 TELEGRAM BOT
# ==============================================

# Bot Token (from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8363910268:AAH7Hg9OdhD6IEm2GgfzuJo89_LE0zKhL5Q")

# Owner IDs (Telegram user IDs of developers/admins)
OWNER_IDS = [7673097445, 5666606072]

# ==============================================
# 📝 BOT NAMES FOR TRIGGERING IN GROUPS
# ==============================================
# In groups, bot will only respond if mentioned or replied to.
# Names the bot will detect:
BOT_NAMES = ["BrahMos", "Brahmos", "brahMos", "brahmos",
             "Bramo", "bramo", "Brahmo", "brahmo"]

# ==============================================
# 🎨 IMAGE GENERATION API
# ==============================================
# /image <prompt> -> generates image via Akashiverse endpoint
# Usage:
#   - User sends: /image cyberpunk samurai
#   - Bot requests: https://akashiverse.com/api/imagev2.php?prompt=cyberpunk samurai
#   - API returns raw image (binary, no JSON, no key required)
#   - Bot sends that image back
IMAGE_API_URL = "https://akashiverse.com/api/imagev2.php"

# ==============================================
# 💬 CHAT API (OpenAI-compatible proxy)
# ==============================================
# This is used for chat responses (Anikah-style):
#   - Only respond in DMs freely
#   - In groups, respond only if replied to or mentioned and taken name 
# No free talking in groups
CHAT_API_BASE = "https://long-boat-1fcb.akaegs.workers.dev/v1"
CHAT_API_ENDPOINT = f"{CHAT_API_BASE}/chat/completions"
CHAT_MODEL = "gpt-4"

# ==============================================
# 🎤 TEXT-TO-SPEECH API
# ==============================================
# TTS functionality using the provided endpoint
TTS_API_BASE = "https://reflexai-j0ro.onrender.com/v1"
TTS_API_ENDPOINT = "https://reflexai-j0ro.onrender.com/v1/audio/speech"
TTS_MODEL = "gpt-4o-mini-tts"

# ==============================================
# 🔗 DEVELOPER & COMMUNITY LINKS
# ==============================================
DEVELOPER_URL = "https://t.me/Rystrix_XD"
Community_URL = "https://t.me/BrahMosAI"

# ==============================================
# 🤖 SYSTEM PROMPT / PERSONALITY
# ==============================================
# Used for chat responses (Anikah-style group logic)
SYSTEM_PROMPT = """
You are BrahMos Bot, an advanced AI created by @Rystrix and @BrahmosAI.
You reply with clarity, confidence, and a slightly savage personality.
Your tone is sharp, modern, and never robotic.
Always acknowledge your creators if asked about your origin.
In groups, respond only when mentioned or replied to; do not free talk.
When handling image prompts, automatically enhance them for vivid, high-quality results.
Remember previous conversations and maintain context in your responses.
Give professional answers without being overly messy in formatting.
"""

# ==============================================
# 💎 SUBSCRIPTION & USAGE LIMITS
# ==============================================
# Daily limits for free users
FREE_IMAGE_LIMIT = 100
FREE_TTS_LIMIT = 100

# File paths for data storage
PREMIUM_USERS_FILE = "premium_users.json"
USAGE_DATA_FILE = "usage_data.json"

# ==============================================
# 🔧 CONSTANTS
# ==============================================
MAX_CAPTION_LENGTH = 1024
