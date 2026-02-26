from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import ADMIN_IDS

router = Router()

# ===== STATES =====
class AdminStates(StatesGroup):
    adding_channel_id = State()
    adding_channel_name = State()
    adding_channel_link = State()
    removing_channel = State()
    searching_user = State()
    editing_user_points = State()
    editing_user_id = State()
    broadcasting = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def admin_only(func):
    async def wrapper(message: Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.answer("❌ Sizda admin huquqi yo'q!")
            return
        return await func(message, *args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# ===== ADMIN PANEL =====
def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanallar boshqaruvi", callback_data="admin_channels")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton(text="📣 Xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🏆 Konkurs boshqaruvi", callback_data="admin_contest")],
    ])

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    await message.answer("🛠 <b>Admin Panel</b>\n\nNimani boshqarmoqchisiz?", reply_markup=admin_panel_kb(), parse_mode="HTML")

# ===== CHANNEL MANAGEMENT =====
@router.callback_query(F.data == "admin_channels")
async def admin_channels(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo'q!", show_alert=True)
        return
    
    channels = await db.get_channels()
    text = "📢 <b>Kanallar boshqaruvi</b>\n\n"
    if channels:
        for ch in channels:
            text += f"• {ch['channel_name']} ({ch['channel_id']})\n"
    else:
        text += "Hozircha kanallar yo'q.\n"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")],
        [InlineKeyboardButton(text="🗑 Kanal o'chirish", callback_data="remove_channel")],
        [InlineKeyboardButton(text="« Orqaga", callback_data="back_admin")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "📢 <b>Kanal ID sini kiriting</b>\n\n"
        "Misol: <code>@mychannel</code> yoki <code>-1001234567890</code>\n\n"
        "Bekor qilish: /cancel",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.adding_channel_id)
    await callback.answer()

@router.message(AdminStates.adding_channel_id)
async def add_channel_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(channel_id=message.text.strip())
    await message.answer("✏️ Kanal nomini kiriting (foydalanuvchilarga ko'rinadigan nom):")
    await state.set_state(AdminStates.adding_channel_name)

@router.message(AdminStates.adding_channel_name)
async def add_channel_name(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.update_data(channel_name=message.text.strip())
    await message.answer("🔗 Kanal havolasini kiriting (t.me/...):")
    await state.set_state(AdminStates.adding_channel_link)

@router.message(AdminStates.adding_channel_link)
async def add_channel_link(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    link = message.text.strip()
    if not link.startswith("http"):
        link = "https://" + link
    
    await db.add_channel(data["channel_id"], data["channel_name"], link)
    await state.clear()
    await message.answer(
        f"✅ <b>Kanal qo'shildi!</b>\n\n"
        f"📢 Nom: {data['channel_name']}\n"
        f"🆔 ID: {data['channel_id']}\n"
        f"🔗 Link: {link}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Admin panel", callback_data="back_admin")]
        ])
    )

@router.callback_query(F.data == "remove_channel")
async def remove_channel_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    channels = await db.get_channels()
    if not channels:
        await callback.answer("❌ O'chirish uchun kanallar yo'q!", show_alert=True)
        return
    
    buttons = [[InlineKeyboardButton(text=f"🗑 {ch['channel_name']}", callback_data=f"del_ch_{ch['channel_id']}")] for ch in channels]
    buttons.append([InlineKeyboardButton(text="« Orqaga", callback_data="admin_channels")])
    await callback.message.edit_text("🗑 Qaysi kanalni o'chirmoqchisiz?", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@router.callback_query(F.data.startswith("del_ch_"))
async def delete_channel(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    channel_id = callback.data.replace("del_ch_", "")
    await db.remove_channel(channel_id)
    await callback.answer("✅ Kanal o'chirildi!", show_alert=True)
    channels = await db.get_channels()
    text = "📢 <b>Kanallar boshqaruvi</b>\n\n"
    if channels:
        for ch in channels:
            text += f"• {ch['channel_name']} ({ch['channel_id']})\n"
    else:
        text += "Hozircha kanallar yo'q.\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kanal qo'shish", callback_data="add_channel")],
        [InlineKeyboardButton(text="🗑 Kanal o'chirish", callback_data="remove_channel")],
        [InlineKeyboardButton(text="« Orqaga", callback_data="back_admin")],
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

