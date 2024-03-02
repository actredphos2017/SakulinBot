import telebot.types

import tgbot
from tgbot import MsgReply


class DebugFeature(tgbot.IFeature):

    def __init__(self):
        super().__init__()
        print('正在部署菜单')
        self.menu_reply = tgbot.MsgReply(
            '欢迎访问 Debug 功能',
            [
                tgbot.EventKeyboard(
                    '我是谁？',
                    'DEBUG whoami'
                ),
                tgbot.EventKeyboard(
                    '我在哪？',
                    'DEBUG whereami'
                ),
            ]
        )

    def handle_command(self, model) -> MsgReply | str | None:
        content = tgbot.separate_command_and_content(model, 'debug')
        if content is not None:
            return self.menu_reply
        return None

    def event_router(self, call: telebot.types.CallbackQuery, content) -> str | None:
        match content:
            case 'whoami':
                return (
                    'Username: {}\n'
                    'User ID: {}\n'
                    'First Name: {}\n'
                    'Last Name: {}'
                ).format(
                    call.from_user.username,
                    call.from_user.id,
                    call.from_user.first_name,
                    call.from_user.last_name
                )
            case 'whereami':
                return (
                    'Chat Type: {}\n'
                    'Chat Name: {}\n'
                    'Chat ID: {}\n'
                    'Chat Description:\n"{}"'
                ).format(
                    call.message.chat.type,
                    call.message.chat.title,
                    call.message.chat.id,
                    call.message.chat.description
                )
        return None

    def handle_event(self, call: telebot.types.CallbackQuery) -> MsgReply | str | None:
        content = tgbot.separate_event_data_and_content(call, 'DEBUG')
        if content is not None:
            res = self.event_router(call, content)
            if res is None:
                return self.menu_reply
            return tgbot.MsgReply(
                res,
                [
                    tgbot.EventKeyboard(
                        '返回菜单',
                        'DEBUG menu'
                    )
                ]
            )
        return None

    def register_commands(self) -> list[str]:
        return ['debug']
