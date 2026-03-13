from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.db import (
    create_purchase, confirm_purchase, reject_purchase,
    get_purchase_by_id, get_pending_purchases,
    grant_attestation, get_user
)
from keyboards.keyboards import (
    cancel_keyboard, payment_confirm_keyboard,
    main_menu_keyboard, attestation_format_keyboard
)
from states import PaymentStates
from config import config

router = Router()

# ══════════════════════════════════════════════
# TO'LOV BOSHLASH — buy:retry yoki buy:attestation
# ══════════════════════════════════════════════

@router.callback_query(F.data.startswith("buy:"))
async def buy_handler(callback: CallbackQuery, state: FSMContext):
    """
    buy:retry:onatili:aralash:None:easy
    buy:attestation:onatili
    buy:attestation:adabiyot
    """
    parts        = callback.data.split(":", 2)  # ['buy', 'retry'/'attestation', '...rest']
    product_type = parts[1]
    rest         = parts[2] if len(parts) > 2 else ""

    if product_type == 'retry':
        amount     = config.PRICE_RETRY
        retry_key  = rest
        product_id = 'retry'          # ← DB da 'retry', kalit retry_key da
        desc       = f"🔄 Qayta urinish\n<code>{retry_key}</code>"

    elif product_type == 'attestation':
        subject    = rest  # 'onatili' yoki 'adabiyot'
        amount     = config.PRICE_ATTESTATION
        retry_key  = None
        product_id = f"attestation_{subject}"
        SUBJ       = {'onatili': '📚 Ona tili', 'adabiyot': '📖 Adabiyot'}
        desc       = f"🎓 {SUBJ.get(subject, subject)} Atestatsiyasi"
    else:
        await callback.answer("❌ Noma'lum mahsulot!", show_alert=True)
        return

    # FSM ga saqlash
    await state.update_data(
        product_type=product_id,
        retry_key=retry_key,
        amount=amount,
        subject=rest if product_type == 'attestation' else None
    )

    await callback.message.edit_text(
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        f"📦 Mahsulot: {desc}\n"
        f"💰 Summa: <b>{amount:,} so'm</b>\n\n"
        f"🏦 Karta raqami:\n"
        f"<code>{config.PAYMENT_CARD}</code>\n\n"
        f"👤 Karta egasi: <b>{config.PAYMENT_OWNER}</b>\n\n"
        f"📸 To'lovni amalga oshirgach, <b>chek rasmini</b> yuboring:",
        parse_mode="HTML",
        reply_markup=cancel_keyboard()
    )
    await state.set_state(PaymentStates.waiting_for_check)
    await callback.answer()

# ══════════════════════════════════════════════
# CHEK RASMI QABUL QILISH
# ══════════════════════════════════════════════

@router.message(PaymentStates.waiting_for_check, F.photo)
async def receive_check(message: Message, state: FSMContext, bot: Bot):
    data         = await state.get_data()
    product_type = data.get('product_type', 'unknown')
    retry_key    = data.get('retry_key')
    amount       = data.get('amount', 0)
    photo_id     = message.photo[-1].file_id

    # DB ga saqlash
    purchase_id = await create_purchase(
        telegram_id=message.from_user.id,
        product_type=product_type,
        amount=amount,
        check_photo=photo_id,
        retry_key=retry_key
    )

    await state.clear()

    await message.answer(
        f"✅ <b>Chekingiz qabul qilindi!</b>\n\n"
        f"⏳ Admin tekshirib, tez orada tasdiqlaydi.\n"
        f"📲 Tasdiqlangach xabar olasiz.",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML"
    )

    # Adminlarga yuborish
    user = await get_user(message.from_user.id)
    PROD_LABELS = {
        'retry':       '🔄 Qayta urinish',
        'attestation': '🎓 Atestatsiya',
    }
    prod_short = product_type.split(":")[0] if ":" in product_type else product_type.split("_")[0]
    prod_label = PROD_LABELS.get(prod_short, product_type)

    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=photo_id,
                caption=(
                    f"💳 <b>Yangi to'lov!</b>\n\n"
                    f"👤 {user.full_name if user else 'Noma\'lum'}\n"
                    f"📱 {user.phone_number if user else '—'}\n"
                    f"🆔 {message.from_user.id}\n\n"
                    f"📦 {prod_label}\n"
                    f"💰 {amount:,} so'm\n"
                    f"🔑 {retry_key or '—'}"
                ),
                reply_markup=payment_confirm_keyboard(purchase_id),
                parse_mode="HTML"
            )
        except Exception:
            pass

@router.message(PaymentStates.waiting_for_check)
async def check_not_photo(message: Message):
    if message.text == "❌ Bekor qilish":
        from aiogram.fsm.context import FSMContext
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())
        return
    await message.answer(
        "📸 Iltimos, <b>to'lov chekining rasmini</b> yuboring:",
        parse_mode="HTML"
    )

# ══════════════════════════════════════════════
# ADMIN: TASDIQLASH / RAD ETISH
# ══════════════════════════════════════════════

@router.callback_query(F.data.startswith("confirm_pay:"))
async def confirm_payment(callback: CallbackQuery, bot: Bot):
    purchase_id = int(callback.data.split(":")[1])
    purchase    = await get_purchase_by_id(purchase_id)

    if not purchase:
        await callback.answer("❌ To'lov topilmadi!", show_alert=True)
        return

    if purchase.status != 'pending':
        await callback.answer(
            f"⚠️ Bu to'lov allaqachon: {purchase.status}",
            show_alert=True
        )
        return

    await confirm_purchase(purchase_id, callback.from_user.id)

    # Atestatsiya bo'lsa — huquq berish va format so'rash
    pt = purchase.product_type  # 'attestation_onatili' | 'retry:...'
    if pt.startswith('attestation_'):
        subject = pt.replace('attestation_', '')
        # Foydalanuvchidan format so'rash
        try:
            await bot.send_message(
                chat_id=purchase.telegram_id,
                text=(
                    f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
                    f"🎓 Atestatsiya testini qanday formatda olishni xohlaysiz?"
                ),
                reply_markup=attestation_format_keyboard(subject),
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        # Retry — to'g'ridan xabar
        try:
            await bot.send_message(
                chat_id=purchase.telegram_id,
                text=(
                    f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
                    f"🔓 Endi testni qayta boshlashingiz mumkin.\n"
                    f"📚 Fanlar menyusidan tanlang."
                ),
                reply_markup=main_menu_keyboard(),
                parse_mode="HTML"
            )
        except Exception:
            pass

    # Admin xabarini yangilash
    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n✅ <b>TASDIQLANDI</b>",
        parse_mode="HTML"
    )
    await callback.answer("✅ Tasdiqlandi!")

@router.callback_query(F.data.startswith("reject_pay:"))
async def reject_payment(callback: CallbackQuery, bot: Bot):
    purchase_id = int(callback.data.split(":")[1])
    purchase    = await get_purchase_by_id(purchase_id)

    if not purchase:
        await callback.answer("❌ To'lov topilmadi!", show_alert=True)
        return

    if purchase.status != 'pending':
        await callback.answer(
            f"⚠️ Bu to'lov allaqachon: {purchase.status}",
            show_alert=True
        )
        return

    await reject_purchase(purchase_id, callback.from_user.id)

    try:
        await bot.send_message(
            chat_id=purchase.telegram_id,
            text=(
                "❌ <b>To'lovingiz rad etildi.</b>\n\n"
                "📸 Chekni qayta yuboring yoki admin bilan bog'laning."
            ),
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.message.edit_caption(
        caption=callback.message.caption + "\n\n❌ <b>RAD ETILDI</b>",
        parse_mode="HTML"
    )
    await callback.answer("❌ Rad etildi!")

# ══════════════════════════════════════════════
# ADMIN: KUTAYOTGAN TO'LOVLAR
# ══════════════════════════════════════════════

@router.message(F.text == "💰 Kutayotgan to'lovlar")
async def pending_payments(message: Message, bot: Bot):
    if message.from_user.id not in config.ADMIN_IDS:
        return

    purchases = await get_pending_purchases()

    if not purchases:
        await message.answer("✅ Kutayotgan to'lovlar yo'q!")
        return

    await message.answer(f"⏳ <b>Kutayotgan to'lovlar: {len(purchases)} ta</b>", parse_mode="HTML")

    for purchase, user in purchases:
        PROD_LABELS = {
            'retry':       '🔄 Qayta urinish',
            'attestation': '🎓 Atestatsiya',
        }
        prod_short = purchase.product_type.split(":")[0] if ":" in purchase.product_type \
                     else purchase.product_type.split("_")[0]
        prod_label = PROD_LABELS.get(prod_short, purchase.product_type)

        try:
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=purchase.check_photo,
                caption=(
                    f"👤 {user.full_name or 'Noma\'lum'}\n"
                    f"📱 {user.phone_number or '—'}\n"
                    f"🆔 {purchase.telegram_id}\n\n"
                    f"📦 {prod_label}\n"
                    f"💰 {purchase.amount:,} so'm\n"
                    f"📅 {str(purchase.submitted_at)[:16]}"
                ),
                reply_markup=payment_confirm_keyboard(purchase.id),
                parse_mode="HTML"
            )
        except Exception as e:
            await message.answer(f"⚠️ Chek yuborishda xato: {e}")

# ══════════════════════════════════════════════
# BEKOR QILISH
# ══════════════════════════════════════════════

@router.message(PaymentStates.waiting_for_check, F.text == "❌ Bekor qilish")
async def cancel_payment(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_keyboard())

@router.callback_query(F.data == "payment:cancel")
async def cancel_payment_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_keyboard())
    await callback.answer()
