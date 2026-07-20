#!/usr/bin/env python3
"""
SRRoot Panel Telegram Bot
Deployer & Manager for SRRoot Panel on Cloudflare Workers
"""

import json
import os
import logging
import re
import random
import string
import html
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters
)
import httpx

# ============== Configuration ==============
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8131211408:AAEG10mWPCHkIDQXjuKvabYLvTSO3fL1Fms")
ADMIN_IDS = [5139017887]
GITHUB_REPO = "https://github.com/SRRoot/SRRoot-Panel"
DEVELOPER_URL = "https://t.me/SRRoot_Panel"
CF_API = "https://api.cloudflare.com/client/v4"
RAW_GITHUB = "https://raw.githubusercontent.com/SRRoot/SRRoot-Panel/main/srroot.js"

# Mini App URL (deployer web app)
DEPLOYER_URL = os.environ.get("DEPLOYER_URL", "https://srroot-deployer.your-subdomain.workers.dev")

# ============== Database (JSON file) ==============
DB_FILE = "bot_data.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "cloudflare_accounts": {}, "panels": {}, "broadcast_history": []}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# ============== Logging ==============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============== Conversation States ==============
(
    WAITING_CF_TOKEN,
    WAITING_BROADCAST,
    WAITING_DEV_MESSAGE,
    WAITING_CUSTOM_PROXY,
) = range(4)

# ============== Cloudflare API Helpers ==============
async def cf_get_accounts(token):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{CF_API}/accounts",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=30
        )
        return r.json()

async def cf_get_subdomain(token, account_id):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{CF_API}/accounts/{account_id}/workers/subdomain",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=30
        )
        return r.json()

async def cf_create_subdomain(token, account_id, subdomain):
    async with httpx.AsyncClient() as client:
        r = await client.put(
            f"{CF_API}/accounts/{account_id}/workers/subdomain",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"subdomain": subdomain},
            timeout=30
        )
        return r.json()

async def cf_create_d1(token, account_id, name):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{CF_API}/accounts/{account_id}/d1/database",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"name": name},
            timeout=30
        )
        return r.json()

async def cf_deploy_worker(token, account_id, worker_name, code, bindings):
    import io
    metadata = {
        "main_module": "srroot.js",
        "compatibility_date": "2024-02-08",
        "bindings": bindings,
    }
    # Multipart form data
    boundary = "----FormBoundary" + "".join(random.choices(string.ascii_letters, k=16))
    
    body_parts = []
    # Metadata part
    body_parts.append(f"--{boundary}\r\n")
    body_parts.append(f'Content-Disposition: form-data; name="metadata"\r\n')
    body_parts.append(f"Content-Type: application/json\r\n\r\n")
    body_parts.append(json.dumps(metadata))
    body_parts.append("\r\n")
    # Code part
    body_parts.append(f"--{boundary}\r\n")
    body_parts.append(f'Content-Disposition: form-data; name="srroot.js"; filename="srroot.js"\r\n')
    body_parts.append(f"Content-Type: application/javascript+module\r\n\r\n")
    body_parts.append(code)
    body_parts.append(f"\r\n--{boundary}--\r\n")
    
    body = "".join(body_parts)
    
    async with httpx.AsyncClient() as client:
        r = await client.put(
            f"{CF_API}/accounts/{account_id}/workers/scripts/{worker_name}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            content=body.encode("utf-8"),
            timeout=60
        )
        return r.json()

async def cf_enable_subdomain(token, account_id, worker_name):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{CF_API}/accounts/{account_id}/workers/scripts/{worker_name}/subdomain",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"enabled": True},
            timeout=30
        )
        return r

async def cf_get_workers(token, account_id):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{CF_API}/accounts/{account_id}/workers/scripts",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=30
        )
        return r.json()

async def cf_delete_worker(token, account_id, worker_name):
    async with httpx.AsyncClient() as client:
        r = await client.delete(
            f"{CF_API}/accounts/{account_id}/workers/scripts/{worker_name}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=30
        )
        return r.json()

