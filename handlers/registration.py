from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command

from database.db import (
    get_user, create_user, update_user_phone,
    is_registered, get_user_results, get_leaderboard, get_full_stats
)
from keyboards.keyboards import (
    phone_keyboard, main_menu_keyboard,
    cancel_keyboard, admin_keyboard
)
from states import RegistrationStates
from config import config

router = Router()

# ══════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    user = await get_user(message.from_user.id)

    if not user:
        await create_user(
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )
        user = await get_user(message.from_user.id)

    if user and user.is_registered:
        await message.answer(
            f"👋 Xush kelibsiz, <b>{message.from_user.full_name}</b>!\n\n"
            f"📚 Fan tanlang va testni boshlang:",
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "👋 <b>Ona tili va Adabiyot Test Botiga xush kelibsiz!</b>\n\n"
            "📋 Ro'yxatdan o'tish uchun telefon raqamingizni ulashing.\n\n"
            "⬇️ Quyidagi tugmani bosing:",
            reply_markup=phone_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(RegistrationStates.waiting_for_phone)

# ══════════════════════════════════════════════
# Telefon qabul qilish
# ══════════════════════════════════════════════

@router.message(RegistrationStates.waiting_for_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    contact = message.contact

    if contact.user_id != message.from_user.id:
        await message.answer("❌ Faqat o'z telefon raqamingizni ulashishingiz mumkin!")
        return

    phone = contact.phone_number
    if not phone.startswith('+'):
        phone = '+' + phone

    await update_user_phone(telegram_id=message.from_user.id, phone=phone)
    await state.clear()

    await message.answer(
        f"✅ <b>Muvaffaqiyatli ro'yxatdan o'tdingiz!</b>\n\n"
        f"👤 Ism: <b>{message.from_user.full_name}</b>\n"
        f"📱 Telefon: <b>{phone}</b>\n\n"
        f"📚 Endi fan tanlang va testni boshlang.\n"
        f"🎯 Birinchi urinish <b>bepul</b>!",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

@router.message(RegistrationStates.waiting_for_phone)
async def wrong_contact(message: Message):
    await message.answer(
        "📱 Iltimos, quyidagi tugmani bosib telefon raqamingizni ulashing:",
        reply_markup=phone_keyboard()
    )

# ══════════════════════════════════════════════
# Asosiy menyu tugmalari
# ══════════════════════════════════════════════

@router.message(F.text == "📚 Ona tili")
async def menu_onatili(message: Message, state: FSMContext):
    if not await is_registered(message.from_user.id):
        await message.answer("❌ Avval ro'yxatdan o'ting! /start")
        return
    from keyboards.keyboards import onatili_category_keyboard
    await message.answer(
        "📚 <b>Ona tili</b>\n\nBo'limni tanlang:",
        reply_markup=onatili_category_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "📖 Adabiyot")
async def menu_adabiyot(message: Message, state: FSMContext):
    if not await is_registered(message.from_user.id):
        await message.answer("❌ Avval ro'yxatdan o'ting! /start")
        return
    from keyboards.keyboards import adabiyot_category_keyboard
    await message.answer(
        "📖 <b>Adabiyot</b>\n\nBo'limni tanlang:",
        reply_markup=adabiyot_category_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "🎓 Atestatsiya")
async def menu_attestation(message: Message, state: FSMContext):
    if not await is_registered(message.from_user.id):
        await message.answer("❌ Avval ro'yxatdan o'ting! /start")
        return
    from keyboards.keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await message.answer(
        "🎓 <b>Atestatsiya</b>\n\n"
        "Fan tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Ona tili atestatsiyasi",  callback_data="onatili:attestation")],
            [InlineKeyboardButton(text="📖 Adabiyot atestatsiyasi",  callback_data="adabiyot:attestation")],
        ]),
        parse_mode="HTML"
    )

