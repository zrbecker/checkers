export interface GameState {
  id: number;
  board: (string | null)[][];
  current_turn: "red" | "black";
  status: "active" | "finished";
  winner: "red" | "black" | null;
  red_player_id?: string;
  black_player_id?: string;
}

export interface Move {
  start_row: number;
  start_col: number;
  end_row: number;
  end_col: number;
}
