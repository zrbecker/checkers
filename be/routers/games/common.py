from models import Game
from schemas import GameState

def to_game_state(game: Game) -> GameState:
    return GameState(
        id=str(game.id),
        board=game.board_state,
        current_turn=game.current_turn,
        status=game.status,
        winner=game.winner,
        red_player_id=game.red_player_id,
        black_player_id=game.black_player_id,
        red_player_name=game.red_player_name,
        black_player_name=game.black_player_name,
        last_move=game.last_move,
        active_piece=game.active_piece,
        mode=game.mode,
        draw_offer=game.draw_offer,
        draw_timer=game.draw_timer
    )
