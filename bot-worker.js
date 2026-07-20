const BOT_TOKEN = "8131211408:AAEG10mWPCHkIDQXjuKvabYLvTSO3fL1Fms";
const ADMIN_IDS = [5139017887];
const CF_API = "https://api.cloudflare.com/client/v4";
const GITHUB_REPO = "https://github.com/amirparsa1/SRRoot-Panel";
const RAW_GITHUB = "https://raw.githubusercontent.com/amirparsa1/SRRoot-Panel/main/srroot.js";
const DEPLOYER_URL = "https://srroot-deployer.sr-root.workers.dev";
const BOT_API = `https://api.telegram.org/bot${BOT_TOKEN}`;

async function tgApi(method, data) {
    const r = await fetch(`${BOT_API}/${method}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
    });
    return r.json();
}

async function sendMessage(chatId, text, keyboard = null, parseMode = "Markdown") {
    const msg = { chat_id: chatId, text, parse_mode: parseMode };
    if (keyboard) msg.reply_markup = JSON.stringify({ inline_keyboard: keyboard });
    return tgApi("sendMessage", msg);
}

async function editMessage(chatId, messageId, text, keyboard = null, parseMode = "Markdown") {
    const msg = { chat_id: chatId, message_id: messageId, text, parse_mode: parseMode };
    if (keyboard) msg.reply_markup = JSON.stringify({ inline_keyboard: keyboard });
    return tgApi("editMessageText", msg);
}

async function answerCallback(queryId, text = "") {
    return tgApi("answerCallbackQuery", { callback_query_id: queryId, text });
}

// ========== DB Helpers ==========
async function getDB(kv) {
    const data = await kv.get("bot_data", "json");
    return data || { users: {}, cf_accounts: {}, panels: {} };
}

async function saveDB(kv, db) {
    await kv.put("bot_data", JSON.stringify(db));
}

// ========== CF API Helpers ==========
async function cfRequest(token, path, method = "GET", body = null) {
    const opts = {
        method,
        headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
    };
    if (body) opts.body = JSON.stringify(body);
    const r = await fetch(`${CF_API}${path}`, opts);
    return r.json();
}

async function getSourceCode() {
    const r = await fetch(`${RAW_GITHUB}?t=${Date.now()}`);
    return r.ok ? r.text() : null;
}

function getVersion(code) {
    const m = code.match(/CURRENT_VERSION\s*=\s*['"](\d+\.\d+\.\d+)['"]/i);
    return m ? m[1] : "Unknown";
}

function genSuffix() {
    return Math.random().toString(36).substring(2, 8);
}

// ========== Token URL ==========
const CF_TOKEN_URL = "https://dash.cloudflare.com/profile/api-tokens?permissionGroupKeys=%5B%7B%22key%22%3A%22workers_scripts%22%2C%22type%22%3A%22edit%22%7D%2C%7B%22key%22%3A%22workers_kv_storage%22%2C%22type%22%3A%22edit%22%7D%2C%7B%22key%22%3A%22d1%22%2C%22type%22%3A%22edit%22%7D%2C%7B%22key%22%3A%22account_settings%22%2C%22type%22%3A%22read%22%7D%2C%7B%22key%22%3A%22workers_subdomain%22%2C%22type%22%3A%22edit%22%7D%2C%7B%22key%22%3A%22account_analytics%22%2C%22type%22%3A%22read%22%7D%5D&accountId=*&zoneId=all&name=SRRoot-Bot-Token";

// ========== Main Menu ==========
function mainMenu(userId) {
    const kb = [
        [{ text: "🔑 ثبت اکانت کلودفلر", callback_data: "register_cf" }],
        [{ text: "🚀 ساخت پنل جدید", callback_data: "build_panel" }],
        [{ text: "📋 مدیریت پنل‌ها", callback_data: "manage_panels" }],
        [{ text: "🌐 وب دیپلویِر", web_app: { url: DEPLOYER_URL } }],
        [{ text: "🔗 پروکسی اختصاصی", callback_data: "custom_proxy" }],
        [{ text: "📦 سورس گیت‌هاب", url: GITHUB_REPO }],
        [{ text: "💬 پیام به سازنده", callback_data: "dev_message" }],
    ];
    if (ADMIN_IDS.includes(userId)) {
        kb.push([{ text: "👑 پنل ادمین", callback_data: "admin_panel" }]);
    }
    return kb;
}

const WELCOME = "⚡ *خوش آمدید به ربات SRRoot Panel* ⚡\n\n🛠 مدیریت و ساخت پنل‌های حرفه‌ای روی کلودفلر
📢 کانال: @SR_Panel\n🔥 روزانه ۱۰ الی ۱۰۰ گیگ کانفیگ رایگان\n\nاز منوی زیر عملیات مورد نظر را انتخاب کنید:";

// ========== Handlers ==========
async function handleStart(chatId, userId, kv) {
    const db = await getDB(kv);
    if (!db.users[userId]) {
        db.users[userId] = { registered_at: new Date().toISOString(), cf_accounts: [], panels: [] };
        await saveDB(kv, db);
    }
    await sendMessage(chatId, WELCOME, mainMenu(userId));
}

async function handleCallback(query, kv) {
    const { id: queryId, data, message, from } = query;
    const chatId = message.chat.id;
    const msgId = message.message_id;
    const userId = from.id;

    if (data === "main_menu") {
        await answerCallback(queryId);
        await editMessage(chatId, msgId, WELCOME, mainMenu(userId));
        return;
    }

    if (data === "register_cf") {
        await answerCallback(queryId);
        const kb = [
            [{ text: "🔑 دریافت توکن کلودفلر", url: CF_TOKEN_URL }],
            [{ text: "❌ لغو", callback_data: "main_menu" }],
        ];
        await sendMessage(chatId,
            "🔑 *ثبت اکانت کلودفلر*\n\n" +
            "۱. روی دکمه زیر کلیک کنید\n" +
            "۲. در صفحه کلودفلر `Continue to summary` را بزنید\n" +
            "۳. توکن ساخته شده را کپی و اینجا بفرستید\n\n" +
            "⚠️ توکن شما امن نگهداری می‌شود", kb);
        // Set user state
        const db = await getDB(kv);
        db.users[userId] = db.users[userId] || { cf_accounts: [], panels: [] };
        db.users[userId].state = "waiting_cf_token";
        await saveDB(kv, db);
        return;
    }

    if (data === "build_panel") {
        await answerCallback(queryId);
        const db = await getDB(kv);
        const accs = (db.users[userId] || {}).cf_accounts || [];
        if (accs.length === 0) {
            const kb = [
                [{ text: "🔑 ثبت اکانت کلودفلر", callback_data: "register_cf" }],
                [{ text: "🏠 منوی اصلی", callback_data: "main_menu" }],
            ];
            await editMessage(chatId, msgId, "❌ ابتدا باید یک اکانت کلودفلر ثبت کنید.", kb);
            return;
        }
        const kb = accs.map(ak => {
            const acc = db.cf_accounts[ak] || {};
            return [{ text: `📦 ${acc.account_name || "Account"}`, callback_data: `build_on_${ak}` }];
        });
        kb.push([{ text: "🏠 منوی اصلی", callback_data: "main_menu" }]);
        await editMessage(chatId, msgId, "🚀 *ساخت پنل جدید*\n\nاکانت کلودفلر مورد نظر را انتخاب کنید:", kb);
        return;
    }

    if (data.startsWith("build_on_")) {
        await answerCallback(queryId, "در حال ساخت...");
        const accKey = data.replace("build_on_", "");
        const db = await getDB(kv);
        const acc = db.cf_accounts[accKey];
        if (!acc) { await sendMessage(chatId, "❌ اکانت یافت نشد."); return; }

        const statusMsg = await sendMessage(chatId,
            "⏳ *در حال ساخت پنل...*\n\n۱. ⏳ بررسی توکن...\n۲. ⬜ ایجاد دیتابیس D1\n۳. ⬜ دریافت سورس\n۴. ⬜ دیپلوی ورکر\n۵. ⬜ فعال‌سازی لینک");

        try {
            const token = acc.token;
            const accountId = acc.account_id;

            // Step 1: Verify
            const accData = await cfRequest(token, "/accounts");
            if (!accData.success) {
                await tgApi("editMessageText", { chat_id: chatId, message_id: statusMsg.result.message_id, text: "❌ توکن نامعتبر." });
                return;
            }

            // Step 2: Subdomain
            let subData = await cfRequest(token, `/accounts/${accountId}/workers/subdomain`);
            let devSub;
            if (subData.success && subData.result && subData.result.subdomain) {
                devSub = subData.result.subdomain;
            } else {
                const newSub = `srroot-${genSuffix()}`;
                const cs = await cfRequest(token, `/accounts/${accountId}/workers/subdomain`, "PUT", { subdomain: newSub });
                if (!cs.success) {
                    await tgApi("editMessageText", { chat_id: chatId, message_id: statusMsg.result.message_id, text: "❌ خطا در ساخت ساب‌دامین." });
                    return;
                }
                devSub = newSub;
            }

            await tgApi("editMessageText", { chat_id: chatId, message_id: statusMsg.result.message_id, text: "⏳ *در حال ساخت پنل...*\n\n۱. ✅ بررسی توکن\n۲. ⏳ ایجاد دیتابیس D1\n۳. ⬜ دریافت سورس\n۴. ⬜ دیپلوی ورکر\n۵. ⬜ فعال‌سازی لینک", parse_mode: "Markdown" });

            // Step 3: Create D1
            const suffix = genSuffix();
            const dbName = `srroot-db-${suffix}`;
            const dbData = await cfRequest(token, `/accounts/${accountId}/d1/database`, "POST", { name: dbName });
            if (!dbData.success) {
                await tgApi("editMessageText", { chat_id: chatId, message_id: statusMsg.result.message_id, text: `❌ خطا در ساخت دیتابیس: ${(dbData.errors||[{}])[0].message}` });
                return;
            }
            const dbUuid = dbData.result.uuid;

            await new Promise(r => setTimeout(r, 1000));

            await tgApi("editMessageText", { chat_id: chatId, message_id: statusMsg.result.message_id, text: "⏳ *در حال ساخت پنل...*\n\n۱. ✅ بررسی توکن\n۲. ✅ ایجاد دیتابیس D1\n۳. ⏳ دریافت سورس\n۴. ⬜ دیپلوی ورکر\n۵. ⬜ فعال‌سازی لینک", parse_mode: "Markdown" });

            // Step 4: Get source
            const code = await getSourceCode();
            if (!code) {
                await tgApi("editMessageText", { chat_id: chatId, message_id: statusMsg.result.message_id, text: "❌ خطا در دریافت سورس." });
                return;
            }

            // Step 5: Deploy worker
            const workerName = `srroot-panel-${suffix}`;
            const metadata = {
                main_module: "srroot.js",
                compatibility_date: "2024-02-08",
                bindings: [
                    { type: "d1", name: "DB", id: dbUuid },
                    { type: "secret_text", name: "CF_API_TOKEN", text: token },
                    { type: "secret_text", name: "CF_ACCOUNT_ID", text: accountId },
                ],
            };

            const boundary = "----FormBoundary" + genSuffix() + genSuffix();
            const bodyParts = [];
            bodyParts.push(`--${boundary}\r\nContent-Disposition: form-data; name="metadata"\r\nContent-Type: application/json\r\n\r\n${JSON.stringify(metadata)}\r\n`);
            bodyParts.push(`--${boundary}\r\nContent-Disposition: form-data; name="srroot.js"; filename="srroot.js"\r\nContent-Type: application/javascript+module\r\n\r\n${code}\r\n--${boundary}--\r\n`);
            const body = bodyParts.join("");

            const deployRes = await fetch(`https://api.cloudflare.com/client/v4/accounts/${accountId}/workers/scripts/${workerName}`, {
                method: "PUT",
                headers: { "Authorization": `Bearer ${token}`, "Content-Type": `multipart/form-data; boundary=${boundary}` },
                body: body,
            });
            const deployData = await deployRes.json();
            if (!deployData.success) {
                await tgApi("editMessageText", { chat_id: chatId, message_id: statusMsg.result.message_id, text: `❌ خطا در دیپلوی: ${(deployData.errors||[{}])[0].message}` });
                return;
            }

            await tgApi("editMessageText", { chat_id: chatId, message_id: statusMsg.result.message_id, text: "⏳ *در حال ساخت پنل...*\n\n۱. ✅ بررسی توکن\n۲. ✅ ایجاد D1\n۳. ✅ دریافت سورس\n۴. ✅ دیپلوی ورکر\n۵. ⏳ فعال‌سازی لینک", parse_mode: "Markdown" });

            // Step 6: Enable subdomain
            await fetch(`https://api.cloudflare.com/client/v4/accounts/${accountId}/workers/scripts/${workerName}/subdomain`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}`, "Content-Type": "application/json" },
                body: JSON.stringify({ enabled: true }),
            });

            const finalUrl = `https://${workerName}.${devSub}.workers.dev/panel`;

            // Save panel
            db.panels[workerName] = { user_id: String(userId), account_key: accKey, worker_name: workerName, url: finalUrl, created_at: new Date().toISOString() };
            db.users[userId] = db.users[userId] || { cf_accounts: [], panels: [] };
            db.users[userId].panels = db.users[userId].panels || [];
            db.users[userId].panels.push(workerName);
            await saveDB(kv, db);

            const kb = [
                [{ text: "🌐 ورود به پنل", url: finalUrl }],
                [{ text: "🏠 منوی اصلی", callback_data: "main_menu" }],
            ];
            await tgApi("editMessageText", {
                chat_id: chatId, message_id: statusMsg.result.message_id,
                text: `✅ *پنل با موفقیت ساخته شد!*\n\n📛 نام: \`${workerName}\`\n🔗 لینک:\n\`${finalUrl}\`\n\n⏰ ۵ دقیقه صبر کنید سپس وارد شوید.\n🔒 رمز عبور را در اولین ورود تنظیم کنید.`,
                parse_mode: "Markdown",
                reply_markup: JSON.stringify({ inline_keyboard: kb }),
            });

        } catch (e) {
            await tgApi("editMessageText", { chat_id: chatId, message_id: statusMsg.result.message_id, text: `❌ خطا: ${e.message}` });
        }
        return;
    }

    if (data === "manage_panels") {
        await answerCallback(queryId);
        const db = await getDB(kv);
        const panels = (db.users[userId] || {}).panels || [];
        if (panels.length === 0) {
            const kb = [
                [{ text: "🚀 ساخت پنل جدید", callback_data: "build_panel" }],
                [{ text: "🏠 منوی اصلی", callback_data: "main_menu" }],
            ];
            await editMessage(chatId, msgId, "📋 هیچ پنلی یافت نشد.", kb);
            return;
        }
        const code = await getSourceCode();
        const latestVer = code ? getVersion(code) : "Unknown";
        let text = `📋 *پنل‌های شما*\n\nنسخه آخر: \`v${latestVer}\`\n\n`;
        const kb = panels.map(p => [{ text: `🔧 ${p}`, callback_data: `panel_act_${p}` }]);
        kb.push([{ text: "🏠 منوی اصلی", callback_data: "main_menu" }]);
        await editMessage(chatId, msgId, text, kb);
        return;
    }

    if (data.startsWith("panel_act_")) {
        await answerCallback(queryId);
        const pName = data.replace("panel_act_", "");
        const db = await getDB(kv);
        const pInfo = db.panels[pName] || {};
        const kb = [
            [{ text: "🌐 ورود به پنل", url: pInfo.url || "#" }],
            [{ text: "🔄 آپدیت", callback_data: `upd_${pName}` }],
            [{ text: "🔑 بازیابی رمز", callback_data: `rpwd_${pName}` }],
            [{ text: "🗑 حذف پنل", callback_data: `delp_${pName}` }],
            [{ text: "🔙 بازگشت", callback_data: "manage_panels" }],
        ];
        await editMessage(chatId, msgId, `🔧 *مدیریت پنل*\n\n📦 \`${pName}\`\n📅 ساخت: ${(pInfo.created_at||"?").substring(0,10)}`, kb);
        return;
    }

    if (data.startsWith("upd_")) {
        await answerCallback(queryId, "در حال آپدیت...");
        const pName = data.replace("upd_", "");
        const db = await getDB(kv);
        const pInfo = db.panels[pName] || {};
        const acc = db.cf_accounts[pInfo.account_key];
        if (!acc) { await sendMessage(chatId, "❌ اکانت یافت نشد."); return; }

        const code = await getSourceCode();
        if (!code) { await sendMessage(chatId, "❌ خطا در دریافت سورس."); return; }

        const bindingsData = await cfRequest(acc.token, `/accounts/${acc.account_id}/workers/scripts/${pName}/bindings`);
        if (!bindingsData.success) { await sendMessage(chatId, "❌ خطا."); return; }

        const newBindings = [];
        for (const b of (bindingsData.result || [])) {
            if (b.type === "d1") newBindings.push({ type: "d1", name: b.name, id: b.database_id || b.id });
            else if (b.name === "CF_API_TOKEN") newBindings.push({ type: "secret_text", name: "CF_API_TOKEN", text: acc.token });
            else if (b.name === "CF_ACCOUNT_ID") newBindings.push({ type: "secret_text", name: "CF_ACCOUNT_ID", text: acc.account_id });
        }

        const metadata = { main_module: "srroot.js", compatibility_date: "2024-02-08", bindings: newBindings };
        const boundary = "----FB" + genSuffix() + genSuffix();
        const bodyParts = [];
        bodyParts.push(`--${boundary}\r\nContent-Disposition: form-data; name="metadata"\r\nContent-Type: application/json\r\n\r\n${JSON.stringify(metadata)}\r\n`);
        bodyParts.push(`--${boundary}\r\nContent-Disposition: form-data; name="srroot.js"; filename="srroot.js"\r\nContent-Type: application/javascript+module\r\n\r\n${code}\r\n--${boundary}--\r\n`);

        const deployRes = await fetch(`https://api.cloudflare.com/client/v4/accounts/${acc.account_id}/workers/scripts/${pName}`, {
            method: "PUT",
            headers: { "Authorization": `Bearer ${acc.token}`, "Content-Type": `multipart/form-data; boundary=${boundary}` },
            body: bodyParts.join(""),
        });
        const deployData = await deployRes.json();
        const ver = getVersion(code);
        if (deployData.success) {
            await sendMessage(chatId, `✅ پنل \`${pName}\` آپدیت شد!\n📌 نسخه: \`v${ver}\``);
        } else {
            await sendMessage(chatId, `❌ خطا: ${(deployData.errors||[{}])[0].message}`);
        }
        return;
    }

    if (data.startsWith("rpwd_")) {
        await answerCallback(queryId, "در حال بازیابی رمز...");
        const pName = data.replace("rpwd_", "");
        const db = await getDB(kv);
        const pInfo = db.panels[pName] || {};
        const acc = db.cf_accounts[pInfo.account_key];
        if (!acc) { await sendMessage(chatId, "❌ اکانت یافت نشد."); return; }

        const bindingsData = await cfRequest(acc.token, `/accounts/${acc.account_id}/workers/scripts/${pName}/bindings`);
        const dbBinding = (bindingsData.result || []).find(b => b.type === "d1");
        if (!dbBinding) { await sendMessage(chatId, "❌ D1 یافت نشد."); return; }
        const dbId = dbBinding.database_id || dbBinding.id;
        const qRes = await cfRequest(acc.token, `/accounts/${acc.account_id}/d1/database/${dbId}/query`, "POST", { sql: "DELETE FROM settings WHERE key = 'panel_password'" });
        if (qRes.success) {
            await sendMessage(chatId, `✅ رمز پنل \`${pName}\` بازنشانی شد.`);
        } else {
            await sendMessage(chatId, "❌ خطا در بازیابی رمز.");
        }
        return;
    }

    if (data.startsWith("delp_")) {
        await answerCallback(queryId);
        const pName = data.replace("delp_", "");
        const kb = [
            [{ text: "✅ بله حذف شود", callback_data: `confdel_${pName}` }, { text: "❌ انصراف", callback_data: `panel_act_${pName}` }],
        ];
        await editMessage(chatId, msgId, `⚠️ *هشدار!*\n\nآیا از حذف \`${pName}\` مطمئنید؟`, kb);
        return;
    }

    if (data.startsWith("confdel_")) {
        await answerCallback(queryId, "در حال حذف...");
        const pName = data.replace("confdel_", "");
        const db = await getDB(kv);
        const pInfo = db.panels[pName] || {};
        const acc = db.cf_accounts[pInfo.account_key];
        if (!acc) { await sendMessage(chatId, "❌ اکانت یافت نشد."); return; }

        const delRes = await cfRequest(acc.token, `/accounts/${acc.account_id}/workers/scripts/${pName}`, "DELETE");
        if (delRes.success) {
            delete db.panels[pName];
            if (db.users[userId]) {
                db.users[userId].panels = (db.users[userId].panels || []).filter(p => p !== pName);
            }
            await saveDB(kv, db);
            const kb = [[{ text: "🏠 منوی اصلی", callback_data: "main_menu" }]];
            await editMessage(chatId, msgId, `✅ پنل \`${pName}\` حذف شد.`, kb);
        } else {
            await sendMessage(chatId, `❌ خطا: ${(delRes.errors||[{}])[0].message}`);
        }
        return;
    }

    if (data === "custom_proxy") {
        await answerCallback(queryId);
        await sendMessage(chatId,
            "🌐 *پروکسی اختصاصی*\n\n" +
            "برای ساخت SOCKS5 روی VPS:\n\n" +
            "`bash <(curl -Ls https://raw.githubusercontent.com/amirparsa1/SRRoot-Panel/main/srroot-relay.sh | sed 's/\\r$//')`");
        return;
    }

    if (data === "dev_message") {
        await answerCallback(queryId);
        const db = await getDB(kv);
        db.users[userId] = db.users[userId] || { cf_accounts: [], panels: [] };
        db.users[userId].state = "waiting_dev_msg";
        await saveDB(kv, db);
        await sendMessage(chatId, "💬 پیام خود را ارسال کنید:");
        return;
    }

    // ========== Admin ==========
    if (data === "admin_panel") {
        if (!ADMIN_IDS.includes(userId)) { await answerCallback(queryId, "⛔"); return; }
        await answerCallback(queryId);
        const db = await getDB(kv);
        const nu = Object.keys(db.users || {}).length;
        const np = Object.keys(db.panels || {}).length;
        const nc = Object.keys(db.cf_accounts || {}).length;
        const kb = [
            [{ text: "📢 برادکست", callback_data: "admin_bc" }],
            [{ text: "👥 لیست کاربران", callback_data: "admin_users" }],
            [{ text: "📊 آمار", callback_data: "admin_stats" }],
            [{ text: "🏠 منوی اصلی", callback_data: "main_menu" }],
        ];
        await editMessage(chatId, msgId,
            `👑 *پنل ادمین*\n\n👥 کاربران: \`${nu}\`\n📦 پنل‌ها: \`${np}\`\n🔑 اکانت CF: \`${nc}\``, kb);
        return;
    }

    if (data === "admin_bc") {
        if (!ADMIN_IDS.includes(userId)) { await answerCallback(queryId, "⛔"); return; }
        await answerCallback(queryId);
        const db = await getDB(kv);
        db.users[userId] = db.users[userId] || { cf_accounts: [], panels: [] };
        db.users[userId].state = "waiting_broadcast";
        await saveDB(kv, db);
        await sendMessage(chatId, "📢 پیام برادکست را ارسال کنید:");
        return;
    }

    if (data === "admin_stats") {
        if (!ADMIN_IDS.includes(userId)) { await answerCallback(queryId, "⛔"); return; }
        await answerCallback(queryId);
        const db = await getDB(kv);
        const nu = Object.keys(db.users || {}).length;
        const np = Object.keys(db.panels || {}).length;
        const nc = Object.keys(db.cf_accounts || {}).length;
        await sendMessage(chatId,
            `📊 *آمار SRRoot*\n\n👥 کاربران: \`${nu}\`\n📦 پنل‌ها: \`${np}\`\n🔑 اکانت CF: \`${nc}\``);
        return;
    }

    if (data === "admin_users") {
        if (!ADMIN_IDS.includes(userId)) { await answerCallback(queryId, "⛔"); return; }
        await answerCallback(queryId);
        const db = await getDB(kv);
        let text = "👥 *لیست کاربران*\n\n";
        let i = 0;
        for (const [uid, uinfo] of Object.entries(db.users || {})) {
            if (i >= 30) break;
            i++;
            const panels = (uinfo.panels || []).length;
            text += `${i}. \`${uid}\` - پنل‌ها: ${panels}\n`;
        }
        await sendMessage(chatId, text);
        return;
    }

    await answerCallback(queryId);
}

