import logging
import httpx  
import asyncio
import re
import sys
import pyotp  # 2FA ওটিপি জেনারেট করার জন্য
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ==================== কনফিগারেশন ====================
TELEGRAM_BOT_TOKEN = '8699807890:AAEgxfORsRbsFcV2cmL0g69TvhaIsIKYcuw'  
ZENEX_API_KEY = 'ZNX_E4TY657EJ6GTWJHML7IJZ6UV'                        
BASE_URL = 'https://api.zenexnetwork.com' 

# 🔗 আপনার নিজস্ব রেফারেল লিংক
MY_REFER_LINK = "https://t.me/your_bot_username?start=refer_id"  

# 📢 মেইন চ্যানেল কনফিগারেশন
MAIN_CHANNEL_ID = '@nscoinbuy'  
CHANNEL_LINK = 'https://t.me/nscoinbuy'  

# 🔑 ওটিপি গ্রুপ কনফিগারেশন
OTP_GROUP_ID = '@NR_Number_OTP'  
OTP_GROUP_LINK = 'https://t.me/NR_Number_OTP'

ALLOWED_GROUP_IDS = [
    -1004335865448  
]

HEADERS = {
    'mapikey': ZENEX_API_KEY, 
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
# ===================================================

APPS_DATA = {
    "facebook": "📘 Facebook",
    "instagram": "📸 Instagram",
    "fb_pc_clone": "🖥️ Fb PC Clone",
    "discord": "💬 Discord"
}

COUNTRIES_DATA = {
    "ghana": {"name": "Ghana", "emoji": "🇬🇭", "range": "23350XXX"},
"mali": {"name": "Mali", "emoji": "🇲🇱", "range": "22358XXX"},
"guinea": {"name": "Guinea", "emoji": "🇬🇳", "range": "224654XXX"},
"syria": {"name": "Syria", "emoji": "🇸🇾", "range": "963960XXX"},
"togo": {"name": "Togo", "emoji": "🇹🇬", "range": "22895XXX"},
"ivory": {"name": "Ivory Coast", "emoji": "🇨🇮", "range": "225078XXX"},
"myanmar": {"name": "Myanmar", "emoji": "🇲🇲", "range": "95989XXX"},
"madagascar": {"name": "Madagascar", "emoji": "🇲🇬", "range": "261349XXX"},
"sierra": {"name": "Sierra Leone", "emoji": "🇸🇱", "range": "232751XXX"},
"benin": {"name": "Benin", "emoji": "🇧🇯", "range": "22901XXX"},
"CENTRAL AFRICAN REPUBLIC": {"name": "CENTRAL AFRICAN REPUBLIC", "emoji": "🇨🇫", "range": "236728XXX"},
}

STRINGS = {
    "bn": {
        "welcome_combined": (
            "╭──────────────────────────────╮\n"
            "    🌟  *𝐍𝐑  𝐍𝐔𝐌𝐁𝐄Ｒ  𝐁𝐎𝐓* 🌟\n"
            "╰──────────────────────────────╯\n"
            "👋 *Hello {name}!* \n\n"
            "⚪️ ` Welcome to Number & OTP Service `\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📱 *𝐒𝐄𝐋𝐄𝐂𝐓  𝐀𝐏𝐏𝐋𝐈𝐂𝐀𝐓𝐈𝐎𝐍:*\n"
            "🔴 ` প্রিয় ইউজার, অনুগ্রহ করে নিচের বাটনগুলো `\n"
            "     ` থেকে আপনার কাঙ্ক্ষিত অ্যাপটি সিলেক্ট করুন। `\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💎 *Premium OTP Service*"
        ), 
        "must_join": "📢 *বটটি ব্যবহার করতে হলে আপনাকে আমাদের মেইন চ্যানেল এবং ওটিপি গ্রুপ দুটিতেই জয়েন করতে হবে!* \n\nনিচের বাটনগুলো থেকে জয়েন সম্পন্ন করুন এবং তারপর 'Joined ✅' বাটনে চাপ দিন।",
        "select_country": "👋 **Welcome!**\n✅ ` Choose a country from the buttons below. `", 
        "loading_data": "🔄 ` ZENEX Network থেকে লাইভ ডেটা লোড হচ্ছে... `",
        "searching_num": "🔄 ` নতুন নম্বর খোঁজা হচ্ছে, অপেক্ষা করুন... `",
        "not_found": "❌ তথ্য পাওয়া যায়নি।",
        "btn_get_num": "☎️ Get Number",
        "btn_live_acc": "📊 Generate Range", 
        "btn_2fa": "🔐 2FA", 
        "btn_refer_link": "🔗 Refer Link" 
    }
}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

active_auto_refreshes = {}
user_states = {}  # ইউজারদের স্টেট ট্র্যাকিং

async def post_init(application: Application) -> None:
    commands = [BotCommand("start", "🏠 Start / রিস্টার্ট করুন")]
    await application.bot.set_my_commands(commands)

async def is_user_joined(bot, user_id: int) -> bool:
    try:
        member_main = await bot.get_chat_member(chat_id=MAIN_CHANNEL_ID, user_id=user_id)
        is_in_main = member_main.status in ['member', 'administrator', 'creator']
        
        member_otp = await bot.get_chat_member(chat_id=OTP_GROUP_ID, user_id=user_id)
        is_in_otp = member_otp.status in ['member', 'administrator', 'creator']
        
        return is_in_main and is_in_otp
    except Exception as e:
        logging.error(f"Error checking dual membership: {e}")
        return False

def mask_number(phone_number: str) -> str:
    clean_num = re.sub(r'\D', '', phone_number)
    if len(clean_num) <= 6:
        return f"+{clean_num}"
    start_part = clean_num[:5]
    end_part = clean_num[-3:]
    masked_part = "*" * (len(clean_num) - 8)
    return f"+{start_part}{masked_part}{end_part}"

def detect_app_from_message(sms_text: str, default_app: str) -> str:
    if not sms_text:
        return default_app
    sms_lower = sms_text.lower()
    if "instagram" in sms_lower or "ig code" in sms_lower:
        return "📸 Instagram"
    elif "facebook" in sms_lower or "fb-" in sms_lower:
        return "📘 Facebook"
    elif "discord" in sms_lower:
        return "💬 Discord"
    return default_app

async def send_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    join_buttons = [
        [InlineKeyboardButton("📢 Join Main Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🔑 Join OTP Group", url=OTP_GROUP_LINK)],
        [InlineKeyboardButton("Joined ✅", callback_data="check_join")]
    ]
    reply_markup = InlineKeyboardMarkup(join_buttons)
    if update.callback_query:
        await update.callback_query.message.reply_text(STRINGS["bn"]["must_join"], reply_markup=reply_markup, parse_mode='Markdown')
    else:
        await update.message.reply_text(STRINGS["bn"]["must_join"], reply_markup=reply_markup, parse_mode='Markdown')

def get_apps_markup():
    inline_keyboard = []
    apps_keys = list(APPS_DATA.keys())
    for i in range(0, len(apps_keys), 2):
        key1 = apps_keys[i]
        row = [InlineKeyboardButton(APPS_DATA[key1], callback_data=f"app_{key1}")]
        if i + 1 < len(apps_keys):
            key2 = apps_keys[i+1]
            row.append(InlineKeyboardButton(APPS_DATA[key2], callback_data=f"app_{key2}"))
        inline_keyboard.append(row)
    return InlineKeyboardMarkup(inline_keyboard)

def get_main_keyboard():
    keyboard_layout = [
        [KeyboardButton(STRINGS["bn"]["btn_get_num"]), KeyboardButton(STRINGS["bn"]["btn_live_acc"])], 
        [KeyboardButton(STRINGS["bn"]["btn_2fa"]), KeyboardButton(STRINGS["bn"]["btn_refer_link"])] 
    ]
    return ReplyKeyboardMarkup(keyboard_layout, resize_keyboard=True)

async def show_apps(update: Update, context: ContextTypes.DEFAULT_TYPE, edit_existing=False):
    user_id = update.effective_user.id
    if not await is_user_joined(context.bot, user_id):
        if update.callback_query:
            await update.callback_query.answer("⚠️ আগে দুটি চ্যানেলেই জয়েন করুন!", show_alert=True)
        else:
            await send_join_request(update, context)
        return

    reply_markup = get_apps_markup()
    user_first_name = update.effective_user.first_name if update.effective_user.first_name else "User"
    combined_text = STRINGS["bn"]["welcome_combined"].format(name=user_first_name)
    
    reply_markup_reply = get_main_keyboard()

    if edit_existing and update.callback_query:
        await update.callback_query.message.edit_text(combined_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        if update.callback_query:
            await update.callback_query.message.reply_text(combined_text, reply_markup=reply_markup, parse_mode='Markdown')
        elif update.message:
            await update.message.reply_text(combined_text, reply_markup=reply_markup_reply, parse_mode='Markdown')
            await update.message.reply_text("👇 *Available Apps:*", reply_markup=reply_markup, parse_mode='Markdown')

async def show_countries(update: Update, context: ContextTypes.DEFAULT_TYPE, selected_app_key=""):
    inline_keyboard = []
    keys = list(COUNTRIES_DATA.keys())
    for i in range(0, len(keys), 2):
        key1 = keys[i]
        c1 = COUNTRIES_DATA[key1]
        row = [InlineKeyboardButton(f"{c1['emoji']} {c1['name']} 1", callback_data=f"country_{key1}_{selected_app_key}")]
        if i + 1 < len(keys):
            key2 = keys[i+1]
            c2 = COUNTRIES_DATA[key2]
            row.append(InlineKeyboardButton(f"{c2['emoji']} {c2['name']} 1", callback_data=f"country_{key2}_{selected_app_key}"))
        inline_keyboard.append(row)
    
    inline_keyboard.append([InlineKeyboardButton("⬅️ Back to Apps", callback_data="back_to_apps")])
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    if update.callback_query:
        await update.callback_query.message.edit_text(STRINGS["bn"]["select_country"], reply_markup=reply_markup, parse_mode='Markdown')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states.pop(user_id, None)  
    if await is_user_joined(context.bot, user_id):
        await show_apps(update, context, edit_existing=False)
    else:
        await send_join_request(update, context)

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_user_joined(context.bot, user_id):
        await send_join_request(update, context)
        return

    user_text = update.message.text
    
    # ❌ Cancel বাটন হ্যান্ডেল
    if user_text == "❌ Cancel":
        user_states.pop(user_id, None)
        await update.message.reply_text("❌ অপারেশন বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return

# রেঞ্জ ইনপুট হ্যান্ডেল করার লজিক
        if user_states.get(user_id) == "AWAITING_RANGE":
            user_states.pop(user_id, None)
            user_range = user_text.strip()
            status_msg = await update.message.reply_text(STRINGS["bn"]["searching_num"])
            try:
                url = f"{BASE_URL}/v1/getnum"
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, json={"range": user_range}, headers=HEADERS, timeout=15.0)
                
                if response.status_code == 200:
                    res_data = response.json()
                    if "data" in res_data and "copy" in res_data["data"]:
                        allocated_num = res_data["data"]["copy"]
                        
                        # কান্ট্রি ডাটা খুঁজে বের করার লজিক
                        country_info = next((c for c in COUNTRIES_DATA.values() if c.get("range") == user_range), {"emoji": "🌍", "name": "Manual"})

                        msg_template = (
                            f"✨ {country_info['emoji']} *NAHID NUMBER PANNEL ALLOCATED* ✨\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"🌍 *Country:* {country_info['emoji']} {country_info['name']}\n"
                            f"🔢 *Number:* `{allocated_num}`\n"
                            f"━━━━━━━━━━━━━━━━━━\n"
                            f"⏳ *ওটিপির জন্য অপেক্ষা করা হচ্ছে...*"
                        )

                        action_buttons = [
                            [InlineKeyboardButton("🔑 Receive OTPs (Refresh)", callback_data=f"check:{allocated_num}:manual_")],
                            [InlineKeyboardButton("🔄 New Number", callback_data=f"retry_manual_{user_range}"), InlineKeyboardButton("📢 Codes Group", url=OTP_GROUP_LINK)]
                        ]
                        
                        sent_msg = await status_msg.edit_text(msg_template, reply_markup=InlineKeyboardMarkup(action_buttons), parse_mode='Markdown')
                        asyncio.create_task(auto_refresh_loop(context, update.message.chat_id, sent_msg.message_id, allocated_num, "manual", ""))
                    else:
                        await status_msg.edit_text("❌ ওই রেঞ্জে কোনো নাম্বার পাওয়া যায়নি।")
                else:
                    await status_msg.edit_text(f"❌ Error: {response.status_code}")
            except Exception as e:
                await status_msg.edit_text(f"⚠️ Error: {str(e)}")
            return

    # আপনার আগের 2FA এবং অন্যান্য বাটন হ্যান্ডেলারগুলো এখানে নিচে যোগ করুন
    if user_text == STRINGS["bn"]["btn_live_acc"]:
        user_states[user_id] = "AWAITING_RANGE"
        await update.message.reply_text("📝 *Please enter your Range (e.g., 232765XXX):*", parse_mode='Markdown')
        return

    # বাকি কোড...

    user_text = update.message.text
    
    if user_text == "❌ Cancel":
        user_states.pop(user_id, None)
        await update.message.reply_text("❌ 2FA ভেরিফিকেশন বাতিল করা হয়েছে।", reply_markup=get_main_keyboard())
        return

    # 🔑 প্রথমবার সিক্রেট কি ইনপুট নেওয়ার লজিক
    if user_states.get(user_id) == "AWAITING_2FA_KEY":
        clean_key = user_text.replace(" ", "").upper()
        
        if len(clean_key) >= 16 and re.match(r"^[A-Z2-7]+$", clean_key):
            try:
                totp = pyotp.TOTP(clean_key)
                current_otp = totp.now()  
                
                response_msg = (
                    f"🔐 *Your 2FA Live OTP Code:*\n\n"
                    f"`{current_otp}`\n\n"
                    f"💡 _কোডটি কপি করতে সেটির ওপর ট্যাপ করুন। এটি প্রতি ৩০ সেকেন্ড পর পর পরিবর্তিত হয়।_\n\n"
                    f"👇 *লাইভ কোড আপডেট করতে নিচের বাটনে চাপুন:*"
                )
                
                # ইনলাইন রিফ্রেশ বাটন (একই মেসেজে সংযুক্ত করার জন্য)
                refresh_btn = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh Code", callback_data=f"2farefresh_{clean_key}")]
                ])
                
                user_states.pop(user_id, None)  # স্টেট ক্লিয়ার
                
                # ১টি মেসেজের ভেতরেই কোড এবং বাটন একসাথে পাঠানো হলো
                await update.message.reply_text(response_msg, parse_mode='Markdown', reply_markup=refresh_btn)
            except Exception:
                await update.message.reply_text("❌ দুঃখিত, আপনার দেওয়া 2FA Key টি সঠিক নয়। অনুগ্রহ করে সঠিক Key দিন।")
        else:
            await update.message.reply_text(
                "⚠️ *ভুল ফরম্যাট!*\n"
                "• কমপক্ষে ১৬ অক্ষরের হতে হবে\n"
                "• শুধুমাত্র A-Z এবং ২-৭ এর মধ্যে অক্ষর থাকতে পারবে\n\n"
                "অনুগ্রহ করে আবার চেষ্টা করুন অথবা '❌ Cancel' বাটনে ক্লিক করুন।", 
                parse_mode='Markdown'
            )
        return

    if user_text == STRINGS["bn"]["btn_get_num"]: 
        reply_markup = get_apps_markup()
        await update.message.reply_text("👇 *Available Apps:*", reply_markup=reply_markup, parse_mode='Markdown')
        return

    if user_text == STRINGS["bn"]["btn_2fa"]:
        user_states[user_id] = "AWAITING_2FA_KEY"
        cancel_keyboard = ReplyKeyboardMarkup([[KeyboardButton("❌ Cancel")]], resize_keyboard=True)
        
        msg_2fa = (
            "🔓 *2FA Authenticator*\n\n"
            "আপনার 2FA Secret Key পাঠান।\n\n"
            "📝 *Format:*\n"
            "`ABCD EFGH IGK84 LM44 NSER3 LM44`\n\n"
            "⚠️ *নিয়মাবলী:*\n"
            "• কমপক্ষে ১৬ অক্ষর\n"
            "• শুধুমাত্র A-Z এবং 2-7\n"
            "• Space ব্যবহার করতে হবে\n\n"
            "❌ বাতিল করতে '❌ Cancel' বাটনে ক্লিক করুন।"
        )
        await update.message.reply_text(msg_2fa, parse_mode='Markdown', reply_markup=cancel_keyboard)
        return

    if user_text == STRINGS["bn"]["btn_refer_link"]:
        refer_msg = (
            "🤝 *আমাদের রেফারেল প্রোগ্রাম!*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "আপনার বন্ধুদের আমাদের বটে আমন্ত্রণ জানান এবং আকর্ষণীয় বোনাস লুফে নিন।\n\n"
            f"🔗 *আপনার রেফারেল লিংক:* {MY_REFER_LINK}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 _লিংকটি শেয়ার করে আজই আর্নিং শুরু করুন!_"
        )
        await update.message.reply_text(refer_msg, parse_mode='Markdown')
        return

    if user_text == STRINGS["bn"]["btn_live_acc"]:
        endpoint = "v1/numsuccess/info"
        status_msg = await update.message.reply_text(STRINGS["bn"]["loading_data"], parse_mode='Markdown')
        try:
            url = f"{BASE_URL}/{endpoint}"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=HEADERS, timeout=15.0)
            
            if response.status_code == 200:
                await status_msg.edit_text(f"📊 *ZENEX Response:*\n\n`{response.text[:3500]}`", parse_mode='Markdown')
            else:
                await status_msg.edit_text(f"❌ Error Code: {response.status_code}\n\n`{response.text}`")
        except Exception as e:
            await status_msg.edit_text(f"⚠️ Connection Error: {str(e)}")

