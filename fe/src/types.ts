export interface GameState {
  id: string;
  board: (string | null)[][];
  current_turn: "red" | "black";
  status: "active" | "finished";
  winner: "red" | "black" | "draw" | null;
  red_player_id?: string;
  black_player_id?: string;
  red_player_name?: string;
  black_player_name?: string;
  last_move?: {
    start_row: number;
    start_col: number;
    end_row: number;
    end_col: number;
  };
  active_piece?: {
    row: number;
    col: number;
  };
  mode?: "online" | "cpu" | "local";
  draw_offer?: "red" | "black" | null;
}

export interface Move {
  start_row: number;
  start_col: number;
  end_row: number;
  end_col: number;
}
