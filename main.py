# Change this if you want to connect with another computer :)
# If hosting, this will be the ip and port you use.
# If connecting, this will be the ip and port you connect to.
host_ip = "localhost"
host_port = 12345

import tkinter as tk
from typing import List
from typing import Tuple

import socket
import select
import copy

root = tk.Tk()
root.title("Multiplayer Chess")
root.resizable(False, False)


board_size = 8
cell_size = 60

clicked_row, clicked_col = None, None

my_color = "white"
my_turn = True
my_king_pos = (7, 4) # for quick retrieval later
on_title_screen = True

canvas = None

my_socket = None

class Piece:
    def __init__(self, name: str, piece_type: str, color: str, row: int, col: int):
        self.name = name
        self.piece_type = piece_type
        self.color = color
        self.row = row
        self.col = col
        self.first_move = True
        self.en_passant = False
        assert(color == "black" or color == "white")
    
    # return all valid moves for this piece
    def valid_moves(self, piece_positions) -> List[Tuple[int, int]]:
        moves = []
        if self.piece_type == "rook":
            moves = self.rook_moves(piece_positions)
        elif self.piece_type == "knight":
            moves = self.knight_moves(piece_positions)
        elif self.piece_type == "queen":
            moves = self.rook_moves(piece_positions) + self.bishop_moves(piece_positions)
        elif self.piece_type == "king":
            moves = self.king_moves(piece_positions)
        elif self.piece_type == "bishop":
            moves = self.bishop_moves(piece_positions)
        else:
            moves = self.pawn_moves(piece_positions)

        moves = self.prune_check_moves(moves, piece_positions)
        return moves

    # prune any moves that would result in a check so that we don't display them when trying
    # to make a move.
    # 
    # unfortunately, there's no better way to do this than brute forcing all next positions and
    # seeing if they would result in a check. but since the upper bound of moves is low, this 
    # isn't a huge deal.
    def prune_check_moves(self, moves: List[Tuple[int, int]], piece_positions) -> List[Tuple[int, int]]:
        global my_king_pos

        final_moves = copy.deepcopy(moves)

        king_row, king_col = my_king_pos

        old_row, old_col = self.row, self.col

        is_king = self.piece_type == "king"

        scratch = copy.deepcopy(piece_positions)
        scratch.pop((self.row, self.col))

        for (row, col) in moves:
            piece = scratch.get((row, col))
            if piece:
                scratch.pop((row, col))

            self.row, self.col = row, col
            scratch[(row, col)] = self

            if is_king:
                king_row, king_col = row, col

            if is_in_mate(king_row, king_col, scratch):
                final_moves.remove((row, col))

            scratch.pop((row, col))
            if piece:
                scratch[(row, col)] = piece

        self.row, self.col = old_row, old_col
        return final_moves
    
    # all the proceeding code "X"_moves is just for getting the valid moves of the 
    # given piece type "X"
    def rook_moves(self, piece_positions) -> List[Tuple[int, int]]:
        moves = []
        dxs_dys = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for (dx, dy) in dxs_dys:
            row, col = self.row, self.col
            while row + dx >= 0 and row + dx <= board_size and col + dy >= 0 and col + dy <= board_size:
                row += dx
                col += dy
                piece = piece_positions.get((row, col))
                if piece:
                    if piece.color != self.color:
                        moves.append((row, col))
                    break
                moves.append((row, col))

        return moves

    def knight_moves(self, piece_positions) -> List[Tuple[int, int]]:
        moves = []

        offsets = [
            (-2, -1), (-1, -2), (1, -2), (2, -1),
            (2, 1), (1, 2), (-1, 2), (-2, 1)
        ]

        for (dx, dy) in offsets:
            new_row, new_col = self.row + dx, self.col + dy

            if 0 <= new_row < board_size and 0 <= new_col < board_size:
                piece = piece_positions.get((new_row, new_col))
                if not piece or piece.color != self.color:
                    moves.append((new_row, new_col))

        return moves

    def bishop_moves(self, piece_positions) -> List[Tuple[int, int]]:
        moves = []

        dxs_dys = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

        for (dx, dy) in dxs_dys:
            row, col = self.row, self.col
            while row + dx >= 0 and row + dx <= board_size and col + dy >= 0 and col + dy <= board_size:
                row += dx
                col += dy
                piece = piece_positions.get((row, col))
                if piece:
                    if piece.color != self.color:
                        moves.append((row, col))
                    break
                moves.append((row, col))

        return moves

    def king_moves(self, piece_positions) -> List[Tuple[int, int]]:
        moves = []

        offsets = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, 1), (0, -1),
            (1, -1), (1, 0), (1, 1),
        ]

        for (dx, dy) in offsets:
            new_row, new_col = self.row + dx, self.col + dy

            if 0 <= new_row < board_size and 0 <= new_col < board_size:
                piece = piece_positions.get((new_row, new_col))
                if not piece or piece.color != self.color:
                    moves.append((new_row, new_col))

        return moves

    def pawn_moves(self, piece_positions) -> List[Tuple[int, int]]:
        moves = []
        if (self.row - 1, self.col) not in piece_positions:
            moves.append((self.row - 1, self.col))
            if self.first_move and (self.row - 2, self.col) not in piece_positions:
                moves.append((self.row - 2, self.col))

        piece_diag_left = piece_positions.get((self.row - 1, self.col - 1))
        piece_diag_right = piece_positions.get((self.row - 1, self.col + 1))

        piece_check = [piece_diag_left, piece_diag_right]

        for piece in piece_check:
            if piece and piece.color != self.color:
                moves.append((self.row - 1, piece.col))

        # Check for en passant
        piece_left = piece_positions.get((self.row, self.col - 1))
        piece_right = piece_positions.get((self.row, self.col + 1))
        piece_check = [piece_left, piece_right]

        for piece in piece_check:
            if piece and piece.en_passant and piece.color != self.color:
                moves.append((self.row - 1, piece.col))
            
        return moves
    
    def is_valid_move(self, row: int, col: int, piece_positions) -> bool:
        return (row, col) in self.valid_moves(piece_positions)

