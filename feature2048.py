import json
import random

import tgbot


class _2048Board:

    def get_empty_pos(self):
        empty_pos = []
        for i in range(0, 4):
            for j in range(0, 4):
                if self.board[i][j] == 0:
                    empty_pos.append([i, j])
        return empty_pos

    def spawn_random(self):
        num = 2 * random.randint(1, 2)
        droppable_pos = self.get_empty_pos()
        max_index = len(droppable_pos) - 1
        if max_index >= 0:
            target_pos = droppable_pos[random.randint(0, max_index)]
            self.board[target_pos[0]][target_pos[1]] = num

    def __init__(self):
        self.board = [
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        self.score = 0
        self.spawn_random()

    def status(self, msg='') -> dict:
        return {
            'game_over': self.game_is_over(),
            'score': self.score,
            'max': max(max(*i) for i in self.board),
            'board_view': '\n'.join(('   ' + ' '.join(f'{num}' for num in column)) for column in self.board),
            'msg': msg
        }

    def game_is_over(self) -> bool:
        if len(self.get_empty_pos()) > 0:
            return False

        for i in range(4):
            for j in range(3):
                if self.board[i][j] == self.board[i][j + 1] or self.board[j][i] == self.board[j + 1][i]:
                    return False

        return True

    def move_up(self):
        for j in range(4):
            for i in range(1, 4):
                if self.board[i][j] != 0:
                    for k in range(i, 0, -1):
                        if self.board[k - 1][j] == 0:
                            self.board[k - 1][j] = self.board[k][j]
                            self.board[k][j] = 0
                        elif self.board[k - 1][j] == self.board[k][j]:
                            self.board[k - 1][j] *= 2
                            self.score += self.board[k - 1][j]
                            self.board[k][j] = 0
                            break

    def move_down(self):
        for j in range(4):
            for i in range(2, -1, -1):
                if self.board[i][j] != 0:
                    for k in range(i, 3):
                        if self.board[k + 1][j] == 0:
                            self.board[k + 1][j] = self.board[k][j]
                            self.board[k][j] = 0
                        elif self.board[k + 1][j] == self.board[k][j]:
                            self.board[k + 1][j] *= 2
                            self.score += self.board[k + 1][j]
                            self.board[k][j] = 0
                            break

    def move_left(self):
        for i in range(4):
            for j in range(1, 4):
                if self.board[i][j] != 0:
                    for k in range(j, 0, -1):
                        if self.board[i][k - 1] == 0:
                            self.board[i][k - 1] = self.board[i][k]
                            self.board[i][k] = 0
                        elif self.board[i][k - 1] == self.board[i][k]:
                            self.board[i][k - 1] *= 2
                            self.score += self.board[i][k - 1]
                            self.board[i][k] = 0
                            break

    def move_right(self):
        for i in range(4):
            for j in range(2, -1, -1):
                if self.board[i][j] != 0:
                    for k in range(j, 3):
                        if self.board[i][k + 1] == 0:
                            self.board[i][k + 1] = self.board[i][k]
                            self.board[i][k] = 0
                        elif self.board[i][k + 1] == self.board[i][k]:
                            self.board[i][k + 1] *= 2
                            self.score += self.board[i][k + 1]
                            self.board[i][k] = 0
                            break

    def move(self, direction: str):
        match direction:
            case 'up':
                self.move_up()
            case 'down':
                self.move_down()
            case 'left':
                self.move_left()
            case 'right':
                self.move_right()
        self.spawn_random()


def is_direction(command: str):
    return command in ['up', 'down', 'left', 'right']


def msg_view(status):
    return '游戏结束：{}\n得分：{}\n最大块：{}\n==== 棋盘 ====\n{}\n=============\n{}'.format(
        status['game_over'],
        status['score'],
        status['max'],
        status['board_view'],
        status['msg'],
    )


class _2048Feature(tgbot.IFeature):

    def register_commands(self) -> list[str]:
        return ['2048', 'up', 'down', 'left', 'right']

    def __init__(self):
        self.board_map = {}

    def is_playing(self, key):
        return key in self.board_map

    def handle_command(self, model):
        command = model.text[1:]
        if self.is_playing(model.chat.id):
            if is_direction(command):
                self.board_map[model.chat.id].move(command)
                return msg_view(self.board_map[model.chat.id].status())

        match command:
            case '2048 start':
                self.board_map[model.chat.id] = _2048Board()
                return msg_view(self.board_map[model.chat.id].status())

        return None
