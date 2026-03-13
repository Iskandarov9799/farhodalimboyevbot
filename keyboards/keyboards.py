from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo
)
from config import config

def phone_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamimni ulashish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def main_menu_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧬 Biologiya")],
            [KeyboardButton(text="🎓 Atestatsiya")],
            [KeyboardButton(text="📊 Natijalarim"), KeyboardButton(text="🏆 Reyting")],
            [KeyboardButton(text="👤 Profil"),       KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True
    )

def cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="payment:cancel")]
    ])

def back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    )

def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Kutayotgan to'lovlar")],
            [KeyboardButton(text="👥 Foydalanuvchilar"),  KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📢 Broadcast"),          KeyboardButton(text="➕ Savol qo'shish")],
            [KeyboardButton(text="📋 Savollar"),           KeyboardButton(text="📥 Excel eksport")],
            [KeyboardButton(text="📤 Excel import"),       KeyboardButton(text="🗑 Savollarni o'chirish")],
            [KeyboardButton(text="🔙 Orqaga")],
        ],
        resize_keyboard=True
    )

def skip_image_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⏭ Rasmisiz davom etish")],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True
    )

# ── Biologiya inline ────────────────────────────────

def biologiya_category_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📌 Mavzulashtirilgan", callback_data="biologiya:cat:mavzu")],
        [InlineKeyboardButton(text="🏫 Sinflar bo'yicha",  callback_data="biologiya:cat:sinf")],
        [InlineKeyboardButton(text="🔀 Aralash test",      callback_data="biologiya:cat:aralash")],
        [InlineKeyboardButton(text="🎓 Atestatsiya",       callback_data="biologiya:cat:attestation")],
    ])

def biologiya_topics_keyboard():
    buttons = []
    for key, label in config.BIOLOGIYA_TOPICS.items():
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"biologiya:topic:{key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def grades_keyboard(subject='biologiya'):
    buttons = []
    row = []
    for key, label in config.GRADES.items():
        row.append(InlineKeyboardButton(text=label, callback_data=f"{subject}:grade:{key}"))
        if len(row) == 2:
            buttons.append(row); row = []
    if row: buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def difficulty_keyboard(subject='biologiya', category='aralash', subcategory=None):
    sub = subcategory or ''
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Oson",  callback_data=f"{subject}:diff:{category}:{sub}:easy")],
        [InlineKeyboardButton(text="🟡 O'rta", callback_data=f"{subject}:diff:{category}:{sub}:medium")],
        [InlineKeyboardButton(text="🔴 Qiyin", callback_data=f"{subject}:diff:{category}:{sub}:hard")],
    ])

def miniapp_keyboard(url: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Testni boshlash", web_app=WebAppInfo(url=url))]
    ])

def retry_buy_keyboard(access_key: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"💳 {config.PRICE_RETRY:,} so'm to'lash",
            callback_data=f"payment:retry:{access_key}"
        )],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="payment:cancel")],
    ])

def attestation_buy_keyboard(subject: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"💳 {config.PRICE_ATTESTATION:,} so'm to'lash",
            callback_data=f"payment:attestation:{subject}"
        )],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="payment:cancel")],
    ])

def attestation_format_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Mini App", callback_data="attest:format:miniapp")],
        [InlineKeyboardButton(text="📄 PDF",      callback_data="attest:format:pdf")],
    ])

# ── Savol qo'shish ─────────────────────────────────

def subject_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧬 Biologiya", callback_data="addq:subject:biologiya")],
        [InlineKeyboardButton(text="❌ Bekor",     callback_data="addq:cancel")],
    ])

def addq_category_keyboard(subject):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📌 Mavzulashtirilgan", callback_data="addq:cat:mavzu")],
        [InlineKeyboardButton(text="🏫 Sinflar",           callback_data="addq:cat:sinf")],
        [InlineKeyboardButton(text="🔀 Aralash",           callback_data="addq:cat:aralash")],
        [InlineKeyboardButton(text="🎓 Atestatsiya",       callback_data="addq:cat:attestation")],
        [InlineKeyboardButton(text="❌ Bekor",             callback_data="addq:cancel")],
    ])

def addq_topic_keyboard():
    buttons = []
    for key, label in config.BIOLOGIYA_TOPICS.items():
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"addq:topic:{key}")])
    buttons.append([InlineKeyboardButton(text="❌ Bekor", callback_data="addq:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def addq_grade_keyboard():
    buttons = []
    row = []
    for key, label in config.GRADES.items():
        row.append(InlineKeyboardButton(text=label, callback_data=f"addq:grade:{key}"))
        if len(row) == 3:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton(text="❌ Bekor", callback_data="addq:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def addq_difficulty_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Oson",  callback_data="addq:diff:easy")],
        [InlineKeyboardButton(text="🟡 O'rta", callback_data="addq:diff:medium")],
        [InlineKeyboardButton(text="🔴 Qiyin", callback_data="addq:diff:hard")],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="addq:cancel")],
    ])

def correct_answer_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="A", callback_data="addq:correct:A"),
            InlineKeyboardButton(text="B", callback_data="addq:correct:B"),
            InlineKeyboardButton(text="C", callback_data="addq:correct:C"),
            InlineKeyboardButton(text="D", callback_data="addq:correct:D"),
        ],
        [InlineKeyboardButton(text="❌ Bekor", callback_data="addq:cancel")],
    ])
