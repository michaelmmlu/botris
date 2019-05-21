import pygame, sys
import numpy as np

colors = [
    (44, 44, 43),
    (114, 242, 240),
    (34, 70, 240),
    (237, 161, 50),
    (239, 241, 45),
    (127, 241, 23),
    (164, 81, 242),
    (234, 63, 51),
    (47, 47, 47)
]

tetrominos = np.array([
    np.array([[0, 0, 0, 0],
              [1, 1, 1, 1],
              [0, 0, 0, 0],
              [0, 0, 0, 0]]),
    np.array([[2, 0, 0],
              [2, 2, 2],
              [0, 0, 0]]),
    np.array([[0, 0, 3],
              [3, 3, 3],
              [0, 0, 0]]),
    np.array([[4, 4],
              [4, 4]]),
    np.array([[0, 5, 5],
              [5, 5, 0],
              [0, 0, 0]]),
    np.array([[0, 6, 0],
              [6, 6, 6],
              [0, 0, 0]]),
    np.array([[7, 7, 0],
              [0, 7, 7],
              [0, 0, 0]])
])

def rotate_clockwise(t):
    return np.rot90(t, 3)

def rotate_counterclockwise(t):
    return np.rot90(t)

def delete_row(field, row_num):
    field.pop(row_num)

def add_empty_row(field, num_rows):
    for _ in range(num_rows):
        field.insert(0, [0 for _ in range(len(field[0]))])

