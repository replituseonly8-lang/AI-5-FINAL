import telebot
import time
import threading
import json
import os
from datetime import datetime, date

class AnimatedLoader:
    """Class to handle animated loading messages with emojis"""
    
    def __init__(self, bot, chat_id, initial_message="Processing", animation_type="default"):
        self.bot = bot
        self.chat_id = chat_id
        self.initial_message = initial_message
        self.message = None
        self.is_running = False
        self.thread = None
        self.animation_type = animation_type
        
        if animation_type == "image":
            self.animation_frames = [
                "🎨 Creating magic...", "🖼️ Painting pixels...", "🎭 Bringing vision to life...", 
                "🖌️ Crafting masterpiece...", "🎨 Weaving colors...", "🖼️ Almost ready...",
                "🎭 Final touches...", "🖌️ Perfecting details..."
            ]
        elif animation_type == "prompt":
            self.animation_frames = [
                "📝 ⚡", "✍️ ⚡", "📋 ⚡", "📝 💭", "✍️ 💭", "📋 💭"
            ]
        elif animation_type == "tts":
            self.animation_frames = [
                "🎤 Converting...", "🗣️ Synthesizing...", "🎵 Processing...", 
                "🔊 Generating...", "🎧 Finalizing...", "🎤 Almost ready..."
            ]
        else:
            self.animation_frames = [
                "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"
            ]
        
        self.frame_index = 0
        
    def start(self):
        """Start the animated loading"""
        if not self.is_running:
            self.is_running = True
            # Send initial message
            try:
                if self.animation_type == "image":
                    initial_text = f"{self.animation_frames[0]}\n\n⚡ *BrahMos AI is working its magic...*\n🎯 *Your masterpiece is being created!*"
                elif self.animation_type == "tts":
                    initial_text = f"{self.animation_frames[0]}\n\n🎤 *BrahMos AI is converting your text...*\n🔊 *High-quality speech coming up!*"
                else:
                    initial_text = f"{self.animation_frames[0]} {self.initial_message}..."
                self.message = self.bot.send_message(
                    self.chat_id, 
                    initial_text,
                    parse_mode="Markdown"
                )
                self.thread = threading.Thread(target=self._animate)
                self.thread.daemon = True
                self.thread.start()
            except Exception as e:
                print(f"[DEBUG] Failed to start animated loader: {e}")
                
    def _animate(self):
        """Internal animation loop"""
        while self.is_running:
            try:
                time.sleep(0.8)  # Update every 800ms to avoid rate limits
                if self.is_running and self.message:
                    self.frame_index = (self.frame_index + 1) % len(self.animation_frames)
                    if self.animation_type == "image":
                        new_text = f"{self.animation_frames[self.frame_index]}\n\n⚡ *BrahMos AI is working its magic...*\n🎯 *Your masterpiece is being created!*"
                    elif self.animation_type == "tts":
                        new_text = f"{self.animation_frames[self.frame_index]}\n\n🎤 *BrahMos AI is converting your text...*\n🔊 *High-quality speech coming up!*"
                    elif self.animation_type == "prompt":
                        new_text = f"{self.animation_frames[self.frame_index]} {self.initial_message}...\n\n⏳ *Please wait while BrahMos AI processes your request*"
                    else:
                        new_text = f"{self.animation_frames[self.frame_index]} {self.initial_message}..."
                    self.bot.edit_message_text(
                        new_text,
                        chat_id=self.chat_id,
                        message_id=self.message.message_id,
                        parse_mode="Markdown"
                    )
            except Exception as e:
                # Silently handle edit failures (message too old, etc.)
                break
                
    def stop(self, final_message=None):
        """Stop the animation and optionally update with final message"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
            
        if self.message and final_message:
            try:
                self.bot.edit_message_text(
                    final_message,
                    chat_id=self.chat_id,
                    message_id=self.message.message_id
                )
            except Exception as e:
                print(f"[DEBUG] Failed to update final message: {e}")
        elif self.message:
            try:
                self.bot.delete_message(self.chat_id, self.message.message_id)
            except Exception as e:
                print(f"[DEBUG] Failed to delete loader message: {e}")

def safe_send_photo_with_caption(bot, chat_id, photo_path, caption, reply_markup=None, parse_mode=None):
    """Safely send photo with caption, handling length limits"""
    import config
    
    try:
        if len(caption) > config.MAX_CAPTION_LENGTH:
            short_caption = caption[:config.MAX_CAPTION_LENGTH-3] + "..."
            with open(photo_path, 'rb') as photo_file:
                bot.send_photo(chat_id, photo_file, caption=short_caption, reply_markup=reply_markup, parse_mode=parse_mode)
            remaining_text = caption[config.MAX_CAPTION_LENGTH-3:]
            bot.send_message(chat_id, f"**Continued...**\n\n{remaining_text}", parse_mode=parse_mode)
        else:
            with open(photo_path, 'rb') as photo_file:
                bot.send_photo(chat_id, photo_file, caption=caption, reply_markup=reply_markup, parse_mode=parse_mode)
        return True
    except FileNotFoundError:
        bot.send_message(chat_id, f"🖼️ *[Image: {photo_path}]*\n\n{caption}", reply_markup=reply_markup, parse_mode=parse_mode)
        return False

def safe_edit_message(bot, chat_id, message_id, text, reply_markup=None, parse_mode=None):
    """Safely edit message - tries text first, then caption"""
    try:
        bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception:
        try:
            bot.edit_message_caption(caption=text, chat_id=chat_id, message_id=message_id, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e:
            print(f"[DEBUG] Edit message failed: {e}")
            # If both fail, send a new message instead
            try:
                bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode=parse_mode)
            except Exception as e2:
                print(f"[DEBUG] Send message also failed: {e2}")

def is_owner(user_id):
    """Check if user is owner"""
    import config
    return user_id in config.OWNER_IDS

def is_admin(user_id):
    """Check if user is admin"""
    import config
    return user_id in getattr(config, 'ADMIN_IDS', config.OWNER_IDS)

def is_bot_mentioned(text):
    """Check if any bot name is mentioned in group messages"""
    import config
    if not text:
        return False
    text_lower = text.lower()
    return any(name.lower() in text_lower for name in config.BOT_NAMES)

def format_uptime(start_time):
    """Format bot uptime"""
    uptime_seconds = int(time.time() - start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}h {minutes}m {seconds}s"

def get_user_mention(user):
    """Get user mention string"""
    if user.username:
        return f"@{user.username}"
    else:
        return f"[{user.first_name}](tg://user?id={user.id})"

def log_user_interaction(user, command, chat_type):
    """Log user interactions for debugging"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_info = f"{user.first_name} ({user.id})"
    if user.username:
        user_info += f" @{user.username}"
    print(f"[{timestamp}] {chat_type}: {user_info} used {command}")