piece_positions = {
    (0, 0): Piece("rook_black", "rook", "black", 0, 0),
    (0, 1): Piece("knight_black", "knight", "black", 0, 1),
    (0, 2): Piece("bishop_black", "bishop", "black", 0, 2),
    (0, 3): Piece("queen_black", "queen", "black", 0, 3),
    (0, 4): Piece("king_black", "king", "black", 0, 4),
    (0, 5): Piece("bishop_black", "bishop", "black", 0, 5),
    (0, 6): Piece("knight_black", "knight", "black", 0, 6),
    (0, 7): Piece("rook_black", "rook", "black", 0, 7),
    (1, 0): Piece("pawn_black", "pawn", "black", 1, 0),
    (1, 1): Piece("pawn_black", "pawn", "black", 1, 1),
    (1, 2): Piece("pawn_black", "pawn", "black", 1, 2),
    (1, 3): Piece("pawn_black", "pawn", "black", 1, 3),
    (1, 4): Piece("pawn_black", "pawn", "black", 1, 4),
    (1, 5): Piece("pawn_black", "pawn", "black", 1, 5),
    (1, 6): Piece("pawn_black", "pawn", "black", 1, 6),
    (1, 7): Piece("pawn_black", "pawn", "black", 1, 7),
    (7, 0): Piece("rook_white", "rook", "white", 7, 0),
    (7, 1): Piece("knight_white", "knight", "white", 7, 1),
    (7, 2): Piece("bishop_white", "bishop", "white", 7, 2),
    (7, 3): Piece("queen_white", "queen", "white", 7, 3),
    (7, 4): Piece("king_white", "king", "white", 7, 4),
    (7, 5): Piece("bishop_white", "bishop", "white", 7, 5),
    (7, 6): Piece("knight_white", "knight", "white", 7, 6),
    (7, 7): Piece("rook_white", "rook", "white", 7, 7),
    (6, 0): Piece("pawn_white", "pawn", "white", 6, 0),
    (6, 1): Piece("pawn_white", "pawn", "white", 6, 1),
    (6, 2): Piece("pawn_white", "pawn", "white", 6, 2),
    (6, 3): Piece("pawn_white", "pawn", "white", 6, 3),
    (6, 4): Piece("pawn_white", "pawn", "white", 6, 4),
    (6, 5): Piece("pawn_white", "pawn", "white", 6, 5),
    (6, 6): Piece("pawn_white", "pawn", "white", 6, 6),
    (6, 7): Piece("pawn_white", "pawn", "white", 6, 7),
}

