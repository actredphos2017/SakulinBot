import io
import sys

import tgbot
from tgbot import MsgReply


def execute_code(code):
    origin_output = None
    try:
        origin_output = sys.stdout
        out_stream = io.StringIO()
        sys.stdout = out_stream
        exec(code, {}, {})
        res = out_stream.getvalue()
    except Exception as e:
        res = str(e)
    finally:
        sys.stdout = origin_output

    return res


class CodeRunnerFeature(tgbot.IFeature):

    def __init__(self):
        super().__init__()

    def handle_event(self, call) -> MsgReply | str | None:
        return None

    def handle_command(self, model):
        content = tgbot.separate_command_and_content(model, 'runpy')
        if content is not None:
            print(f'{model.chat.id}会话运行命令：\n{content}\n\n')
            return f'输出：\n{execute_code(content)}'

        return None

    def register_commands(self) -> list[str]:
        return ['runpy']