async def check_otp_from_api(target_number):
    try:
        clean_target = re.sub(r'\D', '', str(target_number))
        if not clean_target:
            return None, None
            
        url = f"{BASE_URL}/v1/numsuccess/info" 
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=HEADERS, timeout=10.0)
        
        if response.status_code == 200:
            res_json = response.json()
            if "data" in res_json and "otps" in res_json["data"]: 
                for item in res_json["data"]["otps"]: 
                    clean_api_num = re.sub(r'\D', '', str(item.get("number", ""))) 
                    if clean_api_num and clean_api_num == clean_target: 
                        full_sms = item.get("otp", "") 
                        otp_match = re.search(r'\b\d{3}\s?\d{3}\b|\b\d{4,6}\b', full_sms)
                        if otp_match:
                            extracted_code = otp_match.group(0)
                            text_body = full_sms.replace(extracted_code, "").replace("<#>", "").strip()
                            return extracted_code, text_body
                        return None, full_sms
    except Exception as e:
        print(f"OTP System Internal Error: {e}")
    return None, None

async def auto_refresh_loop(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, target_num: str, country_key: str, selected_app_key: str):
    loop_key = f"{chat_id}_{message_id}"
    active_auto_refreshes[loop_key] = True
    
    country_info = COUNTRIES_DATA.get(country_key, {"name": "Unknown", "emoji": "🌍"})
    
    for _ in range(36):
        if not active_auto_refreshes.get(loop_key):
            break
            
        await asyncio.sleep(5)
        
        otp_code, text_body = await check_otp_from_api(target_num)
        
        if otp_code or text_body:
            sms_string = text_body if text_body else ""
            initial_app_name = APPS_DATA.get(selected_app_key, "Unknown App")
            actual_app_name = detect_app_from_message(sms_string, initial_app_name)
            
            msg_template = (
                f"✨ {country_info['emoji']} *NAHID NUMBER PANNEL ALLOCATED* ✨\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌏 *Country:* {country_info['emoji']} {country_info['name']}\n"
                f"🔢 *Number:* `{target_num}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ *OTP Code:* `{otp_code if otp_code else 'N/A'}`\n\n"
                f"💬 {text_body}\n"
            )
            action_buttons = [
                [InlineKeyboardButton("🔑 Receive OTPs (Refresh)", callback_data=f"check:{target_num}:{country_key}_`{selected_app_key}`")], 
                [
                    InlineKeyboardButton("🔄 New Number", callback_data=f"retry_{country_key}_{selected_app_key}"), 
                    InlineKeyboardButton("📢 Codes Group", url=OTP_GROUP_LINK) 
                ],
                [InlineKeyboardButton("⬅️ Back to Countries", callback_data=f"app_{selected_app_key}")] 
            ]
            reply_markup = InlineKeyboardMarkup(action_buttons)
            try:
                await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=msg_template, reply_markup=reply_markup, parse_mode='Markdown')
            except Exception:
                pass
                
            hidden_num = mask_number(target_num)
            group_msg = (
                f"📢 *New OTP Received!*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📱 *App Name:* `{actual_app_name}`\n"
                f"🌍 *Country:* {country_info['name']} {country_info['emoji']}\n"
                f"🔢 *Number:* `{hidden_num}`\n"
                f"🔑 *OTP Code:* `{otp_code if otp_code else 'N/A'}`\n"
                f"💬 *Details:* {text_body}\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            for group_id in ALLOWED_GROUP_IDS:
                try:
                    await context.bot.send_message(chat_id=group_id, text=group_msg, parse_mode='Markdown')
                except Exception:
                    pass
            
            break
            
    active_auto_refreshes.pop(loop_key, None)

async def handle_callback_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    if not await is_user_joined(context.bot, user_id):
        await query.answer("⚠️ অনুগ্রহ করে আগে দুটি চ্যানেলেই জয়েন করুন!", show_alert=True)
        return
        
    await query.answer()
    callback_data = query.data
    
    if callback_data.startswith("app_"):
        selected_app_key = callback_data.replace("app_", "")
        await show_countries(update, context, selected_app_key=selected_app_key)
        return

    if callback_data.startswith("country_") or callback_data.startswith("retry_"):
        data_parts = callback_data.replace("country_", "").replace("retry_", "").split("_")
        country_key = data_parts[0]
        selected_app_key = data_parts[1] if len(data_parts) > 1 else ""
        
        country_info = COUNTRIES_DATA.get(country_key)
        if not country_info:
            await query.edit_message_text(STRINGS["bn"]["not_found"])
            return
            
        selected_range = country_info["range"]
        await query.edit_message_text(text=STRINGS["bn"]["searching_num"], parse_mode='Markdown') 
        
        try:
            url = f"{BASE_URL}/v1/getnum"
            payload = {"range": selected_range}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=HEADERS, timeout=15.0)
                
            if response.status_code == 200:
                res_data = response.json() 
                if "data" in res_data and "copy" in res_data["data"]: 
                    allocated_num = res_data["data"]["copy"] 
                    clean_callback_num = re.sub(r'\D', '', str(allocated_num))
                    
                    msg_template = (
                        f"✨ {country_info['emoji']} *NAHID NUMBER PANNEL ALLOCATED* ✨\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"🌏 *Country:* {country_info['emoji']} {country_info['name']}\n" 
                        f"🔢 *Number:* `{clean_callback_num}`\n" 
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                        f"⏳ *ওটিপির জন্য অপেক্ষা করা হচ্ছে... (৩-৪ বার রিসেন্ড কোড করুন)*\n"
                    )
                    
                    action_buttons = [
                        [InlineKeyboardButton("🔑 Receive OTPs (Refresh)", callback_data=f"check:{clean_callback_num}:{country_key}_`{selected_app_key}`")], 
                        [
                            InlineKeyboardButton("🔄 New Number", callback_data=f"retry_{country_key}_{selected_app_key}"), 
                            InlineKeyboardButton("📢 Codes Group", url=OTP_GROUP_LINK) 
                        ],
                        [InlineKeyboardButton("⬅️ Back to Countries", callback_data=f"app_{selected_app_key}")] 
                    ]
                    reply_markup = InlineKeyboardMarkup(action_buttons) 
                    sent_msg = await query.edit_message_text(msg_template, reply_markup=reply_markup, parse_mode='Markdown')
                    
                    asyncio.create_task(auto_refresh_loop(
                        context, 
                        chat_id=query.message.chat_id, 
                        message_id=sent_msg.message_id, 
                        target_num=clean_callback_num, 
                        country_key=country_key, 
                        selected_app_key=selected_app_key
                    ))
                else:
                    await query.edit_message_text(f"❌ কোড: {response.status_code}\n\n`{response.text}`") 
            else:
                await query.edit_message_text(f"❌ এরর রেসপন্স: {response.status_code}\n`{response.text}`")
                    
        except Exception as e:
            await query.edit_message_text(f"⚠️ এরর ঘটেছে:\n{str(e)}") 

