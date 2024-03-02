import inspect
import json
import shlex
import uuid
from typing import Callable

import requests
import telebot.types

import tgbot
import utils
from tgbot import MsgReply


class Ability:
    def __init__(
            self,
            func: Callable,
            instruction: str,
            private: bool = False,
            public: bool = True,
            admin_only: bool = False,
            show_on_help_string: str | None = None,
            show_back_to_help: bool = True
    ):
        self.func = func
        self.instruction = instruction
        self.private = private
        self.public = public
        self.admin_only = admin_only
        self.show_on_help_string = show_on_help_string
        self.show_back_to_help = show_back_to_help


class WebCraftAPIFeature(tgbot.IFeature):

    def __init__(self, hostname: str, admin_authorization: str, https: bool = True, max_auth_frequency: int = 5):
        super().__init__()
        print('组装服务器域名……')
        while hostname.endswith('/'):
            hostname = hostname[:-1]

        if hostname.startswith('https://') or hostname.startswith('http://'):
            self.hostname = hostname
        else:
            while hostname.startswith('/'):
                hostname = hostname[1:]
            self.hostname = ('https://' if https else 'http://') + hostname

        print('初始化本地数据库……')
        self.database_entrance = utils.StorageDataEntrance(
            'craft',
            'craft_init.sql'
        )
        if self.database_entrance.first_create:
            print(f'首次创建 CRAFT 数据库！已生成第一个管理员认证码: {self.create_auth_code()}')

        self.max_auth_frequency = max_auth_frequency

        print('部署能力……')
        self.admin_authorization_headers = {
            'Authorization': admin_authorization
        }
        self.abilities: dict[str, Ability] = {
            'ping': Ability(
                lambda model: self.ping(model),
                '测试服务器连接',
                show_on_help_string='Ping'
            ),
            'api': Ability(
                lambda model: self.api(model),
                '获取 API 状态',
                show_on_help_string='查看 API 状态'
            ),
            'server': Ability(
                lambda model: self.server(model),
                '获取服务器状态',
                show_on_help_string='查看服务器状态'
            ),
            'onlineplayers': Ability(
                lambda model: self.onlineplayers(model),
                '获取在线玩家列表',
                show_on_help_string='在线玩家列表'
            ),
            'auth': Ability(
                lambda model, password: self.authentication(model, password),
                '认证成为管理员',
                public=False,
                private=True,
                show_back_to_help=False
            ),
            'generatecode': Ability(
                lambda model: self.generate_auth_code(model),
                '生成一次性管理员认证码',
                public=False,
                private=True,
                show_back_to_help=False,
                admin_only=True,
                show_on_help_string='生成管理员认证码'
            ),
            'world': Ability(
                lambda model: self.world(model),
                '查看服务器世界信息',
                show_on_help_string='世界信息'
            ),
            'worldinfo': Ability(
                lambda model, worldname: self.worldinfo(model, worldname),
                '查看目标世界的信息'
            ),
            'broadcast': Ability(
                lambda model, msg: self.broadcast(model, msg),
                '向服务器发送广播（管理员）',
                admin_only=True
            ),
            'banlist': Ability(
                lambda model: self.banlist(model),
                '查看被封禁的玩家列表',
                show_on_help_string='封禁玩家列表'
            ),
            'banplayer': Ability(
                lambda model, player: self.banplayer(model, player),
                '封禁玩家（管理员）',
                admin_only=True,
                private=True
            ),
            'unbanplayer': Ability(
                lambda model, player: self.unbanplayer(model, player),
                '解封玩家（管理员）',
                admin_only=True,
                private=True
            )
        }

        print('配置帮助文档……')
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

    def is_admin(self, model) -> bool:
        send_id = model.from_user.id
        select = self.database_entrance.select('authentication_code', f'owner_id = {send_id}')
        return len(select) >= 1

    def handle_command(self, model: telebot.types.Message):
        content = tgbot.separate_command_and_content(model, 'craft')
        print(f'Craft Command:', 'menu' if len(content) == 0 else content)
        if content is not None:
            portions = list(filter(lambda item: item != '', shlex.split(content)))
            if len(portions) == 0 or portions[0] == 'help':
                return self.help(model)
            elif portions[0] in self.abilities:
                target_ability = self.abilities[portions[0]]

                in_group = tgbot.in_group(model)
                if in_group and not target_ability.public:
                    return tgbot.MsgReply(
                        f'命令 {portions[0]} 无法在群组中使用',
                        [
                            tgbot.EventKeyboard('查看帮助', 'CRAFT help')
                        ]
                    )
                elif not in_group and not target_ability.private:
                    return tgbot.MsgReply(
                        f'命令 {portions[0]} 无法在私聊中使用',
                        [
                            tgbot.EventKeyboard('查看帮助', 'CRAFT help')
                        ]
                    )

                if not self.is_admin(model) and target_ability.admin_only:
                    return tgbot.MsgReply(
                        '您无权使用该命令',
                        [
                            tgbot.EventKeyboard('查看帮助', 'CRAFT help')
                        ]
                    )

                param_num = len(inspect.signature(target_ability.func).parameters) - 1
                if (param_num + 1) == len(portions):
                    res = target_ability.func(model, *portions[1:])
                    if isinstance(res, tgbot.MsgReply) and target_ability.show_back_to_help:
                        res.events.append(tgbot.EventKeyboard('返回帮助', 'CRAFT help'))
                    elif isinstance(res, str) and target_ability.show_back_to_help:
                        res = tgbot.MsgReply(res, [tgbot.EventKeyboard('返回帮助', 'CRAFT help')])
                    return res
                else:
                    return f'命令 {portions[0]} 需要接收 {param_num} 个参数'
            else:
                return tgbot.MsgReply(
                    f'命令 {portions[0]} 不存在',
                    [
                        tgbot.EventKeyboard('查看帮助', 'CRAFT help')
                    ]
                )

        return None

    def handle_event(self, call: telebot.types.CallbackQuery) -> MsgReply | str | None:
        content = tgbot.separate_event_data_and_content(call, 'CRAFT')
        print(f'Craft Event: {content}')
        if content is not None:
            portions = list(filter(lambda item: item != '', shlex.split(content)))
            if len(portions) == 0 or portions[0] == 'help':
                return self.help(call)
            if portions[0] in self.abilities:
                target_ability = self.abilities[portions[0]]
                in_group = tgbot.in_group(call)
                if in_group and not target_ability.public:
                    return tgbot.MsgReply(
                        f'命令 {portions[0]} 无法在群组中使用',
                        [
                            tgbot.EventKeyboard('查看帮助', 'CRAFT help')
                        ]
                    )
                elif not in_group and not target_ability.private:
                    return tgbot.MsgReply(
                        f'命令 {portions[0]} 无法在私聊中使用',
                        [
                            tgbot.EventKeyboard('查看帮助', 'CRAFT help')
                        ]
                    )

                if not self.is_admin(call) and target_ability.admin_only:
                    return tgbot.MsgReply(
                        '您无权使用该命令',
                        [
                            tgbot.EventKeyboard('查看帮助', 'CRAFT help')
                        ]
                    )

                param_num = len(inspect.signature(target_ability.func).parameters) - 1
                if (param_num + 1) == len(portions):
                    res = target_ability.func(call, *portions[1:])
                    if isinstance(res, tgbot.MsgReply) and target_ability.show_back_to_help:
                        res.events.append(tgbot.EventKeyboard('返回帮助', 'CRAFT help'))
                    elif isinstance(res, str) and target_ability.show_back_to_help:
                        res = tgbot.MsgReply(res, [tgbot.EventKeyboard('返回帮助', 'CRAFT help')])
                    return res
                else:
                    return f'命令 {portions[0]} 需要接收 {param_num} 个参数'
            else:
                return tgbot.MsgReply(
                    f'命令 {portions[0]} 不存在',
                    [
                        tgbot.EventKeyboard('查看帮助', 'CRAFT help')
                    ]
                )

        return None

    def register_commands(self) -> list[str]:
        return ['craft']

    def ability_filter(self, model):
        in_group = tgbot.in_group(model)
        res = {}
        for key, ability in self.abilities.items():
            if in_group and not ability.public:
                continue
            if not in_group and not ability.private:
                continue
            if ability.admin_only and not self.is_admin(model):
                continue
            res[key] = ability

        return res

    def help(self, model):
        abilities = self.ability_filter(model)

        return tgbot.MsgReply(
            self.basic_doc + '\n' + '\n'.join(
                [f' - {command} {ability.instruction}' for command, ability in abilities.items()]
            ),
            [
                tgbot.EventKeyboard(ability.show_on_help_string, f'CRAFT {key}')
                for key, ability in abilities.items()
                if isinstance(ability.show_on_help_string, str)
            ]
        )

    def out_of_frequency(self, user_id: str):
        target_record = self.database_entrance.select('try_apply_record', f'id = {user_id}')
        if len(target_record) == 0:
            return False
        return self.max_auth_frequency - target_record[0][1] <= 0

    def record_try(self, user_id: str):
        if len(self.database_entrance.select('try_apply_record', f'id = {user_id}')) == 0:
            self.database_entrance.insert(
                'try_apply_record',
                {
                    'id': f'"{user_id}"'
                }
            )
        else:
            self.database_entrance.update(
                'try_apply_record',
                {
                    'apply_times': 'apply_times + 1'
                },
                f'id = "{user_id}"'
            )

        return self.max_auth_frequency - self.database_entrance.select('try_apply_record', f'id = "{user_id}"')[0][1]

    def authentication(self, model, password: str):
        if self.is_admin(model):
            return '您已是管理员，请勿重复认证'
        if self.out_of_frequency(model.from_user.id):
            return '您无法进行认证'
        target = self.database_entrance.select(
            'authentication_code',
            f'owner_id is null and uuid = "{password}"'
        )
        if len(target) == 0:
            frequency = self.record_try(model.from_user.id)
            return f'认证失败\n您还剩下 {frequency} 次尝试机会'
        else:
            self.database_entrance.update(
                'authentication_code',
                {
                    'owner_id': f'{model.from_user.id}'
                },
                f'uuid = "{password}"'
            )
            return '认证成功！'

    def create_auth_code(self) -> str:
        au_code = str(uuid.uuid4())
        self.database_entrance.insert('authentication_code', {
            'uuid': f'"{au_code}"'
        })
        return au_code

    def generate_auth_code(self, model):
        return f'认证码生成成功！\n{self.create_auth_code()}\n请谨慎使用！'

    def get_request(
            self,
            uri: str,
            headers: dict | None = None,
            normal_body: Callable[[dict], bool] = lambda _: True,
            normal_status: str = '200'
    ) -> dict | str:
        url = self.url(uri)
        try:
            if headers is None:
                print('GET:', url)
                response = requests.get(url, timeout=(5, 10))
            else:
                response = requests.get(url, timeout=(5, 10), headers=headers)
            if str(response.status_code) != normal_status:
                return f'响应状态码异常：{response.status_code}'
            body = response.json()
            if normal_body(body):
                return body
            else:
                print(f'服务器响应{url}异常！响应内容：{body}')
                return '服务器响应异常！'
        except requests.exceptions.Timeout:
            return '服务器连接超时！'
        except Exception as e:
            print(f'服务器响应{url}未知异常！异常内容：{e}')
            return f'未知异常！'

    def post_request(
            self,
            uri: str,
            body: dict,
            headers: dict | None = None,
            normal_body: Callable[[dict], bool] = lambda _: True,
            normal_status: str = '202'
    ) -> dict | str:
        url = self.url(uri)
        try:
            if headers is None:
                print('POST:', url)
                response = requests.post(url, json.dumps(body), timeout=(5, 10))
            else:
                response = requests.post(url, json.dumps(body), timeout=(5, 10), headers=headers)
            if str(response.status_code) != normal_status:
                return f'响应状态码异常：{response.status_code}'
            body = response.json()
            if normal_body(body):
                return body
            else:
                print(f'服务器响应{url}异常！响应内容：{body}')
                return '服务器响应异常！'
        except requests.exceptions.Timeout:
            return '服务器连接超时！'
        except Exception as e:
            print(f'服务器响应{url}未知异常！异常内容：{e}')
            return f'未知异常！'

    def ping(self, model):
        response_body = self.get_request(
            '/api/v1/ping',
            normal_body=lambda body: 'response' in body
        )
        if isinstance(response_body, str):
            return response_body
        return '服务器响应成功！响应：' + response_body['response']

    def api(self, model):

        response_body = self.get_request(
            '/api/v1/api',
            normal_body=lambda body: 'name' in body
        )
        if isinstance(response_body, str):
            return response_body
        return 'API信息：\n名称：{}\n版本：{}\n描述：{}\n作者：{}\n发布时间：{}\n网站：{}\n文档：{}'.format(
            response_body['name'],
            response_body['version'],
            response_body['description'],
            response_body['author'],
            response_body['releaseDate'],
            response_body['website'],
            response_body['documentation'],
        )

    def server(self, model):
        data = self.get_request(
            '/api/v1/server',
            normal_body=lambda body: 'serverName' in body
        )
        if isinstance(data, str):
            return data
        return '核心名称：{}\n版本：{}\nBukkit 版本：{}\nIP：{}\n端口：{}\n标题：{}\n状态：{}'.format(
            data['serverName'],
            data['serverVersion'],
            data['serverBukkitVersion'],
            '未定义' if data['serverIP'] == '' else data['serverIP'],
            data['serverPort'],
            data['serverMotd'],
            '运行中' if data['running'] else '未在运行',
        )

    def onlineplayers(self, model):
        data = self.get_request(
            '/api/v1/players/online',
            normal_body=lambda body: 'onlinePlayers' in body
        )
        if isinstance(data, str):
            return data
        if data['onlinePlayers'] == 0:
            return '当前服务器中没有玩家'
        else:
            return '当前服务器中有 {} 位玩家\n玩家列表：\n'.format(
                data['onlinePlayers']) + '\n'.join(f' - {player}' for player in data['online'])

    def world(self, model):
        data = self.get_request(
            '/api/v1/worlds',
            normal_body=lambda body: 'worldCount' in body
        )
        if isinstance(data, str):
            return data
        return tgbot.MsgReply(
            '服务器内共有 {} 个世界'.format(data['worldCount']),
            [
                tgbot.EventKeyboard(
                    worldname,
                    f'CRAFT worldinfo {worldname}'
                ) for worldname in data['worlds']
            ]
        )

    def worldinfo(self, model, worldname):
        data = self.get_request(
            f'/api/v1/worlds/{worldname}',
            normal_body=lambda body: 'name' in body
        )
        if isinstance(data, str):
            return data
        return '世界 {} 信息：\n动物生成：{}\n怪物生成：{}\n难度：{}\n世界总时间：{}\n允许 PVP：{}\n重生点：{}, {}, {}\n时间：{}\n种子：{}'.format(
            data['name'],
            data['allowAnimals'],
            data['allowMonsters'],
            data['difficulty'],
            data['gameTime'],
            data['pvp'],
            data['spawnX'],
            data['spawnY'],
            data['spawnZ'],
            data['time'],
            data['seed'],
        )

    def broadcast(self, model, msg):
        data = self.post_request(
            '/api/v1/chat/broadcast/all',
            {'message': f'[Telegram @{model.from_user.username}] {msg}'},
            headers=self.admin_authorization_headers
        )
        if isinstance(data, str):
            return data
        return '{}\n代码：{}\n消息：{}'.format(
            '发送成功' if data['success'] else '发送失败',
            data['code'],
            data['message']
        )

    def banlist(self, model):
        data = self.get_request(
            '/api/v1/banlist/players',
            normal_body=lambda body: 'bannedPlayers' in body
        )
        if isinstance(data, str):
            return data
        if data['bannedPlayers'] == 0:
            return '没有玩家被封禁'
        else:
            return '服务器共封禁了 {} 位玩家\n被封禁玩家列表：\n'.format(
                data['bannedPlayers']) + '\n'.join(f' - {player}' for player in data['players'])

    def banplayer(self, model, player):
        data = self.post_request(
            '/api/v1/banlist/players/ban',
            {
                'player': player
            },
            headers=self.admin_authorization_headers
        )
        if isinstance(data, str):
            return data
        return '{}\n代码：{}\n消息：{}'.format(
            '封禁成功' if data['success'] else '封禁失败',
            data['code'],
            data['message']
        )

    def unbanplayer(self, model, player):
        data = self.post_request(
            '/api/v1/banlist/players/pardon',
            {
                'player': player
            },
            headers=self.admin_authorization_headers
        )
        if isinstance(data, str):
            return data
        return '{}\n代码：{}\n消息：{}'.format(
            '解封成功' if data['success'] else '解封失败',
            data['code'],
            data['message']
        )
