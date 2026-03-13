import io
import openpyxl
from aiogram import Router, F, Bot
from aiogram.types import Message, BufferedInputFile
from aiogram.fsm.context import FSMContext

from database.db import (
    get_all_users, get_full_stats, add_question,
    count_questions, delete_all_questions
)
from keyboards.keyboards import (
    admin_keyboard, cancel_keyboard, main_menu_keyboard,
    subject_keyboard, addq_category_keyboard, addq_topic_keyboard,
    addq_grade_keyboard, addq_difficulty_keyboard, correct_answer_keyboard,
    skip_image_keyboard
)
from states import AdminStates
from config import config

router = Router()

# ══════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════

def is_admin(message: Message) -> bool:
    return message.from_user.id in config.ADMIN_IDS

# ══════════════════════════════════════════════
# FOYDALANUVCHILAR RO'YXATI
# ══════════════════════════════════════════════

@router.message(F.text == "👥 Foydalanuvchilar")
async def admin_users(message: Message):
    if not is_admin(message): return

    users = await get_all_users()
    total = len(users)
    text  = f"👥 <b>Foydalanuvchilar: {total} ta</b>\n\n"

    for u in users[:20]:
        icon  = "✅" if u.is_registered else "👤"
        uname = f"@{u.username}" if u.username else "—"
        text += f"{icon} {u.full_name or 'Noma\'lum'} | {u.phone_number or '—'} | {uname}\n"

    if total > 20:
        text += f"\n... va yana {total - 20} ta"

    await message.answer(text, parse_mode="HTML")

# ══════════════════════════════════════════════
# EXCEL EKSPORT
# ══════════════════════════════════════════════

@router.message(F.text == "📥 Excel eksport")
async def admin_export(message: Message):
    if not is_admin(message): return

    users = await get_all_users()
    wb    = openpyxl.Workbook()
    ws    = wb.active
    ws.title = "Foydalanuvchilar"

    # Sarlavha
    ws.append(["#", "Telegram ID", "Ism", "Username", "Telefon", "Ro'yxat", "Sana"])
    for i, u in enumerate(users, 1):
        ws.append([
            i,
            u.telegram_id,
            u.full_name or "",
            u.username or "",
            u.phone_number or "",
            "Ha" if u.is_registered else "Yo'q",
            str(u.registered_at)[:16] if u.registered_at else "",
        ])

    # Ustun kengligini moslashtirish
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    await message.answer_document(
        document=BufferedInputFile(buf.read(), filename="users.xlsx"),
        caption=f"📥 Jami: <b>{len(users)}</b> ta foydalanuvchi",
        parse_mode="HTML"
    )

# ══════════════════════════════════════════════
# BROADCAST
# ══════════════════════════════════════════════

@router.message(F.text == "📢 Broadcast")
async def admin_broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message): return
    await message.answer(
        "📢 <b>Broadcast</b>\n\n"
        "Barcha foydalanuvchilarga yuboriladigan xabarni yozing\n"
        "(matn, rasm yoki video yuborishingiz mumkin):",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.broadcast_message)

@router.message(AdminStates.broadcast_message, F.text == "❌ Bekor qilish")
async def broadcast_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=admin_keyboard())

