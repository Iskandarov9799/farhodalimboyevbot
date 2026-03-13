from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_phone = State()

class MenuStates(StatesGroup):
    main    = State()
    subject = State()

class BiologiyaStates(StatesGroup):
    category   = State()
    topic      = State()
    grade      = State()
    difficulty = State()

class AttestationStates(StatesGroup):
    choose_format = State()

class PaymentStates(StatesGroup):
    waiting_for_check = State()

class AdminStates(StatesGroup):
    add_subject       = State()
    add_category      = State()
    add_subcategory   = State()
    add_difficulty    = State()
    add_is_attest     = State()
    add_order_num     = State()
    add_image         = State()
    add_text          = State()
    add_a             = State()
    add_b             = State()
    add_c             = State()
    add_d             = State()
    add_correct       = State()
    broadcast_message = State()

class EditQuestionStates(StatesGroup):
    browsing       = State()
    searching      = State()
    viewing        = State()
    edit_field     = State()
    edit_value     = State()
    confirm_delete = State()