async def handle_callback_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    
    # 🔄 2FA লাইভ কোড ইনস্ট্যান্ট রিফ্রেশ করার ইনলাইন লজিক
    if query.data.startswith("2farefresh_"):
        secret_key = query.data.replace("2farefresh_", "")
        try:
            totp = pyotp.TOTP(secret_key)
            new_otp = totp.now()
            
            updated_text = (
                f"🔐 *Your 2FA Live OTP Code:*\n\n"
                f"`{new_otp}`\n\n"
                f"💡 _কোডটি কপি করতে সেটির ওপর ট্যাপ করুন। এটি প্রতি ৩০ সেকেন্ড পর পর পরিবর্তিত হয়।_\n\n"
                f"👇 *লাইভ কোড আপডেট করতে নিচের বাটনে চাপুন:*"
            )
            
            # বাটনটি যাতে মেসেজ থেকে গায়েব না হয়ে যায়, তাই বাটন লেআউট আবার ডিফাইন করা হলো
            refresh_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Refresh Code", callback_data=f"2farefresh_{secret_key}")]
            ])
            
            # সরাসরি কারেন্ট মেসেজটিকেই (যেটাতে বাটন ক্লিক হয়েছে) এডিট করা হচ্ছে
            await query.message.edit_text(
                text=updated_text,
                parse_mode='Markdown',
                reply_markup=refresh_btn
            )
            await query.answer("🔄 OTP Code Successfully Updated!", show_alert=False)
        except Exception as e:
            logging.error(f"2FA Refresh Error: {e}")
            await query.answer("❌ রিফ্রেশ করা যায়নি! কি-টি চেক করুন।", show_alert=True)
        return

    if query.data == "check_join":
        if await is_user_joined(context.bot, user_id):
            await query.answer("✅ ধন্যবাদ! সফলভাবে জয়েন করেছেন।", show_alert=False)
            try:
                await query.message.delete()  
            except Exception:
                pass
            await show_apps(update, context, edit_existing=False)
        else:
            await query.answer("❌ আপনি এখনো দুটি চ্যানেলে জয়েন করেননি! দয়া করে দুটি বাটনেই ক্লিক করে জয়েন নিশ্চিত করুন।", show_alert=True)
        return

    if not await is_user_joined(context.bot, user_id):
        await query.answer("⚠️ অ্যাকশন রিজেক্টেড! আপনি চ্যানেল থেকে লেフト নিয়েছেন।", show_alert=True)
        return

    if query.data == "back_to_apps":
        loop_key = f"{query.message.chat_id}_{query.message.message_id}"
        active_auto_refreshes[loop_key] = False
        await query.answer()
        await show_apps(update, context, edit_existing=True)
        return

    if query.data.startswith("check:"):
        parts = query.data.split(":")
        target_num = parts[1]
        
        clean_data_raw = parts[2].replace("`", "")
        data_parts = clean_data_raw.split("_")
        country_key = data_parts[0]
        selected_app_key = data_parts[1] if len(data_parts) > 1 else ""
        
        country_info = COUNTRIES_DATA.get(country_key, {"name": "Unknown", "emoji": "🌍"})
        otp_code, text_body = await check_otp_from_api(target_num)
        
        if otp_code or text_body:
            loop_key = f"{query.message.chat_id}_{query.message.message_id}"
            active_auto_refreshes[loop_key] = False
            
            await query.answer("✅ OTP পাওয়া গেছে!", show_alert=False)
            sms_string = text_body if text_body else ""
            initial_app_name = APPS_DATA.get(selected_app_key, "Unknown App")
            actual_app_name = detect_app_from_message(sms_string, initial_app_name)
            
            msg_template = (
                f"✨ {country_info['emoji']} *NAHID NUMBER PANNEL ALLOCATED* ✨\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌏 *Country:* {country_info['emoji']} {country_info['name']}\n"
                f"🔢 *Number:* `{target_num}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ *OTP Code:* `{otp_code if otp_code else 'N/A'}`\n\n"
                f"💬 {text_body}\n"
            )
            action_buttons = [
                [InlineKeyboardButton("🔑 Receive OTPs (Refresh)", callback_data=f"check:{target_num}:{country_key}_`{selected_app_key}`")], 
                [
                    InlineKeyboardButton("🔄 New Number", callback_data=f"retry_{country_key}_{selected_app_key}"), 
                    InlineKeyboardButton("📢 Codes Group", url=OTP_GROUP_LINK) 
                ],
                [InlineKeyboardButton("⬅️ Back to Countries", callback_data=f"app_{selected_app_key}")] 
            ]
            reply_markup = InlineKeyboardMarkup(action_buttons) 
            try:
                await query.edit_message_text(msg_template, reply_markup=reply_markup, parse_mode='Markdown') 
            except Exception:
                pass
            
            hidden_num = mask_number(target_num)
            group_msg = (
                f"📢 *New OTP Received!*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📱 *App Name:* `{actual_app_name}`\n"
                f"🌍 *Country:* {country_info['name']} {country_info['emoji']}\n"
                f"🔢 *Number:* `{hidden_num}`\n"
                f"🔑 *OTP Code:* `{otp_code if otp_code else 'N/A'}`\n"
                f"💬 *Details:* {text_body}\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            for group_id in ALLOWED_GROUP_IDS:
                try:
                    await context.bot.send_message(chat_id=group_id, text=group_msg, parse_mode='Markdown')
                except Exception:
                    pass
        else:
            await query.answer("⏳ ওটিপি এখনও আসেনি! এটি ৫ সেকেন্ড পর পর একাই রিফ্রেশ নিচ্ছে...", show_alert=True)

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback_actions, pattern=r"^(back_to_apps|check:|check_join|2farefresh_)"))
    application.add_handler(CallbackQueryHandler(handle_callback_clicks, pattern=r"^(app_|country_|retry_)"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

    print("🤖 Bot updated successfully with Fixed 2FA Inline Refresh Code...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
