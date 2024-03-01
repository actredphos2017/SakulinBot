import shlex

import tgbot
from tgbot import MsgReply, EventKeyboard


class TestFeature(tgbot.IFeature):

    def handle_command(self, model) -> MsgReply | str | None:
        content = tgbot.separate_command_and_content(model, 'test')
        if content is not None:
            return MsgReply(
                'Hello World',
                [
                    EventKeyboard('Click Me!', 'TEST_EVENT')
                ]
            )
        return None

    def handle_event(self, call) -> MsgReply | str | None:
        if call.data == 'TEST_EVENT':
            return 'You Click The Button!'
        return None

    def register_commands(self) -> list[str]:
        return ['test']


def split_special_string(s):
    # 使用 shlex.split() 方法分割字符串
    return shlex.split(s)


if __name__ == '__main__':
    print(split_special_string('abc b"bcd\\" ead" ge'))
