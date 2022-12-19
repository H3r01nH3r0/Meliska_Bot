from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class Keyboards:
    def __init__(self, texts: dict) -> None:
        self._texts = texts

        self.choose_lang = InlineKeyboardMarkup()

        for lang in self._texts.keys():
            if len(lang) != 2:
                continue

            self.choose_lang.add(
                InlineKeyboardButton(
                    text = self._texts[lang]["markup"],
                    callback_data = "lang_{}".format(lang)
                )
            )


    def from_str(self, text: str) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()

        for line in text.split("\n"):
            sign, url = line.split(" - ")

            markup.add(
                InlineKeyboardButton(
                    text = sign,
                    url = url
                )
            )

        markup.to_python()

        return markup

    def cancel(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()

        markup.add(
            InlineKeyboardButton(
                text = self._texts["cancel"],
                callback_data = "cancel"
            )
        )

        return markup

    def start(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()

        markup.add(InlineKeyboardButton(text='НАЧАТЬ✅', callback_data='start'))

        return markup

    def url(self, arg) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text='НАЧАТЬ ЗАРАБАТЫВАТЬ💸', url=arg))
        return markup