// ========== Main Worker ==========
export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        // Webhook endpoint
        if (url.pathname === "/webhook" && request.method === "POST") {
            const update = await request.json();
            const kv = env.BOT_KV;

            // Handle message
            if (update.message) {
                const msg = update.message;
                const chatId = msg.chat.id;
                const userId = msg.from.id;
                const text = msg.text || "";

                if (text === "/start") {
                    await handleStart(chatId, userId, kv);
                    return new Response("OK");
                }

                // Check user state
                const db = await getDB(kv);
                const userState = (db.users[userId] || {}).state;

                if (userState === "waiting_cf_token") {
                    const token = text.trim();
                    if (!token.startsWith("cfut_") && !token.startsWith("v1.")) {
                        await sendMessage(chatId, "❌ توکن نامعتبر. توکن باید با `cfut_` شروع شود.");
                        return new Response("OK");
                    }

                    const accData = await cfRequest(token, "/accounts");
                    if (!accData.success || !accData.result || accData.result.length === 0) {
                        await sendMessage(chatId, "❌ توکن نامعتبر یا بدون دسترسی.");
                        return new Response("OK");
                    }

                    const accountId = accData.result[0].id;
                    const accountName = accData.result[0].name || "Account";
                    const accKey = `${userId}_${accountId}`;

                    db.cf_accounts[accKey] = { user_id: String(userId), account_id: accountId, account_name: accountName, token: token };
                    db.users[userId] = db.users[userId] || { cf_accounts: [], panels: [] };
                    db.users[userId].cf_accounts = db.users[userId].cf_accounts || [];
                    if (!db.users[userId].cf_accounts.includes(accKey)) {
                        db.users[userId].cf_accounts.push(accKey);
                    }
                    delete db.users[userId].state;
                    await saveDB(kv, db);

                    const kb = [[{ text: "🏠 منوی اصلی", callback_data: "main_menu" }]];
                    await sendMessage(chatId,
                        `✅ *اکانت ثبت شد!*\n\n📛 نام: \`${accountName}\`\n🆔 شناسه: \`${accountId.substring(0,8)}...\``, kb);
                    return new Response("OK");
                }

                if (userState === "waiting_dev_msg") {
                    for (const adminId of ADMIN_IDS) {
                        try {
                            await sendMessage(adminId,
                                `💬 *پیام از کاربر:*\n\n👤 آیدی: \`${userId}\`\n\n📝 پیام:\n${text}`);
                        } catch(e) {}
                    }
                    delete db.users[userId].state;
                    await saveDB(kv, db);
                    const kb = [[{ text: "🏠 منوی اصلی", callback_data: "main_menu" }]];
                    await sendMessage(chatId, "✅ پیام ارسال شد!", kb);
                    return new Response("OK");
                }

                if (userState === "waiting_broadcast") {
                    if (!ADMIN_IDS.includes(userId)) { return new Response("OK"); }
                    let sent = 0, failed = 0;
                    for (const uid of Object.keys(db.users || {})) {
                        try {
                            await sendMessage(parseInt(uid), `📢 *پیام مدیریت SRRoot*\n\n${text}`);
                            sent++;
                        } catch(e) { failed++; }
                    }
                    delete db.users[userId].state;
                    await saveDB(kv, db);
                    await sendMessage(chatId, `✅ برادکست ارسال شد!\n✅ موفق: \`${sent}\`\n❌ ناموفق: \`${failed}\``);
                    return new Response("OK");
                }
            }

            // Handle callback query
            if (update.callback_query) {
                await handleCallback(update.callback_query, env.BOT_KV);
                return new Response("OK");
            }

            return new Response("OK");
        }

        // Set webhook endpoint
        if (url.pathname === "/set-webhook") {
            const workerUrl = `${new URL(request.url).origin}/webhook`;
            const r = await fetch(`${BOT_API}/setWebhook`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: workerUrl, allowed_updates: ["message", "callback_query"] }),
            });
            const data = await r.json();
            return new Response(JSON.stringify(data), { headers: { "Content-Type": "application/json" } });
        }

        // Info page
        if (url.pathname === "/" || url.pathname === "") {
            return new Response(`
<!DOCTYPE html><html><head><title>SRRoot Bot</title>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:sans-serif;background:#0a0118;color:#fff;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}
.card{background:#0f0728;border:1px solid #2d1b69;border-radius:20px;padding:40px;text-align:center;max-width:400px}
h1{color:#06b6d4;margin:0 0 10px}p{color:#a78bfa}</style></head>
<body><div class="card"><h1>⚡ SRRoot Bot</h1><p>ربات مدیریت پنل SRRoot</p>
<a href="https://t.me/srroot_bot" style="color:#8b5cf6;text-decoration:none;font-size:18px">🤖 باز کردن ربات</a></div></body></html>`,
            { headers: { "Content-Type": "text/html;charset=UTF-8" } });
        }

        return new Response("Not Found", { status: 404 });
    },
};
