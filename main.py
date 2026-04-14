import asyncio
from aiogram import Bot
from echo import msg
import Database  # Вызывает init_db() при импорте

async def main() -> None:
    token = "" # Вставьте ваш токен от @BotFather
    bot = Bot(token=token)
    await msg.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())