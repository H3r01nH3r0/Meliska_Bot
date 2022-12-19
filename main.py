from aiogram import Bot, Dispatcher, types, filters, executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from db import DataBase
from utils import get_config, save_config, str2file
from time import time
from asyncio import sleep
from keyboards import Keyboards

config_filename = "config.json"
config = get_config(config_filename)
keyboards = Keyboards(texts=config["texts"])
db = DataBase(config["db_url"], config["db_name"])
bot = Bot(token=config["bot_token"], parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MongoStorage(db_name=config["db_name"], uri=config["db_url"]))
owners_filter = filters.IDFilter(user_id=config["owners"])

class Form(StatesGroup):
    lang = State()
    mailing = State()
    mailing_markup = State()
    show = State()
    show_markup = State()

class UsersMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super(UsersMiddleware, self).__init__()

    async def on_pre_process_message(self, message: types.Message, data: dict) -> None:
        user = {}
        if message.chat.type == types.ChatType.PRIVATE:
            user_id = message.chat.id
            user = db.get_user(user_id)
            if not user:
                db.add_user(user_id)
                user = db.get_user(user_id)
        data["user"] = user

async def on_shutdown(dp: Dispatcher) -> None:
    save_config(config_filename, config)
    db.close()
    await dp.storage.close()
    await dp.storage.wait_closed()

@dp.message_handler(owners_filter, commands=["users", "count"])
async def owners_users_command_handler(message: types.Message) -> None:
    count = db.get_users_count()
    await message.answer(text=config["texts"]["users_count"].format(count=count))


@dp.message_handler(owners_filter, commands=["export"])
async def owners_export_command_handler(message: types.Message) -> None:
    msg = await message.answer(text=config["texts"]["please_wait"])
    file = str2file(" ".join([str(user["user_id"]) for user in db.get_user()]), "users.txt")
    try:
        await message.answer_document(file)
    except:
        await message.answer(text=config["texts"]["no_users"])
    await msg.delete()

@dp.message_handler(owners_filter, commands=["mail", "mailing"])
async def owners_mailing_command_handler(message: types.Message) -> None:

    await Form.mailing.set()

    await message.answer(
        text=config["texts"]["enter_mailing"],
        reply_markup=keyboards.cancel()
    )


@dp.message_handler(content_types=types.ContentType.all(), state=Form.mailing)
async def owners_process_mailing_handler(message: types.Message, state: FSMContext) -> None:

    async with state.proxy() as data:
        data["message"] = message.to_python()

    await Form.mailing_markup.set()

    await message.answer(
        config["texts"]["enter_mailing_markup"],
        reply_markup=keyboards.cancel()
    )


@dp.message_handler(state=Form.mailing_markup)
async def owners_process_mailing_markup_handler(message: types.Message, state: FSMContext) -> None:

    if message.text not in ["-", "."]:
        try:
            markup = keyboards.from_str(message.text)

        except:
            await message.answer(
                text=config["texts"]["incorrect_mailing_markup"],
                reply_markup=keyboards.cancel()
            )

            return

    else:
        markup = types.InlineKeyboardMarkup()

    markup = markup.to_python()

    async with state.proxy() as data:
        _message = data["message"]

    total = 0
    sent = 0
    unsent = 0

    await state.finish()

    await message.answer(config["texts"]["start_mailing"])

    start = time()

    kwargs = {
        "from_chat_id": _message["chat"]["id"],
        "message_id": _message["message_id"],
        "reply_markup": markup
    }

    for user in db.get_user():
        kwargs["chat_id"] = user["user_id"]

        try:
            await bot.copy_message(**kwargs)
            sent += 1

        except:
            unsent += 1

        total += 1

        await sleep(config["sleep_time"])

    await message.answer(
        config["texts"]["mailing_stats"].format(
            total=total,
            sent=sent,
            unsent=unsent,
            time=round(time() - start, 3)
        )
    )

@dp.message_handler(owners_filter, commands=["add_url"])
async def owners_add_channel_command_handler(message: types.Message) -> None:


    args = message.text.split(" ")[1:]

    if len(args) < 1:
        await message.answer(text=config["texts"]["incorrect_value"])
        return

    config["urls"]["url"] = args[0]
    save_config(config_filename, config)

    await message.answer(text=config["texts"]["saved"])

@dp.message_handler(owners_filter, commands=["remove_all_urls"])
async def owners_add_channel_command_handler(message: types.Message) -> None:

    config["urls"].clear()
    save_config(config_filename, config)

    await message.answer(text=config["texts"]["saved"])


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message) -> None:

    await message.answer(
        text='Привет, ты активировал этого бота не случайно😄\nТы думаешь если ты школьник или студент, то не сможешь '
             'заработать и быть независимым?🥲\n- Это не так, ТЕБЕ НУЖЕН ВСЕГО 1₽😱\n\nДорогие подарки 🎁\nБаловать себя🤤'
             'Покупать все что захочешь😎\nПомогать родителям и близким👨‍👩‍👧‍👦\nДоказать друзьям, что ТЫ ВСЕ МОЖЕШЬ😉\n'
             'Позволить себе ВСЕ‼️\n\nИ повторюсь, тебе нужен всего 1₽, чтобы начать:)\nЕсли не получится, все равно '
             'ничего не теряешь😱\n\nСкорее нажимай «НАЧАТЬ✅» и измени СВОЮ жизнь в лучшую сторону👇🏻',
        reply_markup=keyboards.start()
    )

@dp.callback_query_handler(state="*")
async def callback_query_handler(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await state.finish()

    args = callback_query.data.split("_")

    if args[0] == "cancel":
        await callback_query.message.edit_text(
            text = config["texts"]["cancelled"]
        )

    elif callback_query.data == 'start':
        await bot.send_message(callback_query.from_user.id,
                               text='8/10 человек не доходят до этого шага, ты молодец, жизнь любит целеустремлённых '
                                    'людей💸\n\nЯ добыла секретный проект, с помощью которого может заработать каждый😉'
                                    '\n\nВсё, слишком много слов…\nНиже оставляю ссылку, нажимай на «НАЧАТЬ '
                                    'ЗАРАБАТЫВАТЬ💸» и меняй свою жизнь в лучшую сторону\nПереходи👇🏻',
                               reply_markup=keyboards.url(config["urls"]["url"]))

dp.middleware.setup(UsersMiddleware())


if __name__ == "__main__":
    executor.start_polling(dispatcher=dp, skip_updates=False, on_shutdown=on_shutdown)