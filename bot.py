import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    config.validate()

    from database.connection import init_engine, init_db
    init_engine()
    await init_db()

    from keep_alive import start_web_server
    await start_web_server()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(storage=MemoryStorage())

    from handlers import registration, payment, test_handler, admin
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(payment.router)
    dp.include_router(test_handler.router)

    logger.info("🚀 Biologiya bot ishga tushdi! Admin IDs: %s", config.ADMIN_IDS)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except KeyboardInterrupt:
        pass
    finally:
        await bot.session.close()
        logger.info("🛑 Bot to'xtatildi.")

if __name__ == "__main__":
    asyncio.run(main())
