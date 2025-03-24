import colorama
from colorama import Fore, Style
import random
from enum import Enum
import argparse
import time

colorama.init()

# TODO: check perfs improvements, current = 4K/Sec


class GameMode(Enum):
    PvP = 1
    PvE = 2


class Env:
    def __init__(self):
        self.reset_game()

    def reset_game(self):
        self.board = [
            [
                "P1"
                if (i == 0)
                else "P2"
                if (i == 4)
                else "R"
                if (i == 2 and j == 2)
                else " "
                for j in range(5)
            ]
            for i in range(5)
        ]

        self.current_player = 1
        self.move_phase = "bobail"
        self.first_turn = True
        self.bobail_pos = (2, 2)
        self.player_start = {
            1: [(0, j) for j in range(5)],
            2: [(4, j) for j in range(5)],
        }
        self.colors = {
            "P1": Fore.GREEN,
            "P2": Fore.RED,
            "R": Fore.YELLOW,
            "reset": Style.RESET_ALL,
        }

    def print_board(self):
        horizontal = "+---" * 5 + "+"
        print(horizontal)
        for i, row in enumerate(self.board):
            cells = []
            for j, cell in enumerate(row):
                color = self.colors.get(cell, "")
                display = f"{color}{cell:3}{Style.RESET_ALL}" if cell != " " else "   "
                cells.append(display)
            print("|" + "|".join(cells) + "|")
            print(horizontal)

    def get_possible_moves(self, phase):
        """
        takes a phase as param. a phase (move phase) is either a pawn or BOBAIL
        returns a list with 2 tuples (start_row, start_col) and (end_row, end_col)
        which helps track the furthest pos to get to the correct destination.

        Notation:
            d(n) =  direction vector of n
            n(n) = the resulting new vector, calculated with the direciton vect

        """
        moves = []
        for i in range(5):
            for j in range(5):
                piece = self.board[i][j]
                if phase == "bobail" and piece == "R":
                    # we start by checking for the bobail and its surrounding 8 blocks/cells.
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            # these fors create all possible combinations of the 9 blocks ie:
                            # (-1,-1), (-1, 0), (-1, 1) ...
                            if dx == 0 and dy == 0:
                                # we skip if we are in the center -> stay in place because a valid
                                # move has to have direction
                                continue
                            # we calculate the new row/cols indexes by adding the offset
                            ni, nj = i + dx, j + dy
                            if (
                                0 <= ni < 5
                                and 0 <= nj < 5
                                and self.board[ni][nj] == " "
                            ):  # checks if move is withing  bounds and the target cell is empty " "
                                moves.append(((i, j), (ni, nj)))

                    # check for pawn phase and the correct current player
                elif phase == "pawn" and piece == f"P{self.current_player}":
                    # define all possible directions for the pawn, right down up left, diag up left etc..
                    for direction in [
                        (0, 1),
                        (1, 0),
                        (-1, 0),
                        (0, -1),
                        (1, 1),
                        (-1, -1),
                        (1, -1),
                        (-1, 1),
                    ]:
                        step = 1  # distance counter
                        furthest_pos = None  # i,j of furthest empty cell
                        while True:
                            # here step = 1, first iteration
                            # lets say for direction (0, 1), and postion (1, 1)
                            # ni (new i) = 1 + (0 * 1)
                            # nj = 1 + (1 * 1)
                            # which means new position will be (1, 2) and thus furthest_pos = 1,2
                            ni = i + direction[0] * step
                            nj = j + direction[1] * step
                            if not (0 <= ni < 5 and 0 <= nj < 5):
                                break
                            if self.board[ni][nj] != " ":
                                break
                            furthest_pos = (ni, nj)
                            step += 1  # if we dont hit a wall/ illegal move, we increment the step.

                        if furthest_pos:
                            moves.append(((i, j), furthest_pos))
        return moves

    def make_random_move(self):
        if not self.first_turn and self.move_phase == "bobail":
            moves = self.get_possible_moves("bobail")
            if moves:
                move = random.choice(moves)
                return self.move_piece(move[0], move[1])

        moves = self.get_possible_moves("pawn")
        if moves:
            move = random.choice(moves)
            return self.move_piece(move[0], move[1])
        return False, "No valid moves"

    def move_piece(self, start, end):
        valid, message = self.validate_move(start, end)
        if not valid:
            return False, message

        sx, sy = start
        ex, ey = end
        piece = self.board[sx][sy]

        self.board[sx][sy] = " "
        self.board[ex][ey] = piece

        if piece == "R":
            self.bobail_pos = (ex, ey)

        winner = self.check_winner()
        if winner:
            return True, f"Player {winner} wins!"

        if self.first_turn:
            self.first_turn = False
            self.current_player = 3 - self.current_player
            self.move_phase = "bobail"
        else:
            if self.move_phase == "bobail":
                self.move_phase = "pawn"
            else:
                self.current_player = 3 - self.current_player
                self.move_phase = "bobail"

        return True, "Move successful"

    def validate_move(self, start, end):
        """returns is move is valid + empty str
        or error msg
        """
        sx, sy = start
        ex, ey = end

        if not (0 <= sx < 5 and 0 <= sy < 5 and 0 <= ex < 5 and 0 <= ey < 5):
            return False, "Coordinates out of bounds"

        piece = self.board[sx][sy]
        target = self.board[ex][ey]

        if self.move_phase == "bobail" and not self.first_turn:
            if piece != "R":
                return False, "must move BOBAIL first"
            if target != " ":
                return False, "cell already has a pawn!"
            if abs(sx - ex) > 1 or abs(sy - ey) > 1:
                return False, "BOBAIL can only move 1 square"
            return True, ""

        if self.current_player == 1 and piece != "P1":
            return False, "not your pawn"
        if self.current_player == 2 and piece != "P2":
            return False, "not your pawn"
        if target != " ":
            return False, "cell already has a pawn!"

        dx = ex - sx
        dy = ey - sy
        if dx == 0 and dy == 0:
            return False, "no movement"
        if not ((dx == 0 or dy == 0) or (abs(dx) == abs(dy))):
            return False, "invalid direction"

        step_x = dx // abs(dx) if dx != 0 else 0
        step_y = dy // abs(dy) if dy != 0 else 0
        x, y = sx, sy

        while (x, y) != (ex, ey):
            x += step_x
            y += step_y
            if (x, y) == (ex, ey):
                break
            if self.board[x][y] != " ":
                return False, "path blocked"

        if self.first_turn and self.current_player == 1:
            pass

        return True, ""

    def check_winner(self):
        """checks win conditions : smothered bobail, or bobail in starting rows of p1, p2"""
        if self.bobail_pos in self.player_start[1]:
            return 1
        if self.bobail_pos in self.player_start[2]:
            return 2

        bx, by = self.bobail_pos
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = bx + dx, by + dy
                if 0 <= nx < 5 and 0 <= ny < 5:
                    if self.board[nx][ny] == " ":
                        return None
        return self.current_player

    def get_state(self):
        """
        returns the state repr of the game.
        returd a flat list of `79 values` for different modes.
        BOBAIL: 25
        P1 and P2 : 25, 25.
        3 values for state specific attributes.
        ie:
            - 1 value for `current player move`
            - 1 value for `move phase (pawn or bobail)`
            - 1 value for `first move`.
            - 1 value for if game is over
        """
        state = []
        # 75 values encoding, as mentionned above
        for i in range(5):
            for j in range(5):
                state.append(1 if self.board[i][j] == "P1" else 0)

        for i in range(5):
            for j in range(5):
                state.append(1 if self.board[i][j] == "P2" else 0)

        for i in range(5):
            for j in range(5):
                state.append(1 if self.board[i][j] == "R" else 0)

        # remaining 3
        state.append(1 if self.current_player == 1 else 0)  # current plauer

        if self.first_turn and self.current_player == 1:
            state.append(0)
        else:
            state.append(1 if self.move_phase == "bobail" else 0)  # bobail

        state.append(1 if self.first_turn else 0)  # first_turn

        winner = self.check_winner()
        state.append(1 if winner is not None else 0)  # game_over

        return state

    def get_action_mask(self):
        """
        return the action mask of a given move
        we make a lookup-set and
        each action is represented as a tuple (start_row, start_col, end_row, end_col)
        return if the action is valid based on `get_possible_moves` fn
        Issue: very large tuple of 625 elems
        """
        # TODO: find better encoding efficiency.

        if not self.first_turn and self.move_phase == "bobail":
            valid_moves = self.get_possible_moves("bobail")
        else:
            valid_moves = self.get_possible_moves("pawn")

        valid_moves_set = set([(start, end) for start, end in valid_moves])
        mask = []
        for start_row in range(5):
            for start_col in range(5):
                for end_row in range(5):
                    for end_col in range(5):
                        start = (start_row, start_col)
                        end = (end_row, end_col)
                        # 1 if move is valid, 0 if not
                        mask.append(1 if (start, end) in valid_moves_set else 0)
        return mask


