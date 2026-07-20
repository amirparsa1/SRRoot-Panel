<div align="center">

# ⚡ SRRoot Panel

[![Version](https://img.shields.io/badge/Version-v1.9.8-blue.svg?style=for-the-badge&logo=cloudflare)](https://github.com/SRRoot/SRRoot-Panel)
[![Platform](https://img.shields.io/badge/Platform-Cloudflare%20Workers-f38020.svg?style=for-the-badge&logo=cloudflare&logoColor=white)](https://workers.cloudflare.com/)
[![Database](https://img.shields.io/badge/Database-Cloudflare%20D1%20SQL-F38020.svg?style=for-the-badge&logo=sqlite&logoColor=white)](https://developers.cloudflare.com/d1/)
[![Protocol](https://img.shields.io/badge/Protocol-VLESS%20%2F%20WebSocket-06b6d4.svg?style=for-the-badge)](https://github.com/SRRoot/SRRoot-Panel)
[![Telegram](https://img.shields.io/badge/Telegram-SRRoot__Panel-2CA5E0.svg?style=for-the-badge&logo=telegram)](https://t.me/SRRoot_Panel)

**یک پنل مدیریت پراکسی حرفه‌ای و چندکاربره با طراحی اختصاصی، مستقر روی لبه‌ی شبکه‌ی Cloudflare Workers و D1 Serverless SQL.**

[ویژگی‌ها](#️-ویژگی‌ها) • [دیپلوی سریع](#-دیپلوی-سریع) • [ربات تلگرام](#-ربات-تلگرام) • [وب دیپلویِر](#-وب-دیپلویِر)

</div>

---

## ⚡️ ویژگی‌ها

* 🌐 **IP ثابت و جغرافیای دلخواه:** امکان اتصال IP ثابت یا کشورهای خاص به هر کاربر
* 👥 **مدیریت پیشرفته کاربران:** محدودیت ترافیک (GB)، زمان (روز)، تعداد درخواست و تعداد دستگاه همزمان
* ♻️ **ریست خودکار:** بازتاب خودکار شمارنده‌ها بر اساس بازه‌های زمانی مشخص
* 🛠 **عملیات گروهی:** ابزارهای چندانتخابی برای ویرایش، حذف و ریست گروهی
* 🛡 **مکانیزم‌های ضد فیلترینگ:** پشتیبانی از TLS Fragment و شبیه‌ساز ClientHello Fingerprint
* 📱 **رابط کاربری اختصاصی:** طراحی مدرن و ریسپانسیو با تم AMOLED و رنگ‌بندی Cyan/Violet
* 📡 **مسیردهی پراکسی سفارشی:** پشتیبانی از زنجیره پراکسی و پروکسی‌های VIP
* 🌐 **چرخش IP پویا:** تغییر خودکار IP‌های تمیز Cloudflare با بازه‌های دلخواه
* 📊 **مانیتورینگ زنده:** ردیابی لحظه‌ای درخواست‌ها برای جلوگیری از بن
* 🔗 **لینک‌های خودکار:** تولید خودکار لینک سابسکریپشن، QR Code و صفحات وضعیت
* 🔄 **آپدیت OTA:** بروزرسانی خودکار مستقیم از گیت‌هاب بدون از دست رفتن اطلاعات
* 🗄 **سیستم بکاپ:** خروجی و ورودی کامل JSON از دیتابیس و تنظیمات
* 🤖 **ربات تلگرام:** مدیریت کامل از طریق تلگرام با قابلیت Mini App
* 🌐 **وب دیپلویِر:** نصب پنل تنها با یک کلیک

---

## 🚀 دیپلوی سریع

<div align="center">

### روش ۱: ربات تلگرام (پیشنهادی)

<a href="https://t.me/SRRoot_Panel_Bot" target="_blank">
<img src="https://img.shields.io/badge/شروع_ربات_SRRoot-0088cc?style=for-the-badge&logo=telegram&logoColor=white" alt="SRRoot Bot" height="40">
</a>

### روش ۲: وب دیپلویِر

<a href="https://srroot-deployer.workers.dev" target="_blank">
<img src="https://img.shields.io/badge/SRRoot_Deployer-06b6d4?style=for-the-badge&logo=cloudflare&logoColor=white" alt="Deploy" height="40">
</a>

</div>

---

## 🤖 ربات تلگرام

ربات تلگرام SRRoot امکان مدیریت کامل پنل‌ها را از طریق تلگرام فراهم می‌کند:

### قابلیت‌ها:
- 🔑 **ثبت اکانت کلودفلر** - اتصال اکانت CF به ربات
- 🚀 **ساخت پنل جدید** - دیپلوی خودکار پنل روی CF Workers
- 📋 **مدیریت پنل‌ها** - لیست، آپدیت، ری‌استارت، بازیابی رمز، حذف
- 🌐 **پروکسی اختصاصی** - راهنمای ساخت SOCKS5
- 💬 **پیام به سازنده** - ارتباط مستقیم
- 📦 **سورس گیت‌هاب** - دسترسی سریع
- 👑 **پنل ادمین** - برادکست، آمار، مدیریت کاربران

### نصب ربات:
```bash
cd bot
pip install -r requirements.txt
python bot.py
```

### متغیرهای محیطی:
| متغیر | توضیح |
|---|---|
| `BOT_TOKEN` | توکن ربات تلگرام |
| `DEPLOYER_URL` | آدرس وب دیپلویِر |

---

## 🌐 وب دیپلویِر

وب دیپلویِر یک Cloudflare Worker است که صفحه‌ی نصب گرافیکی را فراهم می‌کند.

فایل `deployer/deployer.js` را به عنوان یک Worker جدید روی Cloudflare دیپلوی کنید.

### ویژگی‌ها:
- نصب پنل با یک کلیک
- مدیریت و آپدیت پنل‌های موجود
- بازیابی رمز عبور
- ری‌استارت پنل
- حذف پنل
- رابط کاربری اختصاصی SRRoot

---

## 📁 ساختار پروژه

```
SRRoot-Panel/
├── srroot.js              # سورس اصلی پنل (Cloudflare Worker)
├── ips.txt                # لیست IP‌های Cloudflare
├── proxy/                 # فایل‌های پراکسی عمومی
├── proxy_vip/             # فایل‌های پراکسی VIP
├── deployer/
│   └── deployer.js        # وب دیپلویِر (Cloudflare Worker)
├── bot/
│   ├── bot.py             # ربات تلگرام
│   └── requirements.txt   # وابستگی‌های پایتون
├── README.md              # راهنمای پروژه
└── LICENSE                # مجوز
```

---

## ⚖️ مجوز

**کلیه حقوق محفوظ است © 2026 SRRoot Contributors**

این نرم‌افزار صرفاً برای استفاده **شخصی و غیرتجاری** ارائه شده است.

---

<p align="center">ساخته شده با ❤️ توسط تیم SRRoot</p>