piece_images = {}
piece_images["king_white"] = tk.PhotoImage(file="assets/king_white.png").subsample(32)
piece_images["queen_white"] = tk.PhotoImage(file="assets/queen_white.png").subsample(32)
piece_images["rook_white"] = tk.PhotoImage(file="assets/rook_white.png").subsample(32)
piece_images["bishop_white"] = tk.PhotoImage(file="assets/bishop_white.png").subsample(32)
piece_images["knight_white"] = tk.PhotoImage(file="assets/knight_white.png").subsample(32)
piece_images["pawn_white"] = tk.PhotoImage(file="assets/pawn_white.png").subsample(32)
piece_images["king_black"] = tk.PhotoImage(file="assets/king_black.png").subsample(32)
piece_images["queen_black"] = tk.PhotoImage(file="assets/queen_black.png").subsample(32)
piece_images["rook_black"] = tk.PhotoImage(file="assets/rook_black.png").subsample(32)
piece_images["bishop_black"] = tk.PhotoImage(file="assets/bishop_black.png").subsample(32)
piece_images["knight_black"] = tk.PhotoImage(file="assets/knight_black.png").subsample(32)
piece_images["pawn_black"] = tk.PhotoImage(file="assets/pawn_black.png").subsample(32)

def handle_click(event):
    global clicked_col  
    global clicked_row
    global piece_positions
    global my_socket
    global my_turn
    global my_king_pos

    assert(my_socket)

    highlight_list = []
    
    if clicked_row is None:
        # Player hasn't selected anything yet. Highlight any clicked piece.
        clicked_col = event.x // cell_size
        clicked_row = event.y // cell_size
        piece = piece_positions.get((clicked_row, clicked_col))
        if not piece or piece.color != my_color or not my_turn:
            clicked_row, clicked_col = None, None
        else:
            highlight_list = piece.valid_moves(piece_positions)
    else:
        # Player wants to move a piece or unselect the piece.
        assert(clicked_col is not None)
        move_col = event.x // cell_size
        move_row = event.y // cell_size
        piece = piece_positions.get((clicked_row, clicked_col))
        # If it's a valid move, then make the move & send. Extra check for removing an 
        # en passant piece, since it kills a target on a square other than the square moved to.
        if piece and piece.is_valid_move(move_row, move_col, piece_positions):
            msg = str(piece.row) + str(piece.col) + str(move_row) + str(move_col)

            if piece.piece_type == "pawn" and move_col != piece.col:
                en_passant_piece = piece_positions.get((piece.row, move_col))
                if en_passant_piece:
                    piece_positions.pop((piece.row, move_col))

                    
            piece.row = move_row
            piece.col = move_col

            piece.first_move = False
            piece_positions.pop((clicked_row, clicked_col))
            piece_positions[(move_row, move_col)] = piece

            for (_, piece) in piece_positions.items():
                piece.en_passant = False

            if piece.piece_type == "king":
                my_king_pos = (piece.row, piece.col)

            my_socket.sendall(msg.encode())
            my_turn = False


        clicked_row, clicked_col = None, None

    draw_board(None, highlight_list)