# Premium user management functions
def load_premium_users():
    """Load premium users from JSON file"""
    import config
    try:
        if os.path.exists(config.PREMIUM_USERS_FILE):
            with open(config.PREMIUM_USERS_FILE, 'r') as f:
                return set(json.load(f))
        return set()
    except Exception as e:
        print(f"[DEBUG] Error loading premium users: {e}")
        return set()

def save_premium_users(premium_users):
    """Save premium users to JSON file"""
    import config
    try:
        with open(config.PREMIUM_USERS_FILE, 'w') as f:
            json.dump(list(premium_users), f)
    except Exception as e:
        print(f"[DEBUG] Error saving premium users: {e}")

# Global premium users set
premium_users = load_premium_users()

def is_premium_user(user_id):
    """Check if user is premium"""
    return user_id in premium_users

def add_premium_user(user_id):
    """Add user to premium"""
    premium_users.add(user_id)
    save_premium_users(premium_users)

def remove_premium_user(user_id):
    """Remove user from premium"""
    premium_users.discard(user_id)
    save_premium_users(premium_users)

# Usage tracking class
class UsageTracker:
    """Track daily usage for images and TTS"""
    
    def __init__(self):
        import config
        self.usage_file = config.USAGE_DATA_FILE
        self.usage_data = self.load_usage_data()
        
    def load_usage_data(self):
        """Load usage data from JSON file"""
        try:
            if os.path.exists(self.usage_file):
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    # Clean old data (older than today)
                    today = date.today().isoformat()
                    cleaned_data = {}
                    for user_id, user_data in data.items():
                        if user_data.get('date') == today:
                            cleaned_data[user_id] = user_data
                    return cleaned_data
            return {}
        except Exception as e:
            print(f"[DEBUG] Error loading usage data: {e}")
            return {}
    
    def save_usage_data(self):
        """Save usage data to JSON file"""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f)
        except Exception as e:
            print(f"[DEBUG] Error saving usage data: {e}")
    
    def get_user_data(self, user_id):
        """Get user usage data for today"""
        user_id_str = str(user_id)
        today = date.today().isoformat()
        
        if user_id_str not in self.usage_data or self.usage_data[user_id_str].get('date') != today:
            self.usage_data[user_id_str] = {
                'date': today,
                'images_used': 0,
                'tts_used': 0
            }
            self.save_usage_data()
        
        return self.usage_data[user_id_str]
    
    def can_use_image(self, user_id):
        """Check if user can generate an image"""
        if is_premium_user(user_id):
            return True
        
        import config
        user_data = self.get_user_data(user_id)
        return user_data['images_used'] < config.FREE_IMAGE_LIMIT
    
    def can_use_tts(self, user_id):
        """Check if user can use TTS"""
        if is_premium_user(user_id):
            return True
        
        import config
        user_data = self.get_user_data(user_id)
        return user_data['tts_used'] < config.FREE_TTS_LIMIT
    
    def use_image(self, user_id):
        """Use one image generation"""
        user_data = self.get_user_data(user_id)
        user_data['images_used'] += 1
        self.save_usage_data()
    
    def use_tts(self, user_id):
        """Use one TTS generation"""
        user_data = self.get_user_data(user_id)
        user_data['tts_used'] += 1
        self.save_usage_data()
    
    def get_remaining_images(self, user_id):
        """Get remaining image generations for today"""
        if is_premium_user(user_id):
            return 999999  # Large number to represent unlimited
        
        import config
        user_data = self.get_user_data(user_id)
        return max(0, config.FREE_IMAGE_LIMIT - user_data['images_used'])
    
    def get_remaining_tts(self, user_id):
        """Get remaining TTS generations for today"""
        if is_premium_user(user_id):
            return 999999  # Large number to represent unlimited
        
        import config
        user_data = self.get_user_data(user_id)
        return max(0, config.FREE_TTS_LIMIT - user_data['tts_used'])