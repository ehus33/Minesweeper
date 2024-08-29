from tkinter import *
from tkinter import messagebox as msgBox
from collections import deque
import random
import platform
from datetime import datetime

BOARD_WIDTH = 10
BOARD_HEIGHT = 10

STATUS_HIDDEN = 0
STATUS_REVEALED = 1
STATUS_MARKED = 2

LEFT_CLICK_EVENT = "<Button-1>"
RIGHT_CLICK_EVENT = "<Button-2>" if platform.system() == 'Darwin' else "<Button-3>"

app_window = None

class MinesweeperApp:

    def __init__(self, root_window):

        self.image_assets = {
            "default": PhotoImage(file="images/tile_plain.gif"),
            "revealed": PhotoImage(file="images/tile_clicked.gif"),
            "bomb": PhotoImage(file="images/tile_mine.gif"),
            "mark": PhotoImage(file="images/tile_flag.gif"),
            "error": PhotoImage(file="images/tile_wrong.gif"),
            "numbers": []
        }
        for i in range(1, 9):
            self.image_assets["numbers"].append(PhotoImage(file="images/tile_" + str(i) + ".gif"))

        self.root_window = root_window
        self.main_frame = Frame(self.root_window)
        self.main_frame.pack()

        self.status_labels = {
            "time": Label(self.main_frame, text="00:00:00"),
            "mines": Label(self.main_frame, text="Mines: 0"),
            "marks": Label(self.main_frame, text="Marks: 0")
        }
        self.status_labels["time"].grid(row=0, column=0, columnspan=BOARD_HEIGHT)
        self.status_labels["mines"].grid(row=BOARD_WIDTH + 1, column=0, columnspan=int(BOARD_HEIGHT / 2))
        self.status_labels["marks"].grid(row=BOARD_WIDTH + 1, column=int(BOARD_HEIGHT / 2) - 1, columnspan=int(BOARD_HEIGHT / 2))

        self.initialize_game()
        self.refresh_timer()

    def create_board(self):
        self.marked_tiles = 0
        self.correct_marks = 0
        self.revealed_tiles = 0
        self.start_time = None

        self.board = dict({})
        self.total_bombs = 0

        x = 0
        while x < BOARD_WIDTH:
            y = 0
            while y < BOARD_HEIGHT:
                if y == 0:
                    self.board[x] = {}

                tile_id = str(x) + "_" + str(y)
                has_bomb = False

                tile_img = self.image_assets["default"]

                if random.uniform(0.0, 1.0) < 0.1:
                    has_bomb = True
                    self.total_bombs += 1

                tile = {
                    "id": tile_id,
                    "has_bomb": has_bomb,
                    "status": STATUS_HIDDEN,
                    "position": {"x": x, "y": y},
                    "button": Button(self.main_frame, image=tile_img),
                    "nearby_bombs": 0
                }

                tile["button"].bind(LEFT_CLICK_EVENT, self.handle_left_click(x, y))
                tile["button"].bind(RIGHT_CLICK_EVENT, self.handle_right_click(x, y))
                tile["button"].grid(row=x + 1, column=y)

                self.board[x][y] = tile
                y += 1
            x += 1

        x = 0
        while x < BOARD_WIDTH:
            y = 0
            while y < BOARD_HEIGHT:
                bomb_count = 0
                for neighbor in self.find_neighbors(x, y):
                    bomb_count += 1 if neighbor["has_bomb"] else 0
                self.board[x][y]["nearby_bombs"] = bomb_count
                y += 1
            x += 1

    def initialize_game(self):
        self.create_board()
        self.update_status_labels()

    def update_status_labels(self):
        self.status_labels["marks"].config(text="Marks: " + str(self.marked_tiles))
        self.status_labels["mines"].config(text="Mines: " + str(self.total_bombs))

    def end_game(self, victory):
        x = 0
        while x < BOARD_WIDTH:
            y = 0
            while y < BOARD_HEIGHT:
                if self.board[x][y]["has_bomb"] == False and self.board[x][y]["status"] == STATUS_MARKED:
                    self.board[x][y]["button"].config(image=self.image_assets["error"])
                if self.board[x][y]["has_bomb"] == True and self.board[x][y]["status"] != STATUS_MARKED:
                    self.board[x][y]["button"].config(image=self.image_assets["bomb"])
                y += 1
            x += 1

        self.root_window.update()

        message = "You Win! Play again?" if victory else "You Lose! Play again?"
        response = msgBox.askyesno("Game Over", message)
        if response:
            self.initialize_game()
        else:
            self.root_window.quit()

    def refresh_timer(self):
        time_text = "00:00:00"
        if self.start_time is not None:
            elapsed_time = datetime.now() - self.start_time
            time_text = str(elapsed_time).split('.')[0]
            if elapsed_time.total_seconds() < 36000:
                time_text = "0" + time_text
        self.status_labels["time"].config(text=time_text)
        self.main_frame.after(100, self.refresh_timer)

    def find_neighbors(self, x, y):
        neighbors = []
        neighbor_positions = [
            {"x": x - 1, "y": y - 1},
            {"x": x - 1, "y": y},
            {"x": x - 1, "y": y + 1},
            {"x": x, "y": y - 1},
            {"x": x, "y": y + 1},
            {"x": x + 1, "y": y - 1},
            {"x": x + 1, "y": y},
            {"x": x + 1, "y": y + 1},
        ]
        for pos in neighbor_positions:
            try:
                neighbors.append(self.board[pos["x"]][pos["y"]])
            except KeyError:
                pass
        return neighbors

    def handle_left_click(self, x, y):
        return lambda Button: self.process_left_click(self.board[x][y])

    def handle_right_click(self, x, y):
        return lambda Button: self.process_right_click(self.board[x][y])

    def process_left_click(self, tile):
        if self.start_time is None:
            self.start_time = datetime.now()

        if tile["has_bomb"]:
            self.end_game(False)
            return

        if tile["nearby_bombs"] == 0:
            tile["button"].config(image=self.image_assets["revealed"])
            self.clear_adjacent_tiles(tile["id"])
        else:
            tile["button"].config(image=self.image_assets["numbers"][tile["nearby_bombs"] - 1])

        if tile["status"] != STATUS_REVEALED:
            tile["status"] = STATUS_REVEALED
            self.revealed_tiles += 1
        if self.revealed_tiles == (BOARD_WIDTH * BOARD_HEIGHT) - self.total_bombs:
            self.end_game(True)

    def process_right_click(self, tile):
        if self.start_time is None:
            self.start_time = datetime.now()

        if tile["status"] == STATUS_HIDDEN:
            tile["button"].config(image=self.image_assets["mark"])
            tile["status"] = STATUS_MARKED
            tile["button"].unbind(LEFT_CLICK_EVENT)
            if tile["has_bomb"]:
                self.correct_marks += 1
            self.marked_tiles += 1
            self.update_status_labels()
        elif tile["status"] == STATUS_MARKED:
            tile["button"].config(image=self.image_assets["default"])
            tile["status"] = STATUS_HIDDEN
            tile["button"].bind(LEFT_CLICK_EVENT, self.handle_left_click(tile["position"]["x"], tile["position"]["y"]))
            if tile["has_bomb"]:
                self.correct_marks -= 1
            self.marked_tiles -= 1
            self.update_status_labels()

    def clear_adjacent_tiles(self, tile_id):
        queue = deque([tile_id])

        while queue:
            current_id = queue.popleft()
            x, y = map(int, current_id.split("_"))

            for neighbor in self.find_neighbors(x, y):
                self.reveal_tile(neighbor, queue)

    def reveal_tile(self, tile, queue):
        if tile["status"] != STATUS_HIDDEN:
            return

        if tile["nearby_bombs"] == 0:
            tile["button"].config(image=self.image_assets["revealed"])
            queue.append(tile["id"])
        else:
            tile["button"].config(image=self.image_assets["numbers"][tile["nearby_bombs"] - 1])

        tile["status"] = STATUS_REVEALED
        self.revealed_tiles += 1

def main():
    app_window = Tk()
    app_window.title("Minesweeper")
    game_instance = MinesweeperApp(app_window)
    app_window.mainloop()

if __name__ == "__main__":
    main()