@router.message(AdminStates.broadcast_message)
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users   = await get_all_users()
    success = 0
    failed  = 0

    await message.answer(f"⏳ {len(users)} ta foydalanuvchiga yuborilmoqda...")

    for user in users:
        try:
            if message.photo:
                await bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption or ""
                )
            elif message.video:
                await bot.send_video(
                    chat_id=user.telegram_id,
                    video=message.video.file_id,
                    caption=message.caption or ""
                )
            else:
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=message.text or ""
                )
            success += 1
        except Exception:
            failed += 1

    await message.answer(
        f"📢 <b>Broadcast tugadi!</b>\n\n"
        f"✅ Yuborildi: <b>{success}</b>\n"
        f"❌ Xato:     <b>{failed}</b>",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

# ══════════════════════════════════════════════
# SAVOL QO'SHISH
# ══════════════════════════════════════════════

@router.message(F.text == "➕ Savol qo'shish")
async def add_question_start(message: Message, state: FSMContext):
    if not is_admin(message): return
    await message.answer(
        "➕ <b>Yangi savol qo'shish</b>\n\nFanni tanlang:",
        reply_markup=subject_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_subject)

# Fan tanlash
from aiogram.types import CallbackQuery

@router.callback_query(F.data.startswith("addq:subject:"))
async def addq_subject(callback: CallbackQuery, state: FSMContext):
    subject = callback.data.split(":")[2]
    await state.update_data(subject=subject)
    SUBJ = {'onatili': '📚 Ona tili', 'adabiyot': '📖 Adabiyot'}
    await callback.message.edit_text(
        f"📁 <b>{SUBJ.get(subject)} — Kategoriya tanlang:</b>",
        reply_markup=addq_category_keyboard(subject),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_category)
    await callback.answer()

# Kategoriya tanlash
@router.callback_query(F.data.startswith("addq:cat:"))
async def addq_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[2]
    await state.update_data(category=category)
    data = await state.get_data()
    subject = data.get('subject')

    if category == 'mavzu':
        await callback.message.edit_text(
            "📌 <b>Mavzuni tanlang:</b>",
            reply_markup=addq_topic_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.add_subcategory)

    elif category == 'sinf':
        await callback.message.edit_text(
            "🏫 <b>Sinfni tanlang:</b>",
            reply_markup=addq_grade_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.add_subcategory)

    elif category == 'attestation':
        # Atestatsiya — subcategory yo'q, difficulty yo'q
        await state.update_data(subcategory=None, difficulty=None, is_attestation=True)
        # order_num so'rash
        cnt = await count_questions(subject=subject, is_attestation=True)
        await callback.message.edit_text(
            f"🎓 <b>Atestatsiya savoli</b>\n\n"
            f"Hozir {cnt} ta atestatsiya savoli bor.\n"
            f"Tartib raqamini yozing (masalan: <code>{cnt + 1}</code>):",
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.add_order_num)

    else:
        # aralash, gazallar — qiyinlik kerak
        await callback.message.edit_text(
            "🎯 <b>Qiyinlik darajasini tanlang:</b>",
            reply_markup=addq_difficulty_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(AdminStates.add_difficulty)

    await callback.answer()

# Subcategory (mavzu yoki sinf)
@router.callback_query(F.data.startswith("addq:topic:"))
async def addq_topic(callback: CallbackQuery, state: FSMContext):
    topic = callback.data.split(":")[2]
    await state.update_data(subcategory=topic, is_attestation=False)
    label = config.ONA_TILI_TOPICS.get(topic, topic)
    await callback.message.edit_text(
        f"📌 <b>{label}</b>\n\nQiyinlik darajasini tanlang:",
        reply_markup=addq_difficulty_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_difficulty)
    await callback.answer()

@router.callback_query(F.data.startswith("addq:grade:"))
async def addq_grade(callback: CallbackQuery, state: FSMContext):
    grade = callback.data.split(":")[2]
    await state.update_data(subcategory=grade, is_attestation=False)
    await callback.message.edit_text(
        f"🏫 <b>{grade}-sinf</b>\n\nQiyinlik darajasini tanlang:",
        reply_markup=addq_difficulty_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_difficulty)
    await callback.answer()

# Qiyinlik tanlash
@router.callback_query(F.data.startswith("addq:diff:"))
async def addq_difficulty(callback: CallbackQuery, state: FSMContext):
    difficulty = callback.data.split(":")[2]
    await state.update_data(difficulty=difficulty, is_attestation=False)
    DIFF = {'easy': '🟢 Oson', 'medium': "🟡 O'rta", 'hard': '🔴 Qiyin'}
    await callback.message.edit_text(
        f"✅ Qiyinlik: <b>{DIFF.get(difficulty)}</b>\n\n"
        f"📸 Savol rasmini yuboring yoki o'tkazib yuboring:",
        parse_mode="HTML",
    )
    await callback.message.answer(
        "📸 Rasm yuboring yoki o'tkazib yuboring:",
        reply_markup=skip_image_keyboard()
    )
    await state.set_state(AdminStates.add_image)
    await callback.answer()

# Order num (attestation uchun)
@router.message(AdminStates.add_order_num)
async def addq_order_num(message: Message, state: FSMContext):
    try:
        order_num = int(message.text.strip())
        await state.update_data(order_num=order_num)
    except ValueError:
        await message.answer("❌ Raqam kiriting!")
        return

    await message.answer(
        "📸 Rasm yuboring yoki o'tkazib yuboring:",
        reply_markup=skip_image_keyboard()
    )
    await state.set_state(AdminStates.add_image)

# Rasm
@router.message(AdminStates.add_image, F.photo)
async def addq_image(message: Message, state: FSMContext):
    await state.update_data(image_file_id=message.photo[-1].file_id)
    await message.answer(
        "✅ Rasm saqlandi.\n\n📝 Savol matnini yozing:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(AdminStates.add_text)

@router.message(AdminStates.add_image, F.text == "⏭ Rasmisiz davom etish")
async def addq_skip_image(message: Message, state: FSMContext):
    await state.update_data(image_file_id=None)
    await message.answer("📝 Savol matnini yozing:", reply_markup=cancel_keyboard())
    await state.set_state(AdminStates.add_text)

# Savol matni
@router.message(AdminStates.add_text)
async def addq_text(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_keyboard())
        return
    await state.update_data(question_text=message.text)
    await message.answer("🅰 A variantini yozing:")
    await state.set_state(AdminStates.add_a)

# Variantlar
@router.message(AdminStates.add_a)
async def addq_a(message: Message, state: FSMContext):
    await state.update_data(option_a=message.text)
    await message.answer("🅱 B variantini yozing:")
    await state.set_state(AdminStates.add_b)

@router.message(AdminStates.add_b)
async def addq_b(message: Message, state: FSMContext):
    await state.update_data(option_b=message.text)
    await message.answer("🅲 C variantini yozing:")
    await state.set_state(AdminStates.add_c)

@router.message(AdminStates.add_c)
async def addq_c(message: Message, state: FSMContext):
    await state.update_data(option_c=message.text)
    await message.answer("🅳 D variantini yozing:")
    await state.set_state(AdminStates.add_d)

@router.message(AdminStates.add_d)
async def addq_d(message: Message, state: FSMContext):
    await state.update_data(option_d=message.text)
    await message.answer(
        "✅ <b>To'g'ri javobni tanlang:</b>",
        reply_markup=correct_answer_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.add_correct)

# To'g'ri javob
@router.callback_query(F.data.startswith("addq:correct:"))
async def addq_correct(callback: CallbackQuery, state: FSMContext):
    correct = callback.data.split(":")[2]
    data    = await state.get_data()
    await state.clear()

    await add_question(
        subject        = data['subject'],
        category       = data['category'],
        question_text  = data['question_text'],
        option_a       = data['option_a'],
        option_b       = data['option_b'],
        option_c       = data['option_c'],
        option_d       = data['option_d'],
        correct_answer = correct,
        subcategory    = data.get('subcategory'),
        difficulty     = data.get('difficulty'),
        is_attestation = data.get('is_attestation', False),
        order_num      = data.get('order_num'),
        image_file_id  = data.get('image_file_id'),
    )

    SUBJ = {'onatili': '📚 Ona tili', 'adabiyot': '📖 Adabiyot'}
    await callback.message.edit_text(
        f"✅ <b>Savol muvaffaqiyatli qo'shildi!</b>\n\n"
        f"📚 Fan: {SUBJ.get(data['subject'])}\n"
        f"📁 Kategoriya: {data['category']}\n"
        f"🔑 Subcategory: {data.get('subcategory') or '—'}\n"
        f"🎯 Qiyinlik: {data.get('difficulty') or '—'}\n"
        f"✅ To'g'ri javob: <b>{correct}</b>",
        parse_mode="HTML"
    )
    await callback.message.answer(
        "Yana savol qo'shish uchun '➕ Savol qo'shish' tugmasini bosing.",
        reply_markup=admin_keyboard()
    )
    await callback.answer()

# Bekor qilish callback
@router.callback_query(F.data == "addq:cancel")
async def addq_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.message.answer("Admin panel:", reply_markup=admin_keyboard())
    await callback.answer()

# ══════════════════════════════════════════════
# BARCHA SAVOLLARNI O'CHIRISH
# ══════════════════════════════════════════════

@router.message(F.text == "🗑 Savollarni o'chirish")
async def delete_questions_confirm(message: Message):
    if not is_admin(message): return
    cnt = await count_questions()
    await message.answer(
        f"⚠️ <b>Diqqat!</b>\n\n"
        f"Hozir bazada <b>{cnt} ta</b> savol bor.\n"
        f"Barchasini o'chirishni tasdiqlaysizmi?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🗑 Ha, o'chirish", callback_data="admin:delete_all_q"),
                InlineKeyboardButton(text="❌ Yo'q", callback_data="admin:cancel_delete"),
            ]
        ]),
        parse_mode="HTML"
    )

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@router.callback_query(F.data == "admin:delete_all_q")
async def delete_questions_execute(callback: CallbackQuery):
    deleted = await delete_all_questions()
    await callback.message.edit_text(
        f"🗑 <b>{deleted} ta savol o'chirildi!</b>",
        parse_mode="HTML"
    )
    await callback.message.answer("Admin panel:", reply_markup=admin_keyboard())
    await callback.answer()

