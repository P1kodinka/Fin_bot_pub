import asyncio
from aiogram import Bot

from echo import msg


async def main() -> None:  # Инициализация пулинг-токена
    token = "" #Токен с Bot_father
    await msg.start_polling(Bot(token))


if __name__ == "__main__":  # Мэйн инициализация событий
    asyncio.run(main())
