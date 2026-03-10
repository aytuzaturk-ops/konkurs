from aiogram.types import WebAppInfo
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from datetime import datetime

import database as db

router = Router()


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="🏆 Top 100")],
            [KeyboardButton(text="👥 Do'stlarim"), KeyboardButton(text="🔗 Referal link")],
            [KeyboardButton(text="🌐 Web App", web_app=WebAppInfo(url="https://yourusername.github.io/konkurs-webapp"))],
        ],
        resize_keyboard=True
    )


async def check_subscriptions(bot: Bot, user_id: int):
    channels = await db.get_channels()
    not_subscribed = []
    for channel in channels:
        try:
            member = await bot.get_chat_member(channel["channel_id"], user_id)
            if member.status in ["left", "kicked", "banned"]:
                not_subscribed.append(channel)
        except Exception:
            not_subscribed.append(channel)
    return len(not_subscribed) == 0, not_subscribed


async def subscription_keyboard(channels):
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(text=f"📢 {ch['channel_name']}", url=ch["channel_link"])])
    buttons.append([InlineKeyboardButton(text="✅ A'zo bo'ldim", callback_data="check_subscription")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name

    referrer_id = None
    args = message.text.split()
    if len(args) > 1:
        try:
            ref_id = int(args[1].replace("ref_", ""))
            if ref_id != user_id:
                referrer = await db.get_user(ref_id)
                if referrer:
                    referrer_id = ref_id
        except ValueError:
            pass

    channels = await db.get_channels()
    if not channels:
        await message.answer(
            "👋 <b>Xush kelibsiz!</b>\n\nBot sozlanmoqda. Tez orada konkurs boshlanadi!",
            parse_mode="HTML"
        )
        return

    all_subscribed, not_subscribed = await check_subscriptions(bot, user_id)

    if not all_subscribed:
        existing_user = await db.get_user(user_id)
        if not existing_user:
            await db.create_user(user_id, username, full_name, referrer_id)

        kb = await subscription_keyboard(not_subscribed)
        await message.answer(
            "👋 <b>Xush kelibsiz!</b>\n\n"
            "Konkursda ishtirok etish uchun quyidagi kanallarga a'zo bo'ling:\n\n"
            "A'zo bo'lgach, <b>\"✅ A'zo bo'ldim\"</b> tugmasini bosing.",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    existing_user = await db.get_user(user_id)
    if not existing_user:
        await db.create_user(user_id, username, full_name, referrer_id)
        existing_user = None

    contest_active = await db.get_contest_status()
    if not contest_active:
        await message.answer(
            "✅ <b>Kanallarga a'zo bo'lgansiz!</b>\n\n"
            "⏳ Konkurs hali boshlanmagan. Tez orada e'lon qilinadi!",
            parse_mode="HTML"
        )
        return

    await process_verified_user(message, bot, user_id, referrer_id, existing_user)


@router.callback_query(F.data == "check_subscription")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id

    all_subscribed, not_subscribed = await check_subscriptions(bot, user_id)

    if not all_subscribed:
        kb = await subscription_keyboard(not_subscribed)
        await callback.message.edit_text(
            "❌ <b>Siz hali barcha kanallarga a'zo bo'lmagansiz!</b>\n\n"
            "Quyidagi kanallarga a'zo bo'lib qayta tekshiring:",
            reply_markup=kb,
            parse_mode="HTML"
        )
        await callback.answer("❌ Avval barcha kanallarga a'zo bo'ling!", show_alert=True)
        return

    contest_active = await db.get_contest_status()
    if not contest_active:
        await callback.message.edit_text(
            "✅ <b>Kanallarga a'zo bo'lgansiz!</b>\n\n"
            "⏳ Konkurs hali boshlanmagan. Tez orada e'lon qilinadi!",
            parse_mode="HTML"
        )
        await callback.answer("✅ Obuna tasdiqlandi!")
        return

    existing_user = await db.get_user(user_id)
    referrer_id = existing_user["referrer_id"] if existing_user else None

    await callback.message.delete()
    await process_verified_user(callback.message, bot, user_id, referrer_id, existing_user, send_new=True)
    await callback.answer("✅ Tekshiruv muvaffaqiyatli!")


async def process_verified_user(message, bot: Bot, user_id: int, referrer_id, existing_user, send_new=False):
    user = await db.get_user(user_id)
    referrals = await db.get_user_referrals(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    if referrer_id and existing_user is None:
        await db.add_points(referrer_id, 1)
        try:
            await bot.send_message(
                referrer_id,
                "🎉 <b>Yangi referal!</b>\n\nSizning havolangiz orqali yangi ishtirokchi qo'shildi. +1 ball oldiniz! 🏆",
                parse_mode="HTML"
            )
        except Exception:
            pass

    # Deadline ma'lumoti
    deadline_str = await db.get_deadline()
    deadline_text = ""
    if deadline_str:
        deadline = datetime.fromisoformat(deadline_str)
        deadline_text = f"\n⏰ <b>Konkurs tugashi:</b> {deadline.strftime('%d.%m.%Y %H:%M')}\n"

    text = (
        f"🎉 <b>Tabriklaymiz! Siz ro'yxatdan o'tdingiz!</b>\n\n"
        f"🆔 <b>Sizning ID:</b> <code>{user_id}</code>\n"
        f"⭐ <b>Ballar:</b> {user['points'] if user else 0}\n"
        f"👥 <b>Taklif qilganlar:</b> {len(referrals)} kishi\n"
        f"{deadline_text}\n"
        f"🔗 <b>Sizning referal havolangiz:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"👆 Havolani do'stlaringizga yuboring va har bir yangi a'zo uchun <b>+1 ball</b> oling!"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="my_stats")],
        [InlineKeyboardButton(text="👥 Do'stlarim ro'yxati", callback_data="my_referrals")],
        [InlineKeyboardButton(text="🏆 Top 100 reyting", callback_data="top_100")],
    ])

    if send_new:
        await bot.send_message(user_id, text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "my_stats")
async def my_stats(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    referrals = await db.get_user_referrals(user_id)
    all_users = await db.get_all_users()
    rank = next((i + 1 for i, u in enumerate(all_users) if u["telegram_id"] == user_id), "?")
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    deadline_str = await db.get_deadline()
    deadline_text = ""
    if deadline_str:
        deadline = datetime.fromisoformat(deadline_str)
        now = datetime.now()
        diff = deadline - now
        if diff.total_seconds() > 0:
            days = diff.days
            hours = diff.seconds // 3600
            deadline_text = f"\n⏰ Tugashiga: <b>{days} kun {hours} soat</b> qoldi\n"

    text = (
        f"📊 <b>Sizning statistikangiz</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"⭐ Ballar: <b>{user['points']}</b>\n"
        f"👥 Referal soni: <b>{len(referrals)}</b>\n"
        f"🏆 Reyting: <b>{rank}-o'rin</b> ({len(all_users)} ta ichida)\n"
        f"{deadline_text}\n"
        f"🔗 Referal link:\n<code>{ref_link}</code>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Top 100", callback_data="top_100")],
        [InlineKeyboardButton(text="« Orqaga", callback_data="back_main")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "my_referrals")
async def my_referrals(callback: CallbackQuery):
    user_id = callback.from_user.id
    referrals = await db.get_user_referrals(user_id)

    if not referrals:
        text = "👥 <b>Do'stlarim ro'yxati</b>\n\nSiz hali hech kimni taklif qilmagansiz."
    else:
        lines = [f"👥 <b>Do'stlarim ro'yxati ({len(referrals)} kishi):</b>\n"]
        for i, ref in enumerate(referrals, 1):
            name = ref["full_name"] or ref["username"] or "Nomsiz"
            lines.append(f"{i}. {name}")
        text = "\n".join(lines)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Orqaga", callback_data="back_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "top_100")
async def top_100(callback: CallbackQuery):
    user_id = callback.from_user.id
    top_users = await db.get_top_users(100)
    all_users = await db.get_all_users()
    user_rank = next((i + 1 for i, u in enumerate(all_users) if u["telegram_id"] == user_id), None)

    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
   lines = [f"🏆 <b>Top {min(100, len(top_users))} Reyting</b>\n"]

    for i, u in enumerate(top_users, 1):
        name = u["full_name"] or u["username"] or "Nomsiz"
        if len(name) > 20:
            name = name[:18] + ".."
        medal = medals.get(i, f"{i}.")
        marker = " ◀️" if u["telegram_id"] == user_id else ""
        lines.append(f"{medal} {name} — {u['points']} ball{marker}")  # ← Bu qator BORMIKAN?

    if user_rank and user_rank > 100:
        lines.append(f"\n...\n🔸 Sizning o'rningiz: {user_rank}-o'rin")

    text = "\n".join(lines)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Orqaga", callback_data="back_main")]
    ])

    # Xabar uzun bo'lishi mumkin, edit_text ishlamasligi mumkin
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_main(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    user = await db.get_user(user_id)
    referrals = await db.get_user_referrals(user_id)
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    deadline_str = await db.get_deadline()
    deadline_text = ""
    if deadline_str:
        deadline = datetime.fromisoformat(deadline_str)
        deadline_text = f"\n⏰ <b>Tugashi:</b> {deadline.strftime('%d.%m.%Y %H:%M')}\n"

    text = (
        f"🏠 <b>Bosh sahifa</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"⭐ Ballar: <b>{user['points'] if user else 0}</b>\n"
        f"👥 Referal soni: <b>{len(referrals)}</b>\n"
        f"{deadline_text}\n"
        f"🔗 Referal link:\n<code>{ref_link}</code>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="my_stats")],
        [InlineKeyboardButton(text="👥 Do'stlarim ro'yxati", callback_data="my_referrals")],
        [InlineKeyboardButton(text="🏆 Top 100 reyting", callback_data="top_100")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()