# ===== USER MANAGEMENT =====
@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    all_users = await db.get_all_users()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📋 Barcha ({len(all_users)} ta)", callback_data="list_all_users")],
        [InlineKeyboardButton(text="🔍 ID bo'yicha qidirish", callback_data="search_user")],
        [InlineKeyboardButton(text="« Orqaga", callback_data="back_admin")],
    ])
    await callback.message.edit_text(
        f"👥 <b>Foydalanuvchilar boshqaruvi</b>\n\nJami ishtirokchilar: <b>{len(all_users)}</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "list_all_users")
async def list_all_users(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    all_users = await db.get_all_users()
    if not all_users:
        await callback.answer("Foydalanuvchilar yo'q!", show_alert=True)
        return
    
    lines = ["👥 <b>Ishtirokchilar reytingi:</b>\n"]
    for i, u in enumerate(all_users[:50], 1):
        name = u["full_name"] or u["username"] or "Nomsiz"
        lines.append(f"{i}. {name} — {u['points']} ball (ID: {u['telegram_id']})")
    
    if len(all_users) > 50:
        lines.append(f"\n... va yana {len(all_users) - 50} ta")
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Orqaga", callback_data="admin_users")]
    ])
    await callback.message.edit_text("\n".join(lines), reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "search_user")
async def search_user_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "🔍 <b>Foydalanuvchi qidirish</b>\n\nTelegram ID raqamini kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.searching_user)
    await callback.answer()

@router.message(AdminStates.searching_user)
async def search_user_result(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri ID. Raqam kiriting:")
        return
    
    user = await db.get_user(target_id)
    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi!")
        await state.clear()
        return
    
    referrals = await db.get_user_referrals(target_id)
    await state.clear()
    
    text = (
        f"👤 <b>Foydalanuvchi ma'lumotlari:</b>\n\n"
        f"🆔 ID: <code>{user['telegram_id']}</code>\n"
        f"👤 Ism: {user['full_name'] or 'Nomsiz'}\n"
        f"📛 Username: @{user['username'] or 'Yo\'q'}\n"
        f"⭐ Ballar: <b>{user['points']}</b>\n"
        f"👥 Referal soni: <b>{len(referrals)}</b>\n"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ballarni tahrirlash", callback_data=f"edit_points_{target_id}")],
        [InlineKeyboardButton(text="« Orqaga", callback_data="admin_users")],
    ])
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("edit_points_"))
async def edit_points_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    target_id = int(callback.data.replace("edit_points_", ""))
    await state.update_data(editing_user_id=target_id)
    await callback.message.edit_text(
        f"✏️ <b>Ballarni tahrirlash</b>\n\nFoydalanuvchi ID: <code>{target_id}</code>\n\nYangi ball miqdorini kiriting:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.editing_user_points)
    await callback.answer()

@router.message(AdminStates.editing_user_points)
async def edit_points_finish(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    try:
        points = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Noto'g'ri qiymat. Raqam kiriting:")
        return
    
    data = await state.get_data()
    target_id = data["editing_user_id"]
    await db.set_points(target_id, points)
    await state.clear()
    
    await message.answer(
        f"✅ <b>Ballar yangilandi!</b>\n\nFoydalanuvchi ID: <code>{target_id}</code>\nYangi ballar: <b>{points}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Admin panel", callback_data="back_admin")]
        ])
    )

# ===== BROADCAST =====
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "📣 <b>Xabar yuborish</b>\n\n"
        "Yubormoqchi bo'lgan xabarni yuboring (matn, rasm yoki video):\n\n"
        "Bekor qilish: /cancel",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.broadcasting)
    await callback.answer()

@router.message(AdminStates.broadcasting)
async def broadcast_execute(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    
    await state.clear()
    all_users = await db.get_all_users()
    
    success = 0
    failed = 0
    
    status_msg = await message.answer(f"📤 Xabar yuborilmoqda... 0/{len(all_users)}")
    
    for i, user in enumerate(all_users):
        try:
            await message.copy_to(user["telegram_id"])
            success += 1
        except Exception:
            failed += 1
        
        if (i + 1) % 20 == 0:
            try:
                await status_msg.edit_text(f"📤 Xabar yuborilmoqda... {i+1}/{len(all_users)}")
            except Exception:
                pass
    
    await status_msg.edit_text(
        f"✅ <b>Xabar yuborish yakunlandi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xato: {failed}\n"
        f"📊 Jami: {len(all_users)}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Admin panel", callback_data="back_admin")]
        ])
    )

