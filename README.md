<div align="center">

# ⚡ SRRoot Panel

[![Version](https://img.shields.io/badge/Version-v1.9.8-06b6d4.svg?style=for-the-badge&logo=cloudflare)](https://github.com/amirparsa1/SRRoot-Panel)
[![Platform](https://img.shields.io/badge/Platform-Cloudflare%20Workers-f38020.svg?style=for-the-badge&logo=cloudflare&logoColor=white)](https://workers.cloudflare.com/)
[![Database](https://img.shields.io/badge/Database-Cloudflare%20D1%20SQL-8b5cf6.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://developers.cloudflare.com/d1/)
[![Protocol](https://img.shields.io/badge/Protocol-VLESS%20%2F%20WebSocket-06b6d4.svg?style=for-the-badge)](https://github.com/amirparsa1/SRRoot-Panel)
[![Telegram](https://img.shields.io/badge/Channel-SR__Panel-2CA5E0.svg?style=for-the-badge&logo=telegram)](https://t.me/SR_Panel)
[![Bot](https://img.shields.io/badge/Bot-srroot__Bot-8b5cf6.svg?style=for-the-badge&logo=telegram)](https://t.me/srroot_bot)

**یک پنل مدیریت پراکسی حرفه‌ای و چندکاربره با طراحی اختصاصی، مستقر روی لبه‌ی شبکه‌ی Cloudflare Workers و D1 Serverless SQL.**

[ویژگی‌ها](#️-ویژگی‌ها) • [دیپلوی سریع](#-دیپلوی-سریع) • [ربات تلگرام](#-ربات-تلگرام) • [وب دیپلویِر](#-وب-دیپلویِر)

---

### 🤖 ربات تلگرام: [@srroot_bot](https://t.me/srroot_bot)
### 📢 کانال: [@SR_Panel](https://t.me/SR_Panel)

</div>

---

## ⚡️ ویژگی‌ها

| ویژگی | توضیح |
|---|---|
| 🌐 **IP ثابت و جغرافیا** | اتصال IP ثابت یا کشورهای خاص به هر کاربر |
| 👥 **مدیریت کاربران** | محدودیت ترافیک (GB)، زمان (روز)، درخواست و دستگاه همزمان |
| ♻️ **ریست خودکار** | بازنشانی خودکار شمارنده‌ها بر اساس بازه زمانی |
| 🛠 **عملیات گروهی** | ویرایش، حذف و ریست گروهی کاربران |
| 🛡 **ضد فیلترینگ** | TLS Fragment و شبیه‌ساز ClientHello Fingerprint |
| 🎨 **UI اختصاصی** | تم AMOLED با رنگ‌بندی Cyan/Violet |
| 📡 **پراکسی سفارشی** | زنجیره پراکسی و پروکسی‌های VIP |
| 🌐 **چرخش IP پویا** | تغییر خودکار IP‌های تمیز با بازه دلخواه |
| 📊 **مانیتورینگ زنده** | ردیابی لحظه‌ای درخواست‌ها |
| 🔗 **لینک خودکار** | سابسکریپشن، QR Code و صفحات وضعیت |
| 🔄 **آپدیت OTA** | بروزرسانی خودکار از گیت‌هاب بدون از دست رفتن اطلاعات |
| 🗄 **بکاپ کامل** | خروجی/ورودی JSON از دیتابیس و تنظیمات |
| 🤖 **ربات تلگرام** | مدیریت کامل + Mini App |

---

## 🚀 دیپلوی سریع

<div align="center">

| روش | لینک |
|---|---|
| 🤖 **ربات تلگرام** | [@srroot_bot](https://t.me/srroot_bot) → ثبت اکانت → ساخت پنل |
| 🌐 **وب دیپلویِر** | [srroot-deployer.sr-root.workers.dev](https://srroot-deployer.sr-root.workers.dev) |

</div>

### مراحل دیپلوی:

1. وارد [ربات تلگرام](https://t.me/srroot_bot) یا [وب دیپلویِر](https://srroot-deployer.sr-root.workers.dev) شوید
2. توکن کلودفلر را دریافت کنید (دکمه نارنجی)
3. در کلودفلر `Continue to summary` → `Create Token`
4. توکن را وارد کنید
5. ⚡ پنل شما در کمتر از ۱ دقیقه آماده می‌شود!

> ⚠️ **رمز عبور اولیه** را حتماً جایی ذخیره کنید!

---

## 🤖 ربات تلگرام

<div align="center">

| دستورات | توضیح |
|---|---|
| `/start` | ⚡ منوی اصلی |
| `/build` | 🚀 ساخت پنل جدید |
| `/panels` | 📋 مدیریت پنل‌ها |
| `/register` | 🔑 ثبت اکانت کلودفلر |
| `/proxy` | 🔗 پروکسی اختصاصی |
| `/source` | 📦 سورس گیت‌هاب |
| `/support` | 💬 پیام به سازنده |
| `/help` | ❓ راهنما |

</div>

### قابلیت‌های ربات:
- 🔑 **ثبت اکانت کلودفلر** با لینک مستقیم ساخت توکن
- 🚀 **ساخت پنل** با انتخاب اکانت CF
- 📋 **مدیریت پنل‌ها** (آپدیت/بازیابی رمز/ری‌استارت/حذف)
- 🌐 **دکمه Mini App** برای وب دیپلویِر
- 🔗 **پروکسی اختصاصی** (راهنمای ساخت SOCKS5)
- 💬 **پیام به سازنده**
- 👑 **پنل ادمین** (برادکست + آمار + لیست کاربران)

---

## 🌐 وب دیپلویِر

**آدرس:** `https://srroot-deployer.sr-root.workers.dev`

- ✅ نصب پنل با یک کلیک
- ✅ مدیریت و آپدیت پنل‌های موجود
- ✅ بازیابی رمز عبور
- ✅ ری‌استارت و حذف پنل
- ✅ رابط کاربری اختصاصی SRRoot

---

## 📁 ساختار پروژه

```
SRRoot-Panel/
├── srroot.js              # سورس اصلی پنل (Cloudflare Worker)
├── ips.txt                # لیست IP‌های Cloudflare
├── proxy/                 # فایل‌های پراکسی عمومی (۱۰۰+ کشور)
├── proxy_vip/             # فایل‌های پراکسی VIP
├── srroot-relay.sh        # اسکریپت ساخت SOCKS5
├── bot-worker.js          # ربات تلگرام (Cloudflare Worker)
├── bot/
│   ├── bot.py             # ربات تلگرام (Python - جایگزین)
│   └── requirements.txt
├── deployer/
│   └── deployer.js        # وب دیپلویِر (Cloudflare Worker)
├── logo.png               # لوگوی اصلی
├── bot-avatar.png         # آواتار ربات
├── README.md
└── LICENSE
```

---

## 🔗 لینک‌ها

| آیتم | لینک |
|---|---|
| 📢 **کانال تلگرام** | [@SR_Panel](https://t.me/SR_Panel) |
| 🤖 **ربات تلگرام** | [@srroot_bot](https://t.me/srroot_bot) |
| 📦 **گیت‌هاب** | [amirparsa1/SRRoot-Panel](https://github.com/amirparsa1/SRRoot-Panel) |
| 🌐 **وب دیپلویِر** | [srroot-deployer](https://srroot-deployer.sr-root.workers.dev) |

---

## ⚖️ مجوز

**کلیه حقوق محفوظ است © 2026 SRRoot Contributors**

استفاده **شخصی و غیرتجاری**. بدون فروش، تغییر یا توزیع مجدد.

---

<div align="center">

### ساخته شده با ❤️ توسط تیم SRRoot

📢 [@SR_Panel](https://t.me/SR_Panel) • 🤖 [@srroot_bot](https://t.me/srroot_bot)

</div>
