from aiogram import Router, types

router = Router()


@router.message()
async def ignore_non_topic(message: types.Message) -> None:
    if message.text and message.text.strip() == "/start":
        await message.reply("AI Futures Signal — Official is running.")