def decode_message(msg: str):
    global piece_positions
    # Message format is just the rows and columns of the move
    # e.g. 1234 moves (1,2) to (3,4)
    row_1, col_1 = 7 - int(msg[0]), int(msg[1])
    row_2, col_2 = 7 - int(msg[2]), int(msg[3])

    piece = piece_positions.get((row_1, col_1))
    assert(piece)

    piece_positions.pop((row_1, col_1))

    if piece_positions.get((row_2, col_2)):
        piece_positions.pop((row_2, col_2))

    piece.en_passant = piece.first_move and \
                       piece.piece_type == "pawn" and \
                       row_2 == piece.row + 2

    # special case for en passant, since captured piece is diff
    if piece.piece_type == "pawn" and col_2 != piece.col:
        en_passant_piece = piece_positions.get((piece.row, col_2))
        if en_passant_piece:
            piece_positions.pop((piece.row, col_2))

    piece.first_move = False
    piece.row = row_2
    piece.col = col_2
    piece_positions[(row_2, col_2)] = piece

def listen_and_decode():
    global my_turn
    global my_socket

    assert(my_socket)

    if not my_turn:
        readable, _, _ = select.select([my_socket], [], [], 0.01)
        if readable:
            # Read data from the client
            data = my_socket.recv(4)
            if data:
                decode_message(data.decode())
                my_turn = True
                draw_board()
            else:
                # Client disconnected, game can't continue
                return
        else:
            root.after(100, listen_and_decode)

def is_in_mate(king_row, king_col, piece_positions) -> bool:
    global my_color
    king = piece_positions.get((king_row, king_col))
    assert(king and king.piece_type == "king" and king.color == my_color)

    # Check for pawns first in the unlikely case that happens.
    dxs_dys = [(-1, -1), (-1, 1)]
    for (dx, dy) in dxs_dys:
        pawn = piece_positions.get((king_row + dx, king_col + dy))
        if pawn and pawn.color != my_color and pawn.piece_type == "pawn":
            return True

    # We can actually reuse the rook/bishop/knight move functions for the rest.
    for (row, col) in king.rook_moves(piece_positions):
        piece = piece_positions.get((row, col))
        if piece and piece.color != my_color and (piece.piece_type == "rook" or piece.piece_type == "queen"):
            return True

    for (row, col) in king.bishop_moves(piece_positions):
        piece = piece_positions.get((row, col))
        if piece and piece.color != my_color and (piece.piece_type == "bishop" or piece.piece_type == "queen"):
            return True

    for (row, col) in king.knight_moves(piece_positions):
        piece = piece_positions.get((row, col))
        if piece and piece.color != my_color and piece.piece_type == "knight":
            return True

    for (row, col) in king.king_moves(piece_positions):
        piece = piece_positions.get((row, col))
        if piece and piece.color != my_color and piece.piece_type == "king":
            return True

    # Can't be captured if we get here
    return False

def is_in_checkmate(piece_positions) -> bool:
    for (_, piece) in piece_positions.items():
        if piece.color != my_color:
            continue
        moves = piece.valid_moves(piece_positions)
        if len(moves) > 0:
            return False
    return True

