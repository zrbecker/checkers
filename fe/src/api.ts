import axios from "axios";
import type { GameState, Move } from "./types";

const API_URL = import.meta.env.PROD ? "" : "http://localhost:8000";

export const createGame = async (playerId: string, playerName: string, mode: string = "online", player2Name?: string): Promise<GameState> => {
  const response = await axios.post(`${API_URL}/games`, { player_id: playerId, player_name: playerName, mode, player2_name: player2Name });
  return response.data;
};

export const joinGame = async (gameId: string, playerId: string, playerName: string): Promise<GameState> => {
  const response = await axios.post(`${API_URL}/games/${gameId}/join`, { player_id: playerId, player_name: playerName });
  return response.data;
};

export const getGame = async (gameId: string): Promise<GameState> => {
  const response = await axios.get(`${API_URL}/games/${gameId}`);
  return response.data;
};

export const makeMove = async (gameId: string, move: Move & { player_id: string }): Promise<GameState> => {
  const response = await axios.post(`${API_URL}/games/${gameId}/move`, move);
  return response.data;
};

export const makeAiMove = async (gameId: string): Promise<GameState> => {
  const response = await axios.post(`${API_URL}/games/${gameId}/ai-move`);
  return response.data;
};
