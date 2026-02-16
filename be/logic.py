from typing import List, Optional, Tuple, Dict, Any

# Board dimensions
ROWS = 8
COLS = 8

# Piece constants
RED = "r"
BLACK = "b"
RED_KING = "R"
BLACK_KING = "B"

def initialize_board() -> List[List[Optional[str]]]:
    # Explicitly type the inner lists to avoid inference as List[None]
    board: List[List[Optional[str]]] = [[None for _ in range(COLS)] for _ in range(ROWS)]
    for row in range(ROWS):
        for col in range(COLS):
            if (row + col) % 2 == 1:
                if row < 3:
                    board[row][col] = RED
                elif row > 4:
                    board[row][col] = BLACK
    return board

def get_valid_moves(board: List[List[Optional[str]]], player: str) -> List[Tuple[int, int, int, int]]:
    """
    Returns a list of all valid moves for the given player.
    Each move is a tuple: (start_row, start_col, end_row, end_col).
    """
    moves = []
    captures = []
    
    is_red = player == "red"
    
    # Iterate through all board positions
    for r in range(ROWS):
        for c in range(COLS):
            piece = board[r][c]
            if not piece:
                continue
            
            # Check ownership
            if is_red and piece.lower() != "r":
                continue
            if not is_red and piece.lower() != "b":
                continue
                
            is_king = piece.isupper()
            
            # Determine movement directions
            # Red moves "down" (increasing row index), Black moves "up" (decreasing row index)
            move_dirs = []
            if is_king:
                move_dirs = [-1, 1]
            elif is_red:
                move_dirs = [1]
            else:
                move_dirs = [-1]
                
            for dr in move_dirs:
                for dc in [-1, 1]:
                    # 1. Check for normal move (1 step)
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS:
                        if board[nr][nc] is None:
                            moves.append((r, c, nr, nc))
                        
                    # 2. Check for capture (2 steps)
                    nr2, nc2 = r + 2*dr, c + 2*dc
                    mid_r, mid_c = r + dr, c + dc
                    
                    if 0 <= nr2 < ROWS and 0 <= nc2 < COLS:
                        mid_piece = board[mid_r][mid_c]
                        # Check if landing spot is empty
                        if board[nr2][nc2] is None:
                             # Check if piece being jumped over exists and is opponent
                            if mid_piece:
                                if is_red and mid_piece.lower() == "b":
                                    captures.append((r, c, nr2, nc2))
                                elif not is_red and mid_piece.lower() == "r":
                                    captures.append((r, c, nr2, nc2))

    # Strict rule: if captures are available, you must capture.
    # For MVP, let's enforce this to keep it standard-ish.
    if captures:
        return captures
    return moves

def is_valid_move(board: List[List[Optional[str]]], move_data: Any, player: str) -> bool:
    # Handle move_data being a dict or object
    if isinstance(move_data, dict):
        sr, sc = move_data["start_row"], move_data["start_col"]
        er, ec = move_data["end_row"], move_data["end_col"]
    else:
        sr, sc = move_data.start_row, move_data.start_col
        er, ec = move_data.end_row, move_data.end_col
        
    valid_moves = get_valid_moves(board, player)
    return (sr, sc, er, ec) in valid_moves

def apply_move(board: List[List[Optional[str]]], move_data: Any) -> Tuple[List[List[Optional[str]]], bool]:
    if isinstance(move_data, dict):
        sr, sc = move_data["start_row"], move_data["start_col"]
        er, ec = move_data["end_row"], move_data["end_col"]
    else:
        sr, sc = move_data.start_row, move_data.start_col
        er, ec = move_data.end_row, move_data.end_col
    
    piece = board[sr][sc]
    # Move piece
    board[er][ec] = piece
    board[sr][sc] = None
    
    # Handle Capture (remove jumped piece)
    if abs(sr - er) == 2:
        mid_r = (sr + er) // 2
        mid_c = (sc + ec) // 2
        board[mid_r][mid_c] = None
        
    # King Promotion
    if piece == RED and er == ROWS - 1:
        board[er][ec] = RED_KING
    elif piece == BLACK and er == 0:
        board[er][ec] = BLACK_KING
        
    return board, True

def check_winner(board: List[List[Optional[str]]], current_turn: str) -> Optional[str]:
    red_count = 0
    black_count = 0
    for row in board:
        for cell in row:
            if cell:
                if cell.lower() == "r":
                    red_count += 1
                elif cell.lower() == "b":
                    black_count += 1
    
    if red_count == 0:
        return "black"
    if black_count == 0:
        return "red"
        
    # Check for stalemate (no valid moves for current player)
    # If it's current_turn's move and they have no moves, they lose.
    if not get_valid_moves(board, current_turn):
        return "black" if current_turn == "red" else "red"
        
    return None