def draw_board(_=None, highlight_list=[]):
    global clicked_col
    global clicked_row
    global piece_positions
    global my_king_pos
    global canvas
    global on_title_screen
    global my_socket
    global my_turn

    if on_title_screen:
        draw_title_screen()
        return

    if not canvas:
       canvas = tk.Canvas(root, width=board_size * cell_size, height=board_size * cell_size)
       canvas.bind("<Button-1>", handle_click)

    canvas.delete("all")

    canvas.pack(fill=tk.BOTH, expand=True)

    canvas_width = canvas.winfo_width()
    canvas_height = canvas.winfo_height()

    new_board_size = min(canvas_width, canvas_height)
    new_cell_size = new_board_size // board_size

    # Draw chessboard
    for row in range(board_size):
        for col in range(board_size):
            x1 = col * new_cell_size
            y1 = row * new_cell_size
            x2 = x1 + new_cell_size
            y2 = y1 + new_cell_size

            # Draw the chess pieces
            piece = piece_positions.get((row, col))

            if (row + col) % 2 == 0:
                color = "white"
            else:
                color = "gray"


            if (row, col) in highlight_list:
                color = "blue"

            king_row, king_col = my_king_pos

            if piece and piece.piece_type == "king" and piece.color == my_color and \
               is_in_mate(king_row, king_col, piece_positions):
                if is_in_checkmate(piece_positions):
                    print("Checkmate! You lose.")
                color = "pink"

            if (row == clicked_row and col == clicked_col):
                color = "red"

            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")

            if piece:
                image = piece_images[piece.name]
                x = x1 + new_cell_size // 2
                y = y1 + new_cell_size // 2
                canvas.create_image(x, y, image=image)

    if not my_turn:
        listen_and_decode()

def reverse_piece_map():
    # reverse the pieces for the "client" side, so that pieces
    # show on the other side of the board
    global piece_positions
    global my_king_pos

    new_map = {}
    for (row, col), piece in piece_positions.items():
        row = piece.row = 7 - row
        new_map[(row, col)] = piece
    
    piece_positions = new_map

def connect():
    global on_title_screen
    global my_socket
    global my_color
    global my_turn
    
    # If we are connecting, we will be the black color
    my_color = "black"
    reverse_piece_map()
    on_title_screen = False
    my_turn = False

    for widget in root.winfo_children():
        widget.destroy()

    container_frame = tk.Frame(root)
    container_frame.pack(padx=80, pady=80, fill=tk.BOTH)
    title_label = tk.Label(container_frame, 
                           text="Trying to connect...", 
                           font=("Arial", 24, "bold"))
    title_label.pack(pady=20)
    root.update()
    root.update_idletasks()

    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setblocking(False)
    try:
        my_socket.connect(('localhost', host_port))
    except BlockingIOError:
        pass  # Connection is in progress, will be handled by select

    while True:
        _, writable, _ = select.select([], [my_socket], [], 0.1)

        if my_socket in writable:
            print("Connected to server")
            break

        root.update()
        root.update_idletasks()
        
    for widget in root.winfo_children():
        widget.destroy()

    draw_board()
    root.bind('<Configure>', draw_board)

def host():
    global on_title_screen
    global my_socket
    on_title_screen = False
    for widget in root.winfo_children():
        widget.destroy()
    container_frame = tk.Frame(root)
    container_frame.pack(padx=80, pady=80, fill=tk.BOTH)
    title_label = tk.Label(container_frame, 
                           text="Waiting for connection...", 
                           font=("Arial", 24, "bold"))
    title_label.pack(pady=20)
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_sock.setblocking(False)

    server_sock.bind(('localhost', host_port))

    server_sock.listen()

    while True:
        readable, _, _ = select.select([server_sock], [], [], 0.1)
        if server_sock in readable:
            my_socket, address = server_sock.accept()
            print(f"Accepted connection from ", address)
            break
        root.update()
        root.update_idletasks()

    for widget in root.winfo_children():
        widget.destroy()

    draw_board()
    root.bind('<Configure>', draw_board)

def draw_title_screen():
    container_frame = tk.Frame(root)
    container_frame.pack(padx=80, pady=80, fill=tk.BOTH)

    title_label = tk.Label(container_frame, text="Chess", font=("Arial", 24, "bold"))
    title_label.pack(pady=20)

    button_frame = tk.Frame(container_frame)
    button_frame.pack(pady=20)

    connect_button = tk.Button(button_frame, text="Connect", padx=20, pady=10, command=connect)
    connect_button.pack(side=tk.LEFT, padx=10)

    host_button = tk.Button(button_frame, text="Host", padx=20, pady=10, command=host)
    host_button.pack(side=tk.LEFT, padx=10)

if __name__ == '__main__':
    draw_board()
    root.mainloop()

