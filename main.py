import tkinter as tk
from typing import List
from typing import Tuple

root = tk.Tk()
root.title("Multiplayer Chess")

board_size = 8
cell_size = 60

clicked_row, clicked_col = None, None

canvas = tk.Canvas(root, width=board_size * cell_size, height=board_size * cell_size)
canvas.pack(fill=tk.BOTH, expand=True)

piece_images = {}
piece_images["king_white"] = tk.PhotoImage(file="king_white.png").subsample(32)
piece_images["queen_white"] = tk.PhotoImage(file="queen_white.png").subsample(32)
piece_images["rook_white"] = tk.PhotoImage(file="rook_white.png").subsample(32)
piece_images["bishop_white"] = tk.PhotoImage(file="bishop_white.png").subsample(32)
piece_images["knight_white"] = tk.PhotoImage(file="knight_white.png").subsample(32)
piece_images["pawn_white"] = tk.PhotoImage(file="pawn_white.png").subsample(32)
piece_images["king_black"] = tk.PhotoImage(file="king_black.png").subsample(32)
piece_images["queen_black"] = tk.PhotoImage(file="queen_black.png").subsample(32)
piece_images["rook_black"] = tk.PhotoImage(file="rook_black.png").subsample(32)
piece_images["bishop_black"] = tk.PhotoImage(file="bishop_black.png").subsample(32)
piece_images["knight_black"] = tk.PhotoImage(file="knight_black.png").subsample(32)
piece_images["pawn_black"] = tk.PhotoImage(file="pawn_black.png").subsample(32)


class Piece:
    def __init__(self, name: str, piece_type: str, color: str, row: int, col: int):
        self.name = name
        self.piece_type = piece_type
        self.color = color
        self.row = row
        self.col = col
        self.first_move = True
        assert(color == "black" or color == "white")

    def valid_moves(self, piece_positions) -> List[Tuple[int, int]]:
        if self.piece_type == "rook":
            return self.rook_moves(piece_positions)
        elif self.piece_type == "knight":
            return self.knight_moves(piece_positions)
        elif self.piece_type == "queen":
            return self.rook_moves(piece_positions) + self.bishop_moves(piece_positions)
        elif self.piece_type == "king":
            return self.king_moves(piece_positions)
        elif self.piece_type == "bishop":
            return self.bishop_moves(piece_positions)
        else:
            return self.pawn_moves(piece_positions)
    
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

        if piece_diag_left and piece_diag_left.color != self.color:
            moves.append((self.row - 1, self.col -1))

        if piece_diag_right and piece_diag_right.color != self.color:
            moves.append((self.row - 1, self.col + 1))
            
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

def handle_click(event):
    global clicked_col  
    global clicked_row
    global piece_positions

    highlight_list = []
    
    if clicked_row is None:
        clicked_col = event.x // cell_size
        clicked_row = event.y // cell_size
        piece = piece_positions.get((clicked_row, clicked_col))
        if not piece:
            clicked_row, clicked_col = None, None
        else:
            highlight_list = piece.valid_moves(piece_positions)
    else:
        assert(clicked_col is not None)
        move_col = event.x // cell_size
        move_row = event.y // cell_size
        piece = piece_positions.get((clicked_row, clicked_col))
        if piece and piece.is_valid_move(move_row, move_col, piece_positions):
            piece.row = move_row
            piece.col = move_col
            piece.first_move = False
            piece_positions.pop((clicked_row, clicked_col))
            piece_positions[(move_row, move_col)] = piece
            # print(f"Move to {move_row} {move_col} from {clicked_row} {clicked_col}")


        clicked_row, clicked_col = None, None

    draw_board(None, highlight_list)

def draw_board(_event=None, highlight_list=[]):
    global clicked_col
    global clicked_row
    global piece_positions
    canvas.delete("all")

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

            if (row == clicked_row and col == clicked_col):
                color = "red"

            if (row, col) in highlight_list:
                color = "blue"

            canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")

            if piece:
                image = piece_images[piece.name]
                x = x1 + new_cell_size // 2
                y = y1 + new_cell_size // 2
                canvas.create_image(x, y, image=image)


draw_board()

root.bind('<Configure>', draw_board)
canvas.bind("<Button-1>", handle_click)

root.mainloop()