@router.callback_query(F.data == "admin:cancel_delete")
async def delete_questions_cancel(callback: CallbackQuery):
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer()

# ══════════════════════════════════════════════
# YECHIM LINKI
# ══════════════════════════════════════════════

@router.message(F.text == "🔗 Yechim linki")
async def solution_url_info(message: Message):
    if not is_admin(message): return
    url = config.SOLUTION_URL
    if url:
        await message.answer(
            f"🔗 <b>Hozirgi yechim linki:</b>\n<code>{url}</code>\n\n"
            f"O'zgartirish uchun .env faylida <code>SOLUTION_URL</code> ni yangilang.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            "⚠️ <b>SOLUTION_URL</b> .env faylida yo'q!\n\n"
            "Qo'shish uchun:\n<code>SOLUTION_URL=https://t.me/kanal_nomi</code>",
            parse_mode="HTML"
        )

# ══════════════════════════════════════════════
# EXCEL DAN KO'P SAVOL YUKLASH
# ══════════════════════════════════════════════

@router.message(F.text == "📤 Excel import")
async def excel_import_start(message: Message):
    if not is_admin(message): return

    # Shablon yaratib yuborish
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Savollar"

    # Sarlavha
    headers = [
        "subject", "category", "subcategory", "difficulty",
        "is_attestation", "order_num",
        "question", "a", "b", "c", "d", "correct"
    ]
    ws.append(headers)

    # Sarlavhalarni qalin qilish
    from openpyxl.styles import Font, PatternFill
    for col in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="4472C4")
        cell.font = Font(bold=True, color="FFFFFF")

    # Ustun kengligini moslashtirish
    widths = [10, 12, 14, 12, 14, 10, 50, 25, 25, 25, 25, 10]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w

    # Misol qatorlar
    examples = [
        ["onatili", "mavzu", "fonetika", "easy",   "FALSE", "", "O'zbek tilida nechta unli tovush bor?", "5 ta", "6 ta", "7 ta", "8 ta", "B"],
        ["onatili", "aralash", "", "medium",         "FALSE", "", "Sinonimlarga misol:", "katta-kichik", "baland-past", "go'zal-chiroyli", "tez-sekin", "C"],
        ["adabiyot", "sinf", "7", "hard",            "FALSE", "", "Navoiy qaysi asrda yashagan?", "XIV", "XV", "XVI", "XVII", "B"],
        ["adabiyot", "gazallar", "", "easy",         "FALSE", "", "G'azal necha misradan iborat?", "4", "6", "8", "10", "C"],
        ["onatili", "attestation", "", "",           "TRUE",  "1", "Fonetika nima?", "So'z haqidagi fan", "Tovush haqidagi fan", "Gap haqidagi fan", "Harf haqidagi fan", "B"],
    ]
    for row in examples:
        ws.append(row)

    # Izohlar varaqasi
    ws2 = wb.create_sheet("Qo'llanma")
    ws2.column_dimensions['A'].width = 20
    ws2.column_dimensions['B'].width = 50
    guide = [
        ("subject",        "onatili | adabiyot"),
        ("category",       "mavzu | aralash | sinf | gazallar | attestation"),
        ("subcategory",    "mavzu uchun: fonetika, leksika, morfologiya, sintaksis, imlo, uslubiyat\nsinf uchun: 5, 6, 7, 8, 9, 10, 11\nboshqalar uchun: bo'sh"),
        ("difficulty",     "easy | medium | hard  (attestation uchun bo'sh)"),
        ("is_attestation", "TRUE | FALSE"),
        ("order_num",      "Faqat attestation uchun tartib raqami (1, 2, 3...), boshqalar uchun bo'sh"),
        ("question",       "Savol matni"),
        ("a, b, c, d",     "Variant matni"),
        ("correct",        "To'g'ri javob: A | B | C | D"),
    ]
    ws2.append(["Ustun", "Qiymatlar"])
    ws2.cell(1,1).font = Font(bold=True)
    ws2.cell(1,2).font = Font(bold=True)
    for row in guide:
        ws2.append(list(row))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    await message.answer_document(
        document=BufferedInputFile(buf.read(), filename="savollar_shablon.xlsx"),
        caption=(
            "📋 <b>Excel shablon</b>\n\n"
            "1️⃣ Shu faylni yuklab oling\n"
            "2️⃣ Savollarni to'ldiring\n"
            "3️⃣ Faylni botga yuboring\n\n"
            "📌 <b>Qo'llanma</b> varaqasini ham o'qing!"
        ),
        parse_mode="HTML"
    )