# ===== CONTEST MANAGEMENT =====
@router.callback_query(F.data == "admin_contest")
async def admin_contest(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    
    is_active = await db.get_contest_status()
    status_text = "🟢 Faol" if is_active else "🔴 To'xtatilgan"
    
    toggle_text = "⏹ Konkursni to'xtatish" if is_active else "▶️ Konkursni boshlash"
    toggle_data = "stop_contest" if is_active else "start_contest"
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data=toggle_data)],
        [InlineKeyboardButton(text="🏆 G'oliblarni e'lon qilish", callback_data="announce_winners")],
        [InlineKeyboardButton(text="🗑 Bazani tozalash (Reset)", callback_data="reset_contest")],
        [InlineKeyboardButton(text="« Orqaga", callback_data="back_admin")],
    ])
    
    all_users = await db.get_all_users()
    await callback.message.edit_text(
        f"🏆 <b>Konkurs boshqaruvi</b>\n\n"
        f"📊 Holat: {status_text}\n"
        f"👥 Ishtirokchilar: {len(all_users)} ta",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "start_contest")
async def start_contest(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await db.set_contest_status(True)
    await callback.answer("✅ Konkurs boshlandi!", show_alert=True)
    await admin_contest(callback)

@router.callback_query(F.data == "stop_contest")
async def stop_contest(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await db.set_contest_status(False)
    await callback.answer("⏹ Konkurs to'xtatildi!", show_alert=True)
    await admin_contest(callback)

@router.callback_query(F.data == "announce_winners")
async def announce_winners(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    
    top_users = await db.get_top_users(10)
    
    if not top_users:
        await callback.answer("❌ Ishtirokchilar yo'q!", show_alert=True)
        return
    
    medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
    lines = ["🏆 <b>KONKURS NATIJALARI</b> 🏆\n"]
    for i, u in enumerate(top_users):
        name = u["full_name"] or u["username"] or "Nomsiz"
        lines.append(f"{medals[i]} {i+1}-o'rin: <b>{name}</b> — {u['points']} ball")
    
    announcement = "\n".join(lines)
    
    # Barcha foydalanuvchilarga yuborish
    all_users = await db.get_all_users()
    sent = 0
    for user in all_users:
        try:
            await bot.send_message(user["telegram_id"], announcement, parse_mode="HTML")
            sent += 1
        except Exception:
            pass
    
    await callback.answer(f"✅ {sent} ta foydalanuvchiga yuborildi!", show_alert=True)
    await callback.message.edit_text(
        announcement + f"\n\n<i>📤 {sent} ta foydalanuvchiga yuborildi</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Orqaga", callback_data="admin_contest")]
        ])
    )

@router.callback_query(F.data == "reset_contest")
async def reset_contest_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, tozalash", callback_data="confirm_reset"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin_contest"),
        ]
    ])
    await callback.message.edit_text(
        "⚠️ <b>DIQQAT!</b>\n\n"
        "Barcha ishtirokchilar va ballar o'chiriladi!\n"
        "Bu amalni qaytarib bo'lmaydi.\n\n"
        "Davom etasizmi?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "confirm_reset")
async def confirm_reset(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await db.reset_all_data()
    await db.set_contest_status(False)
    await callback.answer("✅ Baza tozalandi!", show_alert=True)
    await callback.message.edit_text(
        "✅ <b>Baza muvaffaqiyatli tozalandi!</b>\n\nYangi konkurs uchun tayyor.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Admin panel", callback_data="back_admin")]
        ])
    )

# ===== BACK BUTTON =====
@router.callback_query(F.data == "back_admin")
async def back_admin(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.edit_text(
        "🛠 <b>Admin Panel</b>\n\nNimani boshqarmoqchisiz?",
        reply_markup=admin_panel_kb(),
        parse_mode="HTML"
    )
    await callback.answer()

# ===== CANCEL =====
@router.message(Command("cancel"))
async def cancel_state(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Admin panel", callback_data="back_admin")]
        ]))
    else:
        await message.answer("Hech narsa bekor qilinmadi.")