@router.message(F.text == "📊 Natijalarim")
async def menu_results(message: Message):
    if not await is_registered(message.from_user.id):
        await message.answer("❌ Avval ro'yxatdan o'ting! /start")
        return

    results = await get_user_results(message.from_user.id, limit=10)
    if not results:
        await message.answer(
            "📊 Hali test ishlamagansiz.\n"
            "📚 Ona tili yoki Adabiyotdan boshlang!"
        )
        return

    SUBJ = {'onatili': '📚 Ona tili', 'adabiyot': '📖 Adabiyot'}
    DIFF = {'easy': '🟢', 'medium': '🟡', 'hard': '🔴'}

    text = "📊 <b>So'nggi natijalaringiz:</b>\n\n"
    for i, r in enumerate(results, 1):
        subj  = SUBJ.get(r.subject, r.subject or '')
        diff  = DIFF.get(r.difficulty, '') if r.difficulty else ''
        date  = str(r.finished_at)[:10] if r.finished_at else '—'
        sub   = f" › {r.subcategory}" if r.subcategory else ''
        text += (
            f"{i}. {subj} {diff}\n"
            f"   📁 {r.category or ''}{sub}\n"
            f"   ✅ {r.correct}/{r.total}  📈 {r.score}%\n"
            f"   📅 {date}  (#{r.attempt_number} urinish)\n\n"
        )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "🏆 Reyting")
async def menu_leaderboard(message: Message):
    leaders = await get_leaderboard(10)
    if not leaders:
        await message.answer("🏆 Hali reyting mavjud emas!")
        return

    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    text = "🏆 <b>Eng yaxshi natijalar:</b>\n\n"
    for i, row in enumerate(leaders):
        medal = medals[i] if i < len(medals) else f"{i+1}."
        name  = row.full_name or "Noma'lum"
        text += f"{medal} <b>{name}</b> — {row.best_score}%  ({row.attempts} marta)\n"
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "👤 Profil")
async def menu_profile(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting! /start")
        return

    results = await get_user_results(message.from_user.id)
    total_tests = len(results)
    best_score  = max((r.score for r in results), default=0)
    reg_date    = str(user.registered_at)[:10] if user.registered_at else '—'

    await message.answer(
        f"👤 <b>Profil</b>\n\n"
        f"📛 Ism: <b>{user.full_name}</b>\n"
        f"📱 Telefon: <b>{user.phone_number or '—'}</b>\n"
        f"📅 Ro'yxat: <b>{reg_date}</b>\n\n"
        f"📊 Jami testlar: <b>{total_tests}</b>\n"
        f"🏆 Eng yaxshi natija: <b>{best_score}%</b>",
        parse_mode="HTML"
    )

@router.message(F.text == "ℹ️ Yordam")
async def menu_help(message: Message):
    await message.answer(
        "📚 <b>Ona tili va Adabiyot Test Boti</b>\n\n"
        "🎯 <b>Qanday ishlaydi?</b>\n"
        "1️⃣ Telefon raqamingizni ulashing\n"
        "2️⃣ Fan tanlang (Ona tili / Adabiyot)\n"
        "3️⃣ Bo'lim va qiyinlik tanlang\n"
        "4️⃣ <b>Birinchi urinish bepul!</b>\n"
        "5️⃣ Keyingi urinishlar — {retry:,} so'm\n\n"
        "🎓 <b>Atestatsiya</b> — {attest:,} so'm (bir martalik)\n\n"
        "📞 Muammo bo'lsa: @admin_username".format(
            retry=config.PRICE_RETRY,
            attest=config.PRICE_ATTESTATION
        ),
        parse_mode="HTML"
    )

# ══════════════════════════════════════════════
# Admin
# ══════════════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in config.ADMIN_IDS:
        await message.answer("⛔ Siz admin emassiz!")
        return
    await message.answer(
        "🔐 <b>Admin panel</b>",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

@router.message(F.text == "📊 Statistika")
async def admin_stats(message: Message):
    if message.from_user.id not in config.ADMIN_IDS:
        return
    s = await get_full_stats()
    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Jami foydalanuvchi: <b>{s['total_users']}</b>\n"
        f"✅ Ro'yxatdan o'tgan: <b>{s['registered']}</b>\n"
        f"⏳ Kutayotgan to'lov: <b>{s['pending']}</b>\n"
        f"💰 Tasdiqlangan: <b>{s['confirmed_purchases']}</b>\n"
        f"📝 Jami testlar: <b>{s['total_tests']}</b>\n"
        f"📈 O'rtacha ball: <b>{s['avg_score']}%</b>\n"
        f"❓ Jami savollar: <b>{s['total_questions']}</b>\n"
        f"🎓 Atestatsiya savollar: <b>{s['attestation_q']}</b>",
        parse_mode="HTML"
    )

@router.message(F.text == "🔙 Orqaga")
async def back_to_main(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Asosiy menyu:",
        reply_markup=main_menu_keyboard()
    )
