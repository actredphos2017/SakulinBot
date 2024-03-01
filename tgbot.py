import re

import telebot

from abc import abstractmethod


def separate_command_and_content(model, target_command) -> str | None:
    if re.split(r'\s', model.text)[0] == f'/{target_command}':
        return model.text[len(target_command) + 2:]
    return None


def separate_event_data_and_content(call, target_event) -> str | None:
    if re.split(r'\s', call.data)[0] == target_event:
        return call.data[len(target_event) + 1:]
    return None


def in_group(model) -> bool:
    if isinstance(model, telebot.types.CallbackQuery):
        return model.message.chat.type != 'private'
    elif isinstance(model, telebot.types.Message):
        return model.chat.type != 'private'
    else:
        print('Unknown Model!')
        raise Exception('Unknown Model!')


class EventKeyboard:
    def __init__(self, title, event):
        self.title = title
        self.event = event


class MsgReply:
    def __init__(self, msg, events: list[EventKeyboard] | None = None):
        self.msg = msg
        self.events = events


class IFeature:
    @abstractmethod
    def handle_command(self, model) -> MsgReply | str | None:
        return None

    @abstractmethod
    def handle_event(self, call) -> MsgReply | str | None:
        return None

    @abstractmethod
    def register_commands(self) -> list[str]:
        return []


class BotBuilder:
    def __init__(self):
        self.feature_list = []
        self.commands = set()
        self.start = None

    def route_command(self, model) -> MsgReply | str | None:
        for feature in self.feature_list:
            try:
                feature_response = feature.handle_command(model)
                if feature_response is not None:
                    return feature_response
            except:
                continue

        return None

    def route_event(self, call) -> MsgReply | str | None:
        for feature in self.feature_list:
            try:
                feature_response = feature.handle_event(call)
                if feature_response is not None:
                    return feature_response
            except:
                continue

        return None

    def use(self, feature: IFeature):
        self.feature_list.append(feature)
        for cmd in feature.register_commands():
            self.commands.add(cmd)
        return self

    def telegram(self, token: str):
        bot = telebot.TeleBot(token)

        @bot.message_handler(commands=list(self.commands))
        def handle_command(msg_model):
            response = self.route_command(msg_model)
            if response is not None:
                if isinstance(response, str):
                    bot.reply_to(msg_model, response)
                elif response.events is None or len(response.events) == 0:
                    bot.reply_to(msg_model, response.msg)
                else:
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    for item in response.events:
                        keyboard.add(telebot.types.InlineKeyboardButton(item.title, callback_data=item.event))
                    bot.reply_to(msg_model, response.msg, reply_markup=keyboard)

        @bot.callback_query_handler(func=lambda callback: True)
        def handle_event(call):
            response = self.route_event(call)
            if response is not None:
                if isinstance(response, str):
                    bot.send_message(call.message.chat.id, response)
                elif response.events is None or len(response.events) == 0:
                    bot.send_message(call.message.chat.id, response.msg)
                else:
                    keyboard = telebot.types.InlineKeyboardMarkup()
                    for item in response.events:
                        keyboard.add(telebot.types.InlineKeyboardButton(item.title, callback_data=item.event))
                    bot.send_message(call.message.chat.id, response.msg, reply_markup=keyboard)
                bot.delete_message(call.message.chat.id, call.message.message_id)

        self.start = lambda: bot.infinity_polling()
        return self

    def run(self):
        if self.start is None:
            raise Exception('Robot Not Loaded')
        print('Robot Service Start!')
        self.start()


def build_bot(features: list[IFeature], bot_meta: dict):
    res = BotBuilder()
    for feature in features:
        res.use(feature)

    if 'type' in bot_meta:
        match bot_meta['type']:
            case 'telegram':
                res.telegram(bot_meta['token'])

    return res
