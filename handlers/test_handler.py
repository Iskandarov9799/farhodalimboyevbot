import json
import base64
import zlib
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database.db import (
    is_registered, get_access_status, mark_free_used,
    has_attestation, get_attestation_format,
    get_questions, count_questions, save_test_result
)
from keyboards.keyboards import (
    biologiya_category_keyboard, biologiya_topics_keyboard,
    grades_keyboard, difficulty_keyboard,
    retry_buy_keyboard, attestation_buy_keyboard,
    miniapp_keyboard, main_menu_keyboard
)
from config import config

router = Router()

def encode_questions(q_list: list, meta: dict = None) -> str:
    payload = {'meta': meta or {}, 'questions': q_list}
    raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    compressed = zlib.compress(raw.encode('utf-8'), level=9)
    return base64.urlsafe_b64encode(compressed).decode('ascii')

def questions_to_miniapp(questions: list) -> list:
    return [
        {"id": q.id, "t": q.question_text, "a": q.option_a,
         "b": q.option_b, "c": q.option_c, "d": q.option_d,
         "ok": q.correct_answer, "img": q.image_file_id or ""}
        for q in questions
    ]

def make_access_key(subject, category, subcategory=None, difficulty=None):
    return f"{subject}:{category}:{subcategory}:{difficulty}"

async def safe_edit(callback: CallbackQuery, text: str, reply_markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        pass

async def launch_miniapp(callback: CallbackQuery, tid: int,
                         subject: str, category: str,
                         subcategory: str = None, difficulty: str = None,
                         is_attestation: bool = False):
    if not await is_registered(tid):
        await callback.message.answer("❗ Avval ro'yxatdan o'ting — /start")
        await callback.answer()
        return

    cnt = await count_questions(
        subject=subject, category=category,
        subcategory=subcategory, difficulty=difficulty,
        is_attestation=is_attestation
    )
    if cnt == 0:
        await safe_edit(callback,
            "❌ <b>Savollar topilmadi!</b>\n\nBu bo'limda hali savollar yo'q.\nAdmin tez orada qo'shadi 🙏"
        )
        await callback.answer()
        return

    if not is_attestation:
        access_key = make_access_key(subject, category, subcategory, difficulty)
        status = await get_access_status(tid, access_key)
        if status == 'buy':
            await safe_edit(callback,
                f"💳 <b>Bu test uchun to'lov talab qilinadi</b>\n\n"
                f"💰 Narxi: <b>{config.PRICE_RETRY:,} so'm</b>",
                reply_markup=retry_buy_keyboard(access_key)
            )
            await callback.answer()
            return
    else:
        if not await has_attestation(tid, subject):
            await safe_edit(callback,
                f"🎓 <b>Atestatsiya testi</b>\n\n"
                f"💰 Narxi: <b>{config.PRICE_ATTESTATION:,} so'm</b> (bir martalik)",
                reply_markup=attestation_buy_keyboard(subject)
            )
            await callback.answer()
            return

    questions = await get_questions(
        subject=subject, category=category,
        subcategory=subcategory, difficulty=difficulty,
        is_attestation=is_attestation,
        count=config.ATTESTATION_COUNT if is_attestation else min(cnt, config.ATTESTATION_COUNT)
    )

    if not is_attestation:
        access_key = make_access_key(subject, category, subcategory, difficulty)
        await mark_free_used(tid, access_key)

    meta = {
        'subject': subject, 'category': category,
        'subcategory': subcategory, 'difficulty': difficulty,
        'is_attestation': is_attestation, 'solution_url': config.SOLUTION_URL,
    }

    encoded = encode_questions(questions_to_miniapp(questions), meta)
    url = f"{config.MINI_APP_URL.rstrip('/')}/?data={encoded}"

    DIFF  = {'easy': '🟢 Oson', 'medium': "🟡 O'rta", 'hard': '🔴 Qiyin'}
    TOPIC = config.BIOLOGIYA_TOPICS
    diff_label = DIFF.get(difficulty, '') if difficulty else ''
    sub_label  = TOPIC.get(subcategory, subcategory) if subcategory else (subcategory or '')

    await callback.message.answer(
        f"🧬 <b>Biologiya</b> — <b>{sub_label or category}</b>"
        f"{' · ' + diff_label if diff_label else ''}\n\n"
        f"📝 Savollar soni: <b>{len(questions)} ta</b>\n\nTestni boshlashga tayyor bo'lsangiz, tugmani bosing 👇",
        reply_markup=miniapp_keyboard(url), parse_mode="HTML"
    )
    await callback.answer()

# ══════════════════════════════════════════════
# ASOSIY HANDLER
# ══════════════════════════════════════════════

@router.message(F.text == "🧬 Biologiya")
async def biologiya_menu(message: Message, state: FSMContext):
    if not await is_registered(message.from_user.id):
        await message.answer("❗ Avval ro'yxatdan o'ting — /start")
        return
    await message.answer(
        "🧬 <b>Biologiya</b>\n\nQaysi turdagi testni ishlaysiz?",
        reply_markup=biologiya_category_keyboard(), parse_mode="HTML"
    )

# ══════════════════════════════════════════════
# ORQAGA — BACK HANDLERS
# ══════════════════════════════════════════════

@router.callback_query(F.data == "biologiya:back:category")
async def back_to_category(callback: CallbackQuery):
    await safe_edit(callback,
        "🧬 <b>Biologiya</b>\n\nQaysi turdagi testni ishlaysiz?",
        reply_markup=biologiya_category_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "biologiya:back:topics")
async def back_to_topics(callback: CallbackQuery):
    await safe_edit(callback,
        "📌 <b>Mavzuni tanlang:</b>",
        reply_markup=biologiya_topics_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "biologiya:back:grades")
async def back_to_grades(callback: CallbackQuery):
    await safe_edit(callback,
        "🏫 <b>Sinfni tanlang:</b>",
        reply_markup=grades_keyboard('biologiya')
    )
    await callback.answer()

# ══════════════════════════════════════════════
# KATEGORIYA
# ══════════════════════════════════════════════

@router.callback_query(F.data.startswith("biologiya:cat:"))
async def biologiya_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":")[2]
    tid = callback.from_user.id
    await state.update_data(subject='biologiya', category=category)

    if category == 'mavzu':
        await safe_edit(callback, "📌 <b>Mavzuni tanlang:</b>",
                        reply_markup=biologiya_topics_keyboard())
    elif category == 'sinf':
        await safe_edit(callback, "🏫 <b>Sinfni tanlang:</b>",
                        reply_markup=grades_keyboard('biologiya'))
    elif category == 'aralash':
        await safe_edit(callback, "🔀 <b>Aralash test</b>\n\nQiyinlik darajasini tanlang:",
                        reply_markup=difficulty_keyboard('biologiya', 'aralash'))
    elif category == 'attestation':
        if not await has_attestation(tid, 'biologiya'):
            await safe_edit(callback,
                f"🎓 <b>Atestatsiya testi</b>\n\n"
                f"💰 Narxi: <b>{config.PRICE_ATTESTATION:,} so'm</b> (bir martalik)",
                reply_markup=attestation_buy_keyboard('biologiya')
            )
        else:
            await launch_miniapp(callback, tid, 'biologiya', 'attestation', is_attestation=True)
            return
    await callback.answer()

# ══════════════════════════════════════════════
# MAVZU → QIYINLIK
# ══════════════════════════════════════════════

@router.callback_query(F.data.regexp(r'^biologiya:topic:[^:]+$'))
async def biologiya_topic(callback: CallbackQuery, state: FSMContext):
    topic = callback.data.split(":")[2]
    await state.update_data(subcategory=topic)
    await safe_edit(callback,
        f"🎯 <b>{config.BIOLOGIYA_TOPICS.get(topic, topic)}</b>\n\nQiyinlik darajasini tanlang:",
        reply_markup=difficulty_keyboard('biologiya', 'mavzu', topic)
    )
    await callback.answer()

# ══════════════════════════════════════════════
# SINF → QIYINLIK
# ══════════════════════════════════════════════

@router.callback_query(F.data.regexp(r'^biologiya:grade:\d+$'))
async def biologiya_grade(callback: CallbackQuery, state: FSMContext):
    grade = callback.data.split(":")[2]
    await state.update_data(subcategory=grade)
    await safe_edit(callback,
        f"🏫 <b>{config.GRADES.get(grade, grade)}</b>\n\nQiyinlik darajasini tanlang:",
        reply_markup=difficulty_keyboard('biologiya', 'sinf', grade)
    )
    await callback.answer()

# ══════════════════════════════════════════════
# QIYINLIK → MINIAPP
# ══════════════════════════════════════════════

@router.callback_query(F.data.startswith("biologiya:diff:"))
async def biologiya_difficulty(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    category    = parts[2]
    subcategory = parts[3] if parts[3] else None
    difficulty  = parts[4]
    await launch_miniapp(callback, callback.from_user.id,
                         subject='biologiya', category=category,
                         subcategory=subcategory, difficulty=difficulty)

# ══════════════════════════════════════════════
# ATESTATSIYA
# ══════════════════════════════════════════════

@router.message(F.text == "🎓 Atestatsiya")
async def attestation_menu(message: Message):
    tid = message.from_user.id
    if not await is_registered(tid):
        await message.answer("❗ Avval ro'yxatdan o'ting — /start")
        return

    if await has_attestation(tid, 'biologiya'):
        cnt = await count_questions(subject='biologiya', is_attestation=True)
        if cnt == 0:
            await message.answer("❌ Atestatsiya savollari hali qo'shilmagan.")
            return
        questions = await get_questions(
            subject='biologiya', is_attestation=True, count=config.ATTESTATION_COUNT
        )
        meta = {
            'subject': 'biologiya', 'category': 'attestation',
            'is_attestation': True, 'solution_url': config.SOLUTION_URL,
        }
        encoded = encode_questions(questions_to_miniapp(questions), meta)
        url = f"{config.MINI_APP_URL.rstrip('/')}/?data={encoded}"
        await message.answer(
            f"🎓 <b>Atestatsiya testi</b>\n\n📝 Savollar: <b>{len(questions)} ta</b>",
            reply_markup=miniapp_keyboard(url), parse_mode="HTML"
        )
    else:
        await message.answer(
            f"🎓 <b>Atestatsiya testi</b>\n\nBu test bir martalik sotib olinadi.\n"
            f"💰 Narxi: <b>{config.PRICE_ATTESTATION:,} so'm</b>",
            reply_markup=attestation_buy_keyboard('biologiya'), parse_mode="HTML"
        )

# ══════════════════════════════════════════════
# MINI APP NATIJA
# ══════════════════════════════════════════════

@router.message(F.web_app_data)
async def webapp_result(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        tid  = message.from_user.id
        await save_test_result(
            telegram_id=tid, subject=data.get('subject', 'biologiya'),
            category=data.get('category', 'aralash'), subcategory=data.get('subcategory'),
            difficulty=data.get('difficulty'), is_attestation=data.get('is_attestation', False),
            total=data.get('total', 0), correct=data.get('correct', 0),
            wrong=data.get('wrong', 0), skipped=data.get('skip', 0), score=data.get('score', 0),
        )
        pct = data.get('score', 0)
        correct = data.get('correct', 0)
        total   = data.get('total', 0)
        if pct >= 90:   emoji, baho = "🏆", "A'lo (5)"
        elif pct >= 70: emoji, baho = "🎉", "Yaxshi (4)"
        elif pct >= 50: emoji, baho = "📚", "Qoniqarli (3)"
        else:           emoji, baho = "😔", "Qoniqarsiz (2)"
        await message.answer(
            f"{emoji} <b>Test yakunlandi!</b>\n\n"
            f"✅ To'g'ri: <b>{correct}</b> / {total}\n"
            f"📊 Natija: <b>{pct}%</b>\n"
            f"📝 Baho: <b>{baho}</b>",
            reply_markup=main_menu_keyboard(), parse_mode="HTML"
        )
    except Exception as e:
        await message.answer(f"❌ Natijani saqlashda xato: {e}")