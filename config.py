import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    BOT_TOKEN:     str  = field(default_factory=lambda: os.getenv("BOT_TOKEN", ""))
    DATABASE_URL:  str  = field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    MINI_APP_URL:  str  = field(default_factory=lambda: os.getenv("MINI_APP_URL", ""))
    ADMIN_IDS:     list = field(default_factory=lambda: [
        int(x)
        for x in os.getenv("ADMIN_IDS", "")
                   .strip().strip("[]").replace(" ", "").split(",")
        if x.strip().lstrip("-").isdigit()
    ])
    PAYMENT_CARD:  str  = field(default_factory=lambda: os.getenv("PAYMENT_CARD",  "8600 0000 0000 0000"))
    PAYMENT_OWNER: str  = field(default_factory=lambda: os.getenv("PAYMENT_OWNER", "Karta egasi"))
    SOLUTION_URL:  str  = field(default_factory=lambda: os.getenv("SOLUTION_URL",  ""))

    PRICE_RETRY:       int = 5_000
    PRICE_ATTESTATION: int = 15_000
    MIN_QUESTIONS:     int = 35
    ATTESTATION_COUNT: int = 35

    SUBJECTS = {
        'biologiya': '🧬 Biologiya',
    }

    BIOLOGIYA_TOPICS = {
        'hujayra':      '🔬 Hujayra biologiyasi',
        'genetika':     '🧬 Genetika',
        'evolyutsiya':  '🦕 Evolyutsiya',
        'botanika':     '🌿 Botanika',
        'zoologiya':    '🐾 Zoologiya',
        'anatomiya':    '🫀 Inson anatomiyasi',
        'ekologiya':    '🌍 Ekologiya',
        'mikrobiologiya': '🦠 Mikrobiologiya',
    }

    GRADES = {
        '6': '6-sinf', '7': '7-sinf', '8': '8-sinf',
        '9': '9-sinf', '10': '10-sinf', '11': '11-sinf',
    }

    DIFFICULTIES = {
        'easy':   '🟢 Oson',
        'medium': "🟡 O'rta",
        'hard':   '🔴 Qiyin',
    }

    def validate(self):
        errors = []
        if not self.BOT_TOKEN:
            errors.append("❌ BOT_TOKEN — .env faylida yo'q!")
        if not self.DATABASE_URL:
            errors.append("❌ DATABASE_URL — .env faylida yo'q!")
        if not self.ADMIN_IDS:
            errors.append("❌ ADMIN_IDS — .env faylida yo'q!")
        if not self.MINI_APP_URL:
            errors.append("⚠️  MINI_APP_URL — .env faylida yo'q")
        if errors:
            for e in errors:
                print(e)
            if any("❌" in e for e in errors):
                raise SystemExit("Bot ishga tushmadi — .env ni to'ldiring!")

config = Config()