def get_coord_input(prompt):
    while True:
        try:
            coord = input(prompt).strip().split()
            if len(coord) != 2:
                raise ValueError
            x, y = map(int, coord)
            if 0 <= x <= 4 and 0 <= y <= 4:
                return (x, y)
            raise ValueError
        except ValueError:
            print(
                "Invalid input! Use format: x y (0-4). PS: matrix format not cartesian plane"
            )


def run_single_game():
    """run a single game with random moves to completion and return the winner and move count"""
    game = Env()
    n_moves = 0

    while True:
        n_moves += 1
        success, message = game.make_random_move()
        if not success:
            # no valid moves, current player loses
            # returns 3 - player num
            # ie : if player 1 loses (current player), we dont return player 1
            # we instead return 3 - 1 = 2 ; player 2
            return 3 - game.current_player, n_moves

        if "wins" in message:
            return game.check_winner(), n_moves


def main():
    parser = argparse.ArgumentParser(description="Play")
    parser.add_argument("--count", action="store_true", help="Count games per sec")
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration in seconds to run the count benchmark",
    )
    args = parser.parse_args()

    if args.count:
        # games/sec
        num_games = 0
        p1_wins = 0
        p2_wins = 0
        total_moves = 0
        start_time = time.time()
        duration = args.duration

        print(f"Running games for {duration} seconds...")

        while time.time() - start_time < duration:
            winner, n_moves = run_single_game()
            num_games += 1
            total_moves += n_moves
            if winner == 1:
                p1_wins += 1
            else:
                p2_wins += 1

            if num_games % 1000 == 0:
                elapsed = time.time() - start_time
                print(
                    f"Games played: {num_games}, Freq: {num_games/elapsed:.2f} games/sec"
                )

        elapsed_time = time.time() - start_time
        games_per_second = num_games / elapsed_time
        avg_moves = total_moves / num_games if num_games > 0 else 0

        print("\n--- Metrics ---")
        print(f"Num games: {num_games}")
        print(f"Time elapsed: {elapsed_time:.2f} seconds")
        print(f"Games/second: {games_per_second:.2f}")
        print(f"N player 1 wins: {p1_wins} ({p1_wins/num_games*100:.1f}%)")
        print(f"N player 2 wins: {p2_wins} ({p2_wins/num_games*100:.1f}%)")
        print(f"Total moves: {total_moves}")
        print(f"Avg moves/game: {avg_moves:.1f}")
        return

    print(f"{Fore.CYAN}=== BOBAIL ==={Style.RESET_ALL}")
    print("1. PvP")
    print("2. PvE")
    choice = input("Select game mode (1-2): ").strip()

    game = Env()
    mode = GameMode.PvP if choice == "1" else GameMode.PvE

    while True:
        game.print_board()
        # show game state
        state = game.get_state()
        print(state)
        print("Mask:", game.get_action_mask())
        print(f"{Fore.BLUE}Player {game.current_player}'s turn{Style.RESET_ALL}")

        if mode == GameMode.PvE and game.current_player == 2:
            bobail_message = ""
            # if not the first turn, bot needs to move BOBAIL first
            if not game.first_turn:
                bobail_success, bobail_message = game.make_random_move()
                # check if bobail is in end state
                if "wins" in bobail_message:
                    print(f"bot moved: {bobail_message}")
                    game.print_board()
                    print(game.get_state())
                    break

            # then move pawn
            pawn_success, pawn_message = game.make_random_move()
            if bobail_message:
                print(f"bot moved: BOBAIL then pawn - {pawn_message}")
            else:
                print(f"bot moved: {pawn_message}")

            if "wins" in pawn_message:
                game.print_board()
                print(game.get_state())
                break
        else:
            if game.move_phase == "bobail" and not game.first_turn:
                print("Move BOBAIL (R)")
                start = get_coord_input(
                    "Enter start position (x y) : matrix format not cartesian plane "
                )
                end = get_coord_input(
                    "Enter end position (x y): matrix format not cartesian plane"
                )
            else:
                print("Move your pawn")
                start = get_coord_input("Enter start position (x y): ")
                end = get_coord_input("Enter end position (x y): ")

            success, message = game.move_piece(start, end)
            print(message)
            if "wins" in message:
                game.print_board()
                print(game.get_state())
                break

        winner = game.check_winner()
        if winner:
            print(f"{Fore.MAGENTA}player {winner} wins!{Style.RESET_ALL}")
            print(game.get_state())
            break


if __name__ == "__main__":
    main()
