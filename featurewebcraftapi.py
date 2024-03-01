import inspect
import json
import shlex
from typing import Callable

import tgbot
import requests

from tgbot import MsgReply
from utils import get_storage


class Ability:
    def __init__(self, func: Callable, instruction: str, private=False, public=True, admin_only=False):
        self.func = func
        self.instruction = instruction
        self.private = private
        self.public = public
        self.admin_only = admin_only


class WebCraftAPIFeature(tgbot.IFeature):

    def __init__(self, hostname: str, https: bool = True):
        while hostname.endswith('/'):
            hostname = hostname[:-1]
        while hostname.startswith('/'):
            hostname = hostname[1:]
        self.hostname = ('https://' if https else 'http://') + hostname

        self.abilities: dict[str, Ability] = {
            'help': Ability(
                lambda model: self.help(model),
                '显示帮助文档',
                private=True
            ),
            'ping': Ability(
                lambda model: self.ping(model),
                '测试服务器连接'
            ),
            'api': Ability(
                lambda model: self.api(model),
                '获取 API 状态'
            ),
            'server': Ability(
                lambda model: self.server(model),
                '获取服务器状态'
            ),
            'onlineplayers': Ability(
                lambda model: self.onlineplayers(model),
                '获取在线玩家列表'
            )
        }

        self.basic_doc = '\n'.join(
            [
                '本机器人专属于 Minecraft 群组 “红石巧构”',
                '使用 /craft <命令> [参数] 来获取服务器相关信息',
                '使用英文双引号能让参数内容支持空格',
                '例如 /craft broadcast "Hello World"',
                '',
                '可用命令如下'
            ]
        )

    def url(self, uri: str):
        return self.hostname + uri

    def is_admin(self, model):
        return True

    def handle_command(self, model):
        content = tgbot.separate_command_and_content(model, 'craft')
        print(f'Craft Feature: {content}')
        if content is not None:
            portions = list(filter(lambda item: item != '', shlex.split(content)))
            if len(portions) == 0:
                return self.help(model)
            elif portions[0] in self.abilities:
                target_ability = self.abilities[portions[0]]

                in_group = tgbot.in_group(model)
                if in_group and not target_ability.public:
                    return f'命令 {portions[0]} 无法在群组中使用'
                elif not in_group and not target_ability.private:
                    return f'命令 {portions[0]} 无法在私聊中使用'

                if not self.is_admin(model) and target_ability.admin_only:
                    return f'您无权使用该命令'

                param_num = len(inspect.signature(target_ability.func).parameters) - 1
                if (param_num + 1) == len(portions):
                    return target_ability.func(model, *portions[1:])
                else:
                    return f'命令 {portions[0]} 需要接收 {param_num} 个参数'
            else:
                return f'命令 {portions[0]} 不存在'

        return None

    def handle_event(self, call) -> MsgReply | str | None:
        content = tgbot.separate_event_data_and_content(call, 'CRAFT')
        print(f'Craft Event: {content}')
        if content is not None:
            portions = list(filter(lambda item: item != '', shlex.split(content)))
            if portions[0] in self.abilities:
                target_ability = self.abilities[portions[0]]
                in_group = tgbot.in_group(call)
                if in_group and not target_ability.public:
                    return f'命令 {portions[0]} 无法在群组中使用'
                elif not in_group and not target_ability.private:
                    return f'命令 {portions[0]} 无法在私聊中使用'

                if not self.is_admin(call) and target_ability.admin_only:
                    return f'您无权使用该命令'

                param_num = len(inspect.signature(target_ability.func).parameters) - 1
                if (param_num + 1) == len(portions):
                    return target_ability.func(call, *portions[1:])
                else:
                    return f'命令 {portions[0]} 需要接收 {param_num} 个参数'
            else:
                return f'命令 {portions[0]} 不存在'

        return None

    def register_commands(self) -> list[str]:
        return ['craft']

    def help(self, model):

        return tgbot.MsgReply(
            self.basic_doc + '\n' + '\n'.join(
                [f' - {command} {ability.instruction}' for command, ability in self.abilities.items() if ability.public]
                if tgbot.in_group(model) else
                [f' - {command} {ability.instruction}' for command, ability in self.abilities.items() if
                 ability.private]
            ),
            [
                tgbot.EventKeyboard('Ping', 'CRAFT ping'),
                tgbot.EventKeyboard('查询 API 状态', 'CRAFT api'),
                tgbot.EventKeyboard('查询服务器状态', 'CRAFT server'),
                tgbot.EventKeyboard('查询在线玩家', 'CRAFT onlineplayers'),
            ]
        )

    def ping(self, model):
        try:
            response = requests.get(self.url('/api/v1/ping'), timeout=(5, 10))
            if str(response.status_code) != '200':
                return f'响应状态码异常：{response.status_code}'
            body = response.json()
            if 'response' in body:
                return tgbot.MsgReply(f'服务器响应成功！响应：' + body['response'], [
                    tgbot.EventKeyboard('帮助', 'CRAFT help')
                ])
            else:
                return f'服务器响应异常！响应内容：' + body
        except requests.exceptions.Timeout:
            return '服务器连接超时！'
        except Exception as e:
            return f'未知异常：\n{e}'

    def api(self, model):
        try:
            response = requests.get(self.url('/api/v1/api'), timeout=(5, 10))
            if str(response.status_code) != '200':
                return f'响应状态码异常：{response.status_code}'
            data = response.json()
            if 'name' in data:
                return tgbot.MsgReply(
                    '服务器响应成功！\nAPI信息：\n名称：{}\n版本：{}\n描述：{}\n作者：{}\n发布时间：{}\n网站：{}\n文档：{}'.format(
                        data['name'],
                        data['version'],
                        data['description'],
                        data['author'],
                        data['releaseDate'],
                        data['website'],
                        data['documentation'],
                    ), [
                        tgbot.EventKeyboard('帮助', 'CRAFT help')
                    ]
                )
            else:
                return f'服务器响应异常！响应内容：' + data
        except requests.exceptions.Timeout:
            return '服务器连接超时！'
        except Exception as e:
            return f'未知异常：\n{e}'

    def server(self, model):
        try:
            response = requests.get(self.url('/api/v1/server'), timeout=(5, 10))
            if str(response.status_code) != '200':
                return f'响应状态码异常：{response.status_code}'
            data = response.json()
            if 'serverName' in data:
                return tgbot.MsgReply(
                    '服务器响应成功！\n核心名称：{}\n版本：{}\nBukkit 版本：{}\nIP：{}\n端口：{}\n标题：{}\n状态：{}'.format(
                        data['serverName'],
                        data['serverVersion'],
                        data['serverBukkitVersion'],
                        '未定义' if data['serverIP'] == '' else data['serverIP'],
                        data['serverPort'],
                        data['serverMotd'],
                        '运行中' if data['running'] else '未在运行',
                    ), [
                        tgbot.EventKeyboard('帮助', 'CRAFT help')
                    ]
                )
            else:
                return f'服务器响应异常！响应内容：' + data
        except requests.exceptions.Timeout:
            return '服务器连接超时！'
        except Exception as e:
            return f'未知异常：\n{e}'

    def onlineplayers(self, model):
        try:
            response = requests.get(self.url('/api/v1/players/online'), timeout=(5, 10))
            if str(response.status_code) != '200':
                return f'响应状态码异常：{response.status_code}'
            data = response.json()
            if 'onlinePlayers' in data:
                if data['onlinePlayers'] == 0:
                    return tgbot.MsgReply(
                        '服务器响应成功！\n当前服务器中没有玩家', [
                            tgbot.EventKeyboard('帮助', 'CRAFT help')
                        ]
                    )
                else:
                    return tgbot.MsgReply(
                        '服务器响应成功！\n当前服务器中有 {} 位玩家\n玩家列表：\n'.format(
                            data['onlinePlayers']) + '\n'.join(f' - {player}' for player in data['online']), [
                            tgbot.EventKeyboard('帮助', 'CRAFT help')
                        ]
                    )
            else:
                return f'服务器响应异常！响应内容：' + data
        except requests.exceptions.Timeout:
            return '服务器连接超时！'
        except Exception as e:
            return f'未知异常：\n{e}'