def join_matrices(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            if val != 0:
                mat1[cy + off_y - 1][cx + off_x] += val
    return mat1

board_width = 10
board_height = 20
cell_size = 18
maxfps = 60

class Botris(object):

    def __init__(self):
        pygame.init()
        pygame.key.set_repeat(250, 25)
        self.width = cell_size * (board_width + 6)
        self.height = cell_size * board_height
        self.rlim = cell_size * board_width
        self.background = [[8 if x % 2 == y % 2 else 0 for x in range(board_width)] for y in range(board_height)]
        self.board = [[0 for _ in range(board_width)] for _ in range(board_height)]
        self.default_font = pygame.font.Font(pygame.font.get_default_font(), 12)
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.event.set_blocked(pygame.MOUSEMOTION)

        self.init_game()
        self.hold_tet = None
        self.hold_used = False

    def init_game(self):
        self.bag = np.copy(tetrominos)
        np.random.shuffle(self.bag)
        self.curr_tet = self.bag[0]
        self.tet_x = int(board_width / 2 - len(self.curr_tet[0]) / 2)
        self.tet_y = 0
        self.bag = np.delete(self.bag, 0)
        self.next_tet = self.bag[0]
        self.bag = np.delete(self.bag, 0)
        self.level = 1
        self.score = 0
        self.lines = 0
        pygame.time.set_timer(pygame.USEREVENT + 1, 1000)

    def spawn_random_tet(self):
        if self.bag.size == 0:
            self.bag = np.copy(tetrominos)
            np.random.shuffle(self.bag)
        self.curr_tet = self.next_tet
        self.tet_x = int(board_width / 2 - len(self.curr_tet[0]) / 2)
        self.tet_y = 0
        self.next_tet = self.bag[0]
        self.bag = np.delete(self.bag, 0)

    def check_collision(self, t, offset):
        off_x, off_y = offset
        for cy, row in enumerate(t):
            for cx, cell in enumerate(row):
                if not cell:
                    continue
                y = cy + off_y
                x = cx + off_x
                if y >= board_height or x < 0 or x >= board_width:
                    return True
                if y < 0:
                    continue
                if self.board[y][x]:
                    return True
        return False

    def get_ghost_loc(self):
        temp_y = self.tet_y
        while not self.check_collision(self.curr_tet, (self.tet_x, temp_y)):
            temp_y += 1
        temp_y -= 1
        return (self.tet_x, temp_y)

    def display_msg(self, msg, topleft):
        x, y = topleft
        for line in msg.splitlines():
            self.screen.blit(self.default_font.render(line, False, (255, 255, 255), (0, 0, 0)), (x, y))
            y += 14

    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msgimage = self.default_font.render(line, False, (255, 255, 255), (0, 0, 0))
            msgimcenterx, msgimcetery = msgimage.get_size()
            msgimcenterx //= 2
            msgimcentery //= 2
            self.screen.blit(msg_image, (self.width // 2 - msgimcenterx, self.height // 2 - msgimcentery + i * 22))

    def draw_matrix(self, matrix, offset):
        off_x, off_y = offset
        for y, row in enumerate(matrix):
            for x, cell in enumerate(row):
                if cell:
                    shape = pygame.Rect((off_x + x) * cell_size, (off_y + y) * cell_size, cell_size, cell_size)
                    pygame.draw.rect(self.screen, colors[cell], shape, 0)

    def move(self, delta_x):
        if not self.gameover and not self.paused:
            new_x = self.tet_x + delta_x
            if not self.check_collision(self.curr_tet, (new_x, self.tet_y)):
                self.tet_x = new_x

    def drop(self):
        if not self.gameover and not self.paused:
            self.tet_y += 1
            if self.check_collision(self.curr_tet, (self.tet_x, self.tet_y)):
                self.board = join_matrices(self.board, self.curr_tet, (self.tet_x, self.tet_y))
                self.prev_tet = self.curr_tet
                self.spawn_random_tet()
                lines_deleted = 0
                while True:
                    for i, row in enumerate(self.board):
                        if 0 not in row:
                            delete_row(self.board, i)
                            lines_deleted += 1
                            break
                    else:
                        break
                if lines_deleted:
                    self.lines += lines_deleted
                    add_empty_row(self.board, lines_deleted)
                    scores = [100, 300, 500, 800]
                    self.score += scores[lines_deleted - 1] * self.level
                self.hold_used = False

    def hard_drop(self):
        if not self.gameover and not self.paused:
            while not self.check_collision(self.curr_tet, (self.tet_x, self.tet_y)):
                self.tet_y += 1
            self.tet_y -= 1
            self.drop()

    def reorient_tet(self):
        for tet in tetrominos:
            for _ in range(4):
                self.hold_tet = rotate_clockwise(self.hold_tet)
                if np.array_equal(self.hold_tet, tet):
                    return
        return

    def hold(self):
        if not self.gameover and not self.paused and not self.hold_used:
            if self.hold_tet is None:
                self.hold_tet = self.curr_tet
                self.spawn_random_tet()
            else:
                self.hold_tet, self.curr_tet = self.curr_tet, self.hold_tet
            self.reorient_tet()
            self.tet_x = int(board_width / 2 - len(self.curr_tet[0]) / 2)
            self.tet_y = 0
            self.hold_used = True

    def rotate_tet(self):
        if not self.gameover and not self.paused:
            new_tet = rotate_clockwise(self.curr_tet)
            if not self.check_collision(new_tet, (self.tet_x, self.tet_y)):
                self.curr_tet = new_tet

    def quit(self):
        self.center_msg("Exiting...")
        pygame.display.update()
        sys.exit()

    def toggle_pause(self):
        self.paused = not self.paused

    def start_game(self):
        if self.gameover:
            self.init_game()
            self.gameover = False

    def run(self):
        key_actions = {
			'ESCAPE':	self.quit,
			'LEFT':		lambda:self.move(-1),
			'RIGHT':	lambda:self.move(+1),
			'DOWN':		self.drop,
			'UP':		self.rotate_tet,
			'p':		self.toggle_pause,
			'q':	    self.start_game,
            'SPACE':    self.hard_drop,
            'LSHIFT':   self.hold,
		}

        self.gameover = False
        self.paused = False

        clock = pygame.time.Clock()

        while True:
            self.screen.fill((0, 0, 0))
            pygame.draw.line(self.screen, (255, 255, 255), (self.rlim + 1, 0), (self.rlim + 1, self.height - 1))
            self.display_msg("Next:", (self.rlim + cell_size, 2))
            self.display_msg("Score: %d\n\nLevel: %d\nLines: %d" % (self.score, self.level, self.lines), (self.rlim + cell_size, cell_size * 5))
            self.draw_matrix(self.background, (0, 0))
            self.draw_matrix(self.board, (0, 0))
            self.draw_matrix(self.curr_tet, (self.tet_x, self.tet_y))
            self.draw_matrix(self.next_tet, (board_width + 1, 2))
            self.draw_matrix(self.curr_tet, self.get_ghost_loc())
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.USEREVENT + 1:
                    self.drop()
                elif event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    for key in key_actions:
                        if event.key == eval("pygame.K_" + key):
                            key_actions[key]()

            clock.tick(maxfps)

if __name__ == '__main__':
    game = Botris()
    game.run()