@router.message(F.document)
async def excel_import_upload(message: Message):
    if not is_admin(message): return

    doc = message.document
    if not doc.file_name or not doc.file_name.endswith('.xlsx'):
        return  # xlsx emas — e'tiborsiz

    await message.answer("⏳ Fayl o'qilmoqda...")

    # Faylni yuklab olish
    from aiogram import Bot
    bot: Bot = message.bot
    file = await bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await bot.download_file(file.file_path, buf)
    buf.seek(0)

    wb = openpyxl.load_workbook(buf)
    ws = wb.active

    VALID_SUBJECTS    = {'onatili', 'adabiyot'}
    VALID_CATEGORIES  = {'mavzu', 'aralash', 'sinf', 'gazallar', 'attestation'}
    VALID_DIFFICULTIES= {'easy', 'medium', 'hard', ''}
    VALID_CORRECT     = {'A', 'B', 'C', 'D'}

    added   = 0
    skipped = 0
    errors  = []

    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not any(row):
            continue  # Bo'sh qator

        try:
            subject        = str(row[0] or '').strip().lower()
            category       = str(row[1] or '').strip().lower()
            subcategory    = str(row[2] or '').strip() or None
            difficulty     = str(row[3] or '').strip().lower()
            is_attestation = str(row[4] or '').strip().upper() == 'TRUE'
            order_num      = int(row[5]) if row[5] else None
            question_text  = str(row[6] or '').strip()
            option_a       = str(row[7] or '').strip()
            option_b       = str(row[8] or '').strip()
            option_c       = str(row[9] or '').strip()
            option_d       = str(row[10] or '').strip()
            correct        = str(row[11] or '').strip().upper()

            # Validatsiya
            if subject not in VALID_SUBJECTS:
                errors.append(f"Qator {row_num}: subject '{subject}' noto'g'ri")
                skipped += 1
                continue
            if category not in VALID_CATEGORIES:
                errors.append(f"Qator {row_num}: category '{category}' noto'g'ri")
                skipped += 1
                continue
            if not question_text:
                errors.append(f"Qator {row_num}: savol matni bo'sh")
                skipped += 1
                continue
            if correct not in VALID_CORRECT:
                errors.append(f"Qator {row_num}: correct '{correct}' noto'g'ri (A/B/C/D)")
                skipped += 1
                continue
            if not all([option_a, option_b, option_c, option_d]):
                errors.append(f"Qator {row_num}: variantlar to'liq emas")
                skipped += 1
                continue

            await add_question(
                subject=subject, category=category,
                subcategory=subcategory, difficulty=difficulty or None,
                is_attestation=is_attestation, order_num=order_num,
                question_text=question_text,
                option_a=option_a, option_b=option_b,
                option_c=option_c, option_d=option_d,
                correct_answer=correct
            )
            added += 1

        except Exception as e:
            errors.append(f"Qator {row_num}: {e}")
            skipped += 1

    # Natija
    text = (
        f"✅ <b>Import tugadi!</b>\n\n"
        f"✅ Qo'shildi: <b>{added} ta</b>\n"
        f"❌ O'tkazildi: <b>{skipped} ta</b>\n"
    )
    if errors:
        error_text = "\n".join(errors[:10])
        if len(errors) > 10:
            error_text += f"\n... va yana {len(errors)-10} ta xato"
        text += f"\n⚠️ <b>Xatolar:</b>\n<code>{error_text}</code>"

    await message.answer(text, parse_mode="HTML", reply_markup=admin_keyboard())