async def cf_get_bindings(token, account_id, worker_name):
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{CF_API}/accounts/{account_id}/workers/scripts/{worker_name}/bindings",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            timeout=30
        )
        return r.json()

async def cf_query_d1(token, account_id, db_id, sql):
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{CF_API}/accounts/{account_id}/d1/database/{db_id}/query",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"sql": sql},
            timeout=30
        )
        return r.json()

async def get_source_code():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{RAW_GITHUB}?t={int(datetime.now().timestamp())}", timeout=30)
        if r.status_code == 200:
            return r.text
    return None

def get_version_from_code(code):
    match = re.search(r"CURRENT_VERSION\s*=\s*['\"](\d+\.\d+\.\d+)['\"]", code)
    if match:
        return match.group(1)
    return "Unknown"

def is_admin(user_id):
    return user_id in ADMIN_IDS

def gen_suffix():
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=6))

# ============== Handler Functions ==============

async def start_command(update: Update, context):
    user = update.effective_user
    db = load_db()
    uid = str(user.id)
    
    if uid not in db["users"]:
        db["users"][uid] = {
            "username": user.username or "",
            "first_name": user.first_name or "",
            "registered_at": datetime.now().isoformat(),
            "cf_accounts": [],
            "panels": [],
        }
        save_db(db)
    
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context):
    query = update.callback_query
    if query:
        await query.answer()
        msg = query.message
    else:
        msg = update.message

    text = (
        "⚡ *خوش آمدید به ربات SRRoot Panel* ⚡\n\n"
        "🛠 مدیریت و ساخت پنل‌های حرفه‌ای روی کلودفلر\n"
        "🔥 روزانه ۱۰ الی ۱۰۰ گیگ کانفیگ رایگان\n\n"
        "از منوی زیر عملیات مورد نظر خود را انتخاب کنید:"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔑 ثبت اکانت کلودفلر", callback_data="register_cf")],
        [InlineKeyboardButton("🚀 ساخت پنل جدید", callback_data="build_panel")],
        [InlineKeyboardButton("📋 مدیریت پنل‌ها", callback_data="manage_panels")],
        [InlineKeyboardButton("🌐 وب دیپلویِر (Mini App)", web_app=WebAppInfo(url=DEPLOYER_URL))],
        [InlineKeyboardButton("🔗 پروکسی اختصاصی", callback_data="custom_proxy")],
        [InlineKeyboardButton("📦 سورس گیت‌هاب", url=GITHUB_REPO)],
        [InlineKeyboardButton("💬 پیام به سازنده", callback_data="dev_message")],
    ]
    
    if is_admin(update.effective_user.id):
        keyboard.append([InlineKeyboardButton("👑 پنل ادمین", callback_data="admin_panel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await msg.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await msg.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ---- Register Cloudflare Account ----
async def register_cf_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    # Send CF token creation link
    token_url = (
        "https://dash.cloudflare.com/profile/api-tokens?"
        "permissionGroupKeys=%5B%7B%22key%22%3A%22workers_scripts%22%2C%22type%22%3A%22edit%22%7D%2C"
        "%7B%22key%22%3A%22workers_kv_storage%22%2C%22type%22%3A%22edit%22%7D%2C"
        "%7B%22key%22%3A%22d1%22%2C%22type%22%3A%22edit%22%7D%2C"
        "%7B%22key%22%3A%22account_settings%22%2C%22type%22%3A%22read%22%7D%2C"
        "%7B%22key%22%3A%22workers_subdomain%22%2C%22type%22%3A%22edit%22%7D%2C"
        "%7B%22key%22%3A%22account_analytics%22%2C%22type%22%3A%22read%22%7D%5D"
        "&accountId=*&zoneId=all&name=SRRoot-Bot-Token"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔑 دریافت توکن کلودفلر", url=token_url)],
        [InlineKeyboardButton("❌ لغو", callback_data="main_menu")],
    ]
    
    await query.message.reply_text(
        "🔑 *ثبت اکانت کلودفلر*\n\n"
        "۱. روی دکمه زیر کلیک کنید\n"
        "۲. در صفحه کلودفلر روی `Continue to summary` کلیک کنید\n"
        "۳. توکن ساخته شده را کپی کنید و اینجا بفرستید\n\n"
        "⚠️ توکن شما امن نگهداری می‌شود",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return WAITING_CF_TOKEN

async def receive_cf_token(update: Update, context):
    token = update.message.text.strip()
    user_id = str(update.effective_user.id)
    
    if not token.startswith("cfut_") and not token.startswith("v1."):
        await update.message.reply_text(
            "❌ توکن نامعتبر است. لطفاً توکن را دقیقاً کپی کنید.\n"
            "توکن باید با `cfut_` یا `v1.` شروع شود.",
            parse_mode="Markdown"
        )
        return WAITING_CF_TOKEN
    
    # Verify token
    status_msg = await update.message.reply_text("⏳ در حال بررسی توکن...")
    
    try:
        acc_data = await cf_get_accounts(token)
        if not acc_data.get("success") or len(acc_data.get("result", [])) == 0:
            await status_msg.edit_text(
                "❌ توکن نامعتبر یا بدون دسترسی.\n"
                "لطفاً فقط با دکمه «دریافت توکن» اقدام کنید."
            )
            return WAITING_CF_TOKEN
        
        account_id = acc_data["result"][0]["id"]
        account_name = acc_data["result"][0].get("name", "Unnamed")
        
        # Save to DB
        db = load_db()
        acc_key = f"{user_id}_{account_id}"
        db["cloudflare_accounts"][acc_key] = {
            "user_id": user_id,
            "account_id": account_id,
            "account_name": account_name,
            "token": token,
            "registered_at": datetime.now().isoformat(),
        }
        if acc_key not in db["users"][user_id].get("cf_accounts", []):
            db["users"][user_id].setdefault("cf_accounts", []).append(acc_key)
        save_db(db)
        
        keyboard = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]
        await status_msg.edit_text(
            f"✅ *اکانت کلودفلر با موفقیت ثبت شد!*\n\n"
            f"📛 نام اکانت: `{account_name}`\n"
            f"🆔 شناسه: `{account_id[:8]}...`\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ خطا در بررسی توکن:\n`{str(e)[:200]}`", parse_mode="Markdown")
    
    return ConversationHandler.END

# ---- Build Panel ----
async def build_panel_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    
    db = load_db()
    user_accounts = db["users"].get(user_id, {}).get("cf_accounts", [])
    
    if not user_accounts:
        keyboard = [
            [InlineKeyboardButton("🔑 ثبت اکانت کلودفلر", callback_data="register_cf")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
        ]
        await query.message.reply_text(
            "❌ ابتدا باید یک اکانت کلودفلر ثبت کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    keyboard = []
    for acc_key in user_accounts:
        acc = db["cloudflare_accounts"].get(acc_key, {})
        name = acc.get("account_name", "Unknown")
        keyboard.append([InlineKeyboardButton(f"📦 {name}", callback_data=f"build_on_{acc_key}")])
    keyboard.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")])
    
    await query.message.reply_text(
        "🚀 *ساخت پنل جدید*\n\n"
        "اکانت کلودفلر مورد نظر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def build_on_account(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    acc_key = query.data.replace("build_on_", "")
    user_id = str(query.from_user.id)
    
    db = load_db()
    acc = db["cloudflare_accounts"].get(acc_key)
    if not acc:
        await query.message.reply_text("❌ اکانت یافت نشد.")
        return
    
    status_msg = await query.message.reply_text(
        "⏳ *در حال ساخت پنل...*\n\n"
        "۱. ⏳ بررسی توکن...\n"
        "۲. ⬜ ایجاد دیتابیس D1\n"
        "۳. ⬜ دریافت سورس\n"
        "۴. ⬜ دیپلوی ورکر\n"
        "۵. ⬜ فعال‌سازی لینک",
        parse_mode="Markdown"
    )
    
    try:
        token = acc["token"]
        account_id = acc["account_id"]
        
        # Step 1: Verify
        acc_data = await cf_get_accounts(token)
        if not acc_data.get("success"):
            await status_msg.edit_text("❌ توکن نامعتبر. لطفاً دوباره ثبت کنید.")
            return
        
        # Step 2: Get/create subdomain
        sub_data = await cf_get_subdomain(token, account_id)
        if sub_data.get("success") and sub_data.get("result", {}).get("subdomain"):
            dev_sub = sub_data["result"]["subdomain"]
        else:
            new_sub = f"srroot-{gen_suffix()}"
            create_sub = await cf_create_subdomain(token, account_id, new_sub)
            if not create_sub.get("success"):
                err = create_sub.get("errors", [{}])[0].get("message", "خطای نامشخص")
                await status_msg.edit_text(f"❌ خطا در ساخت ساب‌دامین: {err}")
                return
            dev_sub = new_sub
        
        await status_msg.edit_text(
            "⏳ *در حال ساخت پنل...*\n\n"
            "۱. ✅ بررسی توکن\n"
            "۲. ⏳ ایجاد دیتابیس D1\n"
            "۳. ⬜ دریافت سورس\n"
            "۴. ⬜ دیپلوی ورکر\n"
            "۵. ⬜ فعال‌سازی لینک",
            parse_mode="Markdown"
        )
        
        # Step 3: Create D1
        suffix = gen_suffix()
        db_name = f"srroot-db-{suffix}"
        db_data = await cf_create_d1(token, account_id, db_name)
        if not db_data.get("success"):
            err = db_data.get("errors", [{}])[0].get("message", "خطای نامشخص")
            await status_msg.edit_text(f"❌ خطا در ساخت دیتابیس: {err}")
            return
        db_uuid = db_data["result"]["uuid"]
        
        import asyncio
        await asyncio.sleep(1)
        
        await status_msg.edit_text(
            "⏳ *در حال ساخت پنل...*\n\n"
            "۱. ✅ بررسی توکن\n"
            "۲. ✅ ایجاد دیتابیس D1\n"
            "۳. ⏳ دریافت سورس\n"
            "۴. ⬜ دیپلوی ورکر\n"
            "۵. ⬜ فعال‌سازی لینک",
            parse_mode="Markdown"
        )
        
        # Step 4: Get source code
        code = await get_source_code()
        if not code:
            await status_msg.edit_text("❌ خطا در دریافت سورس از گیت‌هاب.")
            return
        
        # Step 5: Deploy
        worker_name = f"srroot-panel-{suffix}"
        bindings = [
            {"type": "d1", "name": "DB", "id": db_uuid},
            {"type": "secret_text", "name": "CF_API_TOKEN", "text": token},
            {"type": "secret_text", "name": "CF_ACCOUNT_ID", "text": account_id},
        ]
        
        deploy_data = await cf_deploy_worker(token, account_id, worker_name, code, bindings)
        if not deploy_data.get("success"):
            err = deploy_data.get("errors", [{}])[0].get("message", "خطای نامشخص")
            await status_msg.edit_text(f"❌ خطا در دیپلوی: {err}")
            return
        
        await status_msg.edit_text(
            "⏳ *در حال ساخت پنل...*\n\n"
            "۱. ✅ بررسی توکن\n"
            "۲. ✅ ایجاد دیتابیس D1\n"
            "۳. ✅ دریافت سورس\n"
            "۴. ✅ دیپلوی ورکر\n"
            "۵. ⏳ فعال‌سازی لینک",
            parse_mode="Markdown"
        )
        
        # Step 6: Enable subdomain
        route_res = await cf_enable_subdomain(token, account_id, worker_name)
        
        final_url = f"https://{worker_name}.{dev_sub}.workers.dev/panel"
        
        # Save panel info
        db = load_db()
        db["panels"][worker_name] = {
            "user_id": user_id,
            "account_key": acc_key,
            "worker_name": worker_name,
            "db_name": db_name,
            "url": final_url,
            "created_at": datetime.now().isoformat(),
        }
        db["users"][user_id].setdefault("panels", []).append(worker_name)
        save_db(db)
        
        keyboard = [
            [InlineKeyboardButton("🌐 ورود به پنل", url=final_url)],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
        ]
        
        await status_msg.edit_text(
            "✅ *پنل با موفقیت ساخته شد!*\n\n"
            f"📛 نام: `{worker_name}`\n"
            f"🔗 لینک:\n`{final_url}`\n\n"
            "⏰ لطفاً ۵ دقیقه صبر کنید و سپس وارد شوید.\n"
            "🔒 رمز عبور را در اولین ورود تنظیم کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        await status_msg.edit_text(f"❌ خطای غیرمنتظره:\n`{str(e)[:300]}`", parse_mode="Markdown")

# ---- Manage Panels ----
async def manage_panels_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    
    db = load_db()
    panels = db["users"].get(user_id, {}).get("panels", [])
    
    if not panels:
        keyboard = [
            [InlineKeyboardButton("🚀 ساخت پنل جدید", callback_data="build_panel")],
            [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
        ]
        await query.message.reply_text(
            "📋 هیچ پنلی یافت نشد.\nمی‌توانید یک پنل جدید بسازید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Get latest version
    code = await get_source_code()
    latest_ver = get_version_from_code(code) if code else "Unknown"
    
    text = f"📋 *پنل‌های شما*\n\nنسخه آخر: `v{latest_ver}`\n\n"
    keyboard = []
    
    for p_name in panels:
        p_info = db["panels"].get(p_name, {})
        url = p_info.get("url", "#")
        text += f"📦 `{p_name}`\n"
        
        keyboard.append([
            InlineKeyboardButton(f"🔧 {p_name[:20]}", callback_data=f"panel_actions_{p_name}"),
        ])
    
    keyboard.append([InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")])
    
    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def panel_actions_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    panel_name = query.data.replace("panel_actions_", "")
    db = load_db()
    p_info = db["panels"].get(panel_name, {})
    
    keyboard = [
        [InlineKeyboardButton("🌐 ورود به پنل", url=p_info.get("url", "#"))],
        [InlineKeyboardButton("🔄 آپدیت پنل", callback_data=f"update_panel_{panel_name}")],
        [InlineKeyboardButton("🔑 بازیابی رمز", callback_data=f"reset_pwd_{panel_name}")],
        [InlineKeyboardButton("🔃 ری‌استارت", callback_data=f"restart_panel_{panel_name}")],
        [InlineKeyboardButton("🗑 حذف پنل", callback_data=f"delete_panel_{panel_name}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="manage_panels")],
    ]
    
    await query.message.reply_text(
        f"🔧 *مدیریت پنل*\n\n📦 `{panel_name}`\n📅 ساخت: {p_info.get('created_at', '?')[:10]}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def update_panel_action(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    panel_name = query.data.replace("update_panel_", "")
    status_msg = await query.message.reply_text(f"⏳ در حال آپدیت `{panel_name}`...", parse_mode="Markdown")
    
    db = load_db()
    p_info = db["panels"].get(panel_name, {})
    acc_key = p_info.get("account_key", "")
    acc = db["cloudflare_accounts"].get(acc_key, {})
    
    if not acc:
        await status_msg.edit_text("❌ اکانت کلودفلر یافت نشد.")
        return
    
    try:
        token = acc["token"]
        account_id = acc["account_id"]
        
        # Get latest code
        code = await get_source_code()
        if not code:
            await status_msg.edit_text("❌ خطا در دریافت سورس.")
            return
        
        # Get current bindings
        bindings_data = await cf_get_bindings(token, account_id, panel_name)
        if not bindings_data.get("success"):
            await status_msg.edit_text("❌ خطا در دریافت تنظیمات.")
            return
        
        new_bindings = []
        for b in bindings_data["result"]:
            if b["type"] == "d1":
                new_bindings.append({"type": "d1", "name": b["name"], "id": b.get("database_id") or b.get("id")})
            elif b["name"] == "CF_API_TOKEN":
                new_bindings.append({"type": "secret_text", "name": "CF_API_TOKEN", "text": token})
            elif b["name"] == "CF_ACCOUNT_ID":
                new_bindings.append({"type": "secret_text", "name": "CF_ACCOUNT_ID", "text": account_id})
        
        deploy_data = await cf_deploy_worker(token, account_id, panel_name, code, new_bindings)
        
        if deploy_data.get("success"):
            ver = get_version_from_code(code)
            await status_msg.edit_text(
                f"✅ پنل `{panel_name}` با موفقیت آپدیت شد!\n📌 نسخه: `v{ver}`",
                parse_mode="Markdown"
            )
        else:
            err = deploy_data.get("errors", [{}])[0].get("message", "خطای نامشخص")
            await status_msg.edit_text(f"❌ خطا در آپدیت: {err}")
    except Exception as e:
        await status_msg.edit_text(f"❌ خطا: {str(e)[:200]}")

async def reset_pwd_action(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    panel_name = query.data.replace("reset_pwd_", "")
    status_msg = await query.message.reply_text(f"⏳ در حال بازیابی رمز `{panel_name}`...", parse_mode="Markdown")
    
    db = load_db()
    p_info = db["panels"].get(panel_name, {})
    acc_key = p_info.get("account_key", "")
    acc = db["cloudflare_accounts"].get(acc_key, {})
    
    if not acc:
        await status_msg.edit_text("❌ اکانت یافت نشد.")
        return
    
    try:
        token = acc["token"]
        account_id = acc["account_id"]
        
        # Get bindings to find D1
        bindings_data = await cf_get_bindings(token, account_id, panel_name)
        if not bindings_data.get("success"):
            await status_msg.edit_text("❌ خطا در دریافت تنظیمات.")
            return
        
        db_binding = None
        for b in bindings_data["result"]:
            if b["type"] == "d1":
                db_binding = b
                break
        
        if not db_binding:
            await status_msg.edit_text("❌ دیتابیس یافت نشد.")
            return
        
        db_id = db_binding.get("database_id") or db_binding.get("id")
        
        # Delete password
        query_res = await cf_query_d1(token, account_id, db_id, "DELETE FROM settings WHERE key = 'panel_password'")
        
        if query_res.get("success"):
            await status_msg.edit_text(
                f"✅ رمز عبور پنل `{panel_name}` بازنشانی شد.\n"
                "اکنون می‌توانید با رمز جدید وارد شوید.",
                parse_mode="Markdown"
            )
        else:
            await status_msg.edit_text("❌ خطا در بازیابی رمز.")
    except Exception as e:
        await status_msg.edit_text(f"❌ خطا: {str(e)[:200]}")

async def restart_panel_action(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    panel_name = query.data.replace("restart_panel_", "")
    # Restart = re-deploy same code
    await update_panel_action(update, context)

async def delete_panel_action(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    panel_name = query.data.replace("delete_panel_", "")
    
    keyboard = [
        [
            InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"confirm_del_{panel_name}"),
            InlineKeyboardButton("❌ انصراف", callback_data=f"panel_actions_{panel_name}"),
        ]
    ]
    
    await query.message.reply_text(
        f"⚠️ *هشدار!*\n\nآیا از حذف پنل `{panel_name}` مطمئن هستید؟\n"
        "این عمل قابل بازگشت نیست!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def confirm_delete_action(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    panel_name = query.data.replace("confirm_del_", "")
    status_msg = await query.message.reply_text(f"⏳ در حال حذف `{panel_name}`...", parse_mode="Markdown")
    
    user_id = str(query.from_user.id)
    db = load_db()
    p_info = db["panels"].get(panel_name, {})
    acc_key = p_info.get("account_key", "")
    acc = db["cloudflare_accounts"].get(acc_key, {})
    
    if not acc:
        await status_msg.edit_text("❌ اکانت یافت نشد.")
        return
    
    try:
        token = acc["token"]
        account_id = acc["account_id"]
        
        del_data = await cf_delete_worker(token, account_id, panel_name)
        
        if del_data.get("success"):
            # Remove from DB
            if panel_name in db.get("panels", {}):
                del db["panels"][panel_name]
            if user_id in db.get("users", {}):
                if panel_name in db["users"][user_id].get("panels", []):
                    db["users"][user_id]["panels"].remove(panel_name)
            save_db(db)
            
            keyboard = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]
            await status_msg.edit_text(
                f"✅ پنل `{panel_name}` حذف شد.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            err = del_data.get("errors", [{}])[0].get("message", "خطای نامشخص")
            await status_msg.edit_text(f"❌ خطا: {err}")
    except Exception as e:
        await status_msg.edit_text(f"❌ خطا: {str(e)[:200]}")

# ---- Custom Proxy ----
async def custom_proxy_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "🌐 *پروکسی اختصاصی*\n\n"
        "اگر سرور VPS دارید، می‌توانید پروکسی SOCKS5 اختصاصی بسازید:\n\n"
        "```\n"
        "bash <(curl -Ls https://raw.githubusercontent.com/SRRoot/SRRoot-Panel/main/zeus-relay.sh | sed 's/\\r$//')\n"
        "```\n\n"
        "این اسکریپت را روی سرور لینوکس خود اجرا کنید.",
        parse_mode="Markdown"
    )

# ---- Developer Message ----
async def dev_message_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "💬 *پیام به سازنده*\n\n"
        "پیام خود را ارسال کنید تا به دست سازنده برسد.\n"
        "یا مستقیم به کانال ما بپیوندید:",
        parse_mode="Markdown"
    )
    return WAITING_DEV_MESSAGE

async def receive_dev_message(update: Update, context):
    message = update.message.text
    user = update.effective_user
    
    # Forward to admin
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"💬 *پیام از کاربر:*\n\n"
                f"👤 نام: {html.escape(user.first_name or '')}\n"
                f"🆔 آیدی: `{user.id}`\n"
                f"📛 یوزرنیم: @{user.username or 'N/A'}\n\n"
                f"📝 پیام:\n{html.escape(message)}",
                parse_mode="Markdown"
            )
        except:
            pass
    
    keyboard = [[InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]]
    await update.message.reply_text(
        "✅ پیام شما ارسال شد. با تشکر!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

# ---- Admin Panel ----
async def admin_panel_callback(update: Update, context):
    query = update.callback_query
    
    if not is_admin(query.from_user.id):
        await query.answer("⛔ دسترسی ندارید!", show_alert=True)
        return
    
    await query.answer()
    db = load_db()
    
    total_users = len(db.get("users", {}))
    total_panels = len(db.get("panels", {}))
    total_cf_accounts = len(db.get("cloudflare_accounts", {}))
    
    keyboard = [
        [InlineKeyboardButton("📢 برادکست (ارسال همگانی)", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 لیست کاربران", callback_data="admin_user_list")],
        [InlineKeyboardButton("📊 آمار کلی", callback_data="admin_stats")],
        [InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")],
    ]
    
    await query.message.reply_text(
        f"👑 *پنل مدیریت ادمین*\n\n"
        f"👥 کل کاربران: `{total_users}`\n"
        f"📦 کل پنل‌ها: `{total_panels}`\n"
        f"🔑 اکانت‌های CF: `{total_cf_accounts}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_broadcast_callback(update: Update, context):
    query = update.callback_query
    
    if not is_admin(query.from_user.id):
        await query.answer("⛔", show_alert=True)
        return
    
    await query.answer()
    await query.message.reply_text(
        "📢 *پیام برادکست*\n\n"
        "پیام خود را ارسال کنید تا به همه کاربران فرستاده شود:",
        parse_mode="Markdown"
    )
    return WAITING_BROADCAST

async def receive_broadcast(update: Update, context):
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END
    
    message = update.message.text
    db = load_db()
    
    sent = 0
    failed = 0
    
    status_msg = await update.message.reply_text("⏳ در حال ارسال برادکست...")
    
    for uid in db.get("users", {}):
        try:
            await context.bot.send_message(
                int(uid),
                f"📢 *پیام مدیریت SRRoot*\n\n{html.escape(message)}",
                parse_mode="Markdown"
            )
            sent += 1
        except:
            failed += 1
    
    db.setdefault("broadcast_history", []).append({
        "message": message[:100],
        "sent": sent,
        "failed": failed,
        "date": datetime.now().isoformat(),
    })
    save_db(db)
    
    keyboard = [[InlineKeyboardButton("👑 پنل ادمین", callback_data="admin_panel")]]
    await status_msg.edit_text(
        f"✅ برادکست ارسال شد!\n\n"
        f"✅ موفق: `{sent}`\n"
        f"❌ ناموفق: `{failed}`",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def admin_stats_callback(update: Update, context):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔", show_alert=True)
        return
    await query.answer()
    
    db = load_db()
    total_users = len(db.get("users", {}))
    total_panels = len(db.get("panels", {}))
    total_cf = len(db.get("cloudflare_accounts", {}))
    broadcasts = len(db.get("broadcast_history", []))
    
    await query.message.reply_text(
        f"📊 *آمار کلی SRRoot*\n\n"
        f"👥 کاربران: `{total_users}`\n"
        f"📦 پنل‌ها: `{total_panels}`\n"
        f"🔑 اکانت‌های CF: `{total_cf}`\n"
        f"📢 برادکست‌ها: `{broadcasts}`\n"
        f"📅 آخرین بروزرسانی: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        parse_mode="Markdown"
    )

async def admin_user_list_callback(update: Update, context):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔", show_alert=True)
        return
    await query.answer()
    
    db = load_db()
    users = db.get("users", {})
    
    text = "👥 *لیست کاربران*\n\n"
    count = 0
    for uid, uinfo in list(users.items())[:30]:
        count += 1
        uname = uinfo.get("username", "N/A")
        fname = uinfo.get("first_name", "N/A")
        panels = len(uinfo.get("panels", []))
        text += f"{count}. `{fname}` (@{uname}) - پنل‌ها: {panels}\n"
    
    if len(users) > 30:
        text += f"\n... و {len(users) - 30} کاربر دیگر"
    
    await query.message.reply_text(text, parse_mode="Markdown")

# ---- Cancel Handler ----
async def cancel_handler(update: Update, context):
    await update.message.reply_text("❌ عملیات لغو شد.")
    return ConversationHandler.END

# ============== Main ==============
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation handler for CF token registration
    cf_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(register_cf_callback, pattern="^register_cf$")],
        states={
            WAITING_CF_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_cf_token)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
    )
    
    # Conversation handler for developer message
    dev_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(dev_message_callback, pattern="^dev_message$")],
        states={
            WAITING_DEV_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_dev_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
    )
    
    # Conversation handler for admin broadcast
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_callback, pattern="^admin_broadcast$")],
        states={
            WAITING_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_broadcast)],
        },
        fallbacks=[CommandHandler("cancel", cancel_handler)],
    )
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(cf_conv)
    app.add_handler(dev_conv)
    app.add_handler(broadcast_conv)
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(show_main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(build_panel_callback, pattern="^build_panel$"))
    app.add_handler(CallbackQueryHandler(build_on_account, pattern="^build_on_"))
    app.add_handler(CallbackQueryHandler(manage_panels_callback, pattern="^manage_panels$"))
    app.add_handler(CallbackQueryHandler(panel_actions_callback, pattern="^panel_actions_"))
    app.add_handler(CallbackQueryHandler(update_panel_action, pattern="^update_panel_"))
    app.add_handler(CallbackQueryHandler(reset_pwd_action, pattern="^reset_pwd_"))
    app.add_handler(CallbackQueryHandler(restart_panel_action, pattern="^restart_panel_"))
    app.add_handler(CallbackQueryHandler(delete_panel_action, pattern="^delete_panel_"))
    app.add_handler(CallbackQueryHandler(confirm_delete_action, pattern="^confirm_del_"))
    app.add_handler(CallbackQueryHandler(custom_proxy_callback, pattern="^custom_proxy$"))
    app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(admin_stats_callback, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_user_list_callback, pattern="^admin_user_list$"))
    
    logger.info("🚀 SRRoot Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
