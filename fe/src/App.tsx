import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { createGame, getGame, makeMove, joinGame } from "./api";
import type { GameState } from "./types";
import { Square } from "./components/Square";
import clsx from "clsx";

const POLLING_INTERVAL = 2000;

function App() {
  const { gameId } = useParams();
  const navigate = useNavigate();

  const [game, setGame] = useState<GameState | null>(null);
  const [selectedSquare, setSelectedSquare] = useState<[number, number] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Lobby State
  const [joinInputId, setJoinInputId] = useState("");
  const [playerId, setPlayerId] = useState<string>("");

  // Sound Effect
  const playTurnSound = () => {
      try {
          const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
          const oscillator = audioCtx.createOscillator();
          const gainNode = audioCtx.createGain();
          
          oscillator.connect(gainNode);
          gainNode.connect(audioCtx.destination);
          
          oscillator.type = "sine";
          oscillator.frequency.setValueAtTime(440, audioCtx.currentTime); // A4
          oscillator.frequency.exponentialRampToValueAtTime(880, audioCtx.currentTime + 0.1); // Slide up to A5
          
          gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
          
          oscillator.start();
          oscillator.stop(audioCtx.currentTime + 0.3);
      } catch (e) {
          console.error("Audio play failed", e);
      }
  };

  // Initialize Player ID
  useEffect(() => {
    let storedId = localStorage.getItem("checkers_player_id");
    if (!storedId) {
        storedId = crypto.randomUUID();
        localStorage.setItem("checkers_player_id", storedId);
    }
    setPlayerId(storedId);
  }, []);

  // Handle Routing / Game Joining
  useEffect(() => {
      if (gameId && playerId) {
          // If URL has ID but we haven't loaded it yet (or loaded a different one)
          if (!game || game.id !== gameId) {
              const fetchGame = async () => {
                  setLoading(true);
                  try {
                      // Attempt to join/rejoin
                      const joinedGame = await joinGame(gameId, playerId);
                      setGame(joinedGame);
                      setError(null);
                  } catch (err: any) {
                      console.error(err);
                      setError(err.response?.data?.detail || "Failed to join game");
                      // Optionally navigate back to lobby if 404
                      if (err.response?.status === 404) {
                          navigate("/");
                      }
                  } finally {
                      setLoading(false);
                  }
              };
              fetchGame();
          }
      } else if (!gameId && game) {
          // URL is root but we have game state -> Clear it (user went back)
          setGame(null);
      }
  }, [gameId, playerId]); // Dependency on gameId handles URL changes

  // Polling for updates
  useEffect(() => {
    if (!game || game.status === "finished") return;

    const interval = setInterval(async () => {
      try {
        const updatedGame = await getGame(game.id);
        
        const stateChanged = JSON.stringify(updatedGame.board) !== JSON.stringify(game.board) || 
                             updatedGame.current_turn !== game.current_turn ||
                             updatedGame.black_player_id !== game.black_player_id;

        if (stateChanged) {
          // Check if turn changed to ME
          const myColor = updatedGame.red_player_id === playerId ? "red" : 
                          updatedGame.black_player_id === playerId ? "black" : null;
          
          if (myColor && updatedGame.current_turn === myColor && game.current_turn !== myColor) {
              playTurnSound();
          }

          setGame(updatedGame);
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, POLLING_INTERVAL);

    return () => clearInterval(interval);
  }, [game]);

  const handleCreateGame = async () => {
      setLoading(true);
      try {
          const newGame = await createGame(playerId);
          setGame(newGame);
          setError(null);
          navigate(`/game/${newGame.id}`);
      } catch (err) {
          console.error(err);
          setError("Failed to create game");
      } finally {
          setLoading(false);
      }
  };

  const handleManualJoin = () => {
      if (!joinInputId) return;
      navigate(`/game/${joinInputId}`);
  };

  const handleBackToLobby = () => {
      setGame(null);
      navigate("/");
  };

  const myColor = game ? (game.red_player_id === playerId ? "red" : 
                  game.black_player_id === playerId ? "black" : "spectator") : null;

  const handleSquareClick = async (visualRow: number, visualCol: number) => {
    if (!game || !myColor) return;

    // Transform Visual -> Logic
    // If I am Red, the board is flipped (7-row, 7-col)
    // If I am Black or Spectator, board is standard
    let row = visualRow;
    let col = visualCol;
    if (myColor === "red") {
        row = 7 - visualRow;
        col = 7 - visualCol;
    }

    // Enforce Turn
    if (game.current_turn !== myColor) {
        return;
    }

    const piece = game.board[row][col];
    
    // Logic for selection:
    const pieceIsRed = piece?.toLowerCase() === "r";
    const pieceIsBlack = piece?.toLowerCase() === "b";
    
    // Only allow selecting pieces that match my color
    if ((myColor === "red" && pieceIsRed) || (myColor === "black" && pieceIsBlack)) {
        if (selectedSquare && selectedSquare[0] === row && selectedSquare[1] === col) {
            setSelectedSquare(null); // Deselect if clicking same
        } else {
            setSelectedSquare([row, col]); // Select new
            setError(null);
        }
        return;
    }

    // 2. If we have a selection and click an empty square, try to move
    if (selectedSquare && !piece) {
      const [startRow, startCol] = selectedSquare;
      
      try {
        const updatedGame = await makeMove(game.id, {
          start_row: startRow,
          start_col: startCol,
          end_row: row,
          end_col: col,
          player_id: playerId
        });
        setGame(updatedGame);
        setSelectedSquare(null);
        setError(null);
      } catch (err: any) {
        console.error(err);
        setError(err.response?.data?.detail || "Invalid move");
      }
    }
  };

  if (loading) return <div className="flex justify-center items-center h-screen bg-stone-900 text-white">Loading...</div>;

  // LOBBY VIEW
  if (!gameId) {
      return (
        <div className="min-h-screen bg-stone-900 text-stone-100 flex flex-col items-center justify-center p-4 font-sans">
            <h1 className="text-6xl font-black mb-12 text-amber-500 tracking-wider drop-shadow-lg">CHECKERS</h1>
            
            <div className="bg-stone-800 p-8 rounded-xl shadow-2xl border border-stone-700 w-full max-w-md space-y-8">
                
                {/* Create Game */}
                <div className="text-center">
                    <button 
                        onClick={handleCreateGame}
                        className="w-full py-4 bg-amber-600 hover:bg-amber-500 text-white font-bold text-xl rounded-lg transition-colors shadow-lg"
                    >
                        Create New Game
                    </button>
                    <p className="mt-2 text-stone-400 text-sm">Start a new game as RED</p>
                </div>

                <div className="relative flex items-center justify-center">
                    <div className="border-t border-stone-600 w-full"></div>
                    <span className="absolute bg-stone-800 px-3 text-stone-500 font-mono">OR</span>
                </div>

                {/* Join Game */}
                <div>
                    <label className="block text-stone-300 text-sm font-bold mb-2">Join Existing Game</label>
                    <div className="flex gap-2">
                        <input 
                            type="text" 
                            placeholder="Game ID"
                            value={joinInputId}
                            onChange={(e) => setJoinInputId(e.target.value)}
                            className="flex-1 bg-stone-900 border border-stone-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition-colors"
                        />
                        <button 
                            onClick={handleManualJoin}
                            disabled={!joinInputId}
                            className="px-6 bg-stone-700 hover:bg-stone-600 disabled:opacity-50 text-white font-bold rounded-lg transition-colors"
                        >
                            Join
                        </button>
                    </div>
                </div>

                {error && (
                    <div className="p-3 bg-red-900/50 border border-red-500/50 rounded text-red-200 text-sm text-center">
                        {error}
                    </div>
                )}
            </div>
        </div>
      );
  }

  // If gameId is present but game not loaded (and not loading), show nothing or error
  if (!game) {
      return (
        <div className="min-h-screen bg-stone-900 text-white flex flex-col items-center justify-center">
            {error ? (
                <div className="text-center">
                    <div className="text-2xl text-red-400 mb-4">Error: {error}</div>
                    <button onClick={() => navigate("/")} className="text-blue-400 hover:underline">Return to Lobby</button>
                </div>
            ) : (
                <div>Connecting to game...</div>
            )}
        </div>
      );
  }

  const isMyTurn = game.current_turn === myColor;

  // Prepare Render Board (Flip if Red)
  let renderBoard = game.board;
  // Deep copy for rendering logic
  let displayBoard = [...renderBoard.map(r => [...r])]; 
  
  if (myColor === "red") {
      displayBoard = displayBoard.reverse().map(row => row.reverse());
  }

  return (
    <div className="min-h-screen bg-stone-900 text-stone-100 flex flex-col items-center justify-center p-4 font-sans">
      
      {/* Header Info */}
      <div className="mb-6 w-full max-w-lg flex flex-col items-center gap-4">
        
        {/* Game ID Badge */}
        <div className="bg-stone-800 px-4 py-1 rounded-full text-stone-400 font-mono text-xs border border-stone-700 max-w-full overflow-hidden text-ellipsis whitespace-nowrap">
            Game ID: <span className="text-amber-500 font-bold text-xs">{game.id}</span>
        </div>

        {/* Player Status */}
        <div className="flex gap-2 items-center">
            <span className="text-stone-400">You are playing as:</span>
            <span className={clsx("font-bold px-3 py-1 rounded uppercase text-sm", 
                myColor === "red" ? "bg-red-900 text-red-100 border border-red-500" :
                myColor === "black" ? "bg-slate-800 text-slate-100 border border-slate-500" :
                "bg-purple-900 text-purple-100"
            )}>
                {myColor}
            </span>
        </div>
      </div>
      
      {/* Turn Indicator */}
      <div className="flex justify-between items-center w-full max-w-lg mb-6 px-4">
        <div className={clsx("px-6 py-3 rounded-lg transition-all duration-300 border-2", 
            game.current_turn === "red" 
                ? "bg-red-900/50 border-red-500 text-red-100 shadow-[0_0_15px_rgba(239,68,68,0.5)] scale-105" 
                : "border-transparent text-stone-600 opacity-30 scale-95")}>
          <span className="font-bold text-lg">RED</span>
        </div>
        
        <div className="flex flex-col items-center">
            <div className={clsx("text-xs font-bold uppercase tracking-widest mb-1 transition-colors duration-500", isMyTurn ? "text-green-400 animate-pulse" : "text-stone-600")}>
                {isMyTurn ? "YOUR TURN" : "OPPONENT'S TURN"}
            </div>
            {/* Visual Flash Bar */}
            <div className={clsx("w-24 h-2 rounded-full overflow-hidden transition-all duration-500 shadow-lg", isMyTurn ? "bg-green-500 shadow-green-500/50" : "bg-stone-800")}></div>
        </div>

        <div className={clsx("px-6 py-3 rounded-lg transition-all duration-300 border-2", 
            game.current_turn === "black" 
                ? "bg-slate-800 border-slate-400 text-slate-100 shadow-[0_0_15px_rgba(148,163,184,0.5)] scale-105" 
                : "border-transparent text-stone-600 opacity-30 scale-95")}>
          <span className="font-bold text-lg">BLACK</span>
        </div>
      </div>

      {game.winner && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm transition-opacity duration-1000">
            <div className="bg-stone-800 p-12 rounded-2xl border-4 border-amber-500 text-center shadow-2xl animate-fade-in-up">
                <h2 className="text-6xl font-black text-amber-400 mb-4 tracking-tight drop-shadow-xl">{game.winner.toUpperCase()} WINS!</h2>
                <button 
                    onClick={handleBackToLobby}
                    className="mt-6 px-8 py-3 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg transition-colors"
                >
                    Back to Lobby
                </button>
            </div>
        </div>
      )}
      
      {error && (
        <div className="mb-6 text-red-200 font-semibold bg-red-900/80 border border-red-500 px-6 py-3 rounded-lg shadow-lg animate-pulse">
          ⚠️ {error}
        </div>
      )}

      {/* Board Container */}
      <div className={clsx("relative p-3 bg-stone-700 rounded-lg shadow-2xl transition-opacity duration-300", !isMyTurn && "opacity-90")}>
          <div 
            className="grid grid-cols-8 gap-0 border-4 border-[#5c4033] bg-[#5c4033]" 
            style={{ 
                width: "min(80vh, 80vw)", 
                height: "min(80vh, 80vw)",
                maxHeight: "600px",
                maxWidth: "600px"
            }}
          >
            {displayBoard.map((row, rIndex) => (
            row.map((cell, cIndex) => {
                // Determine logic coords for isSelected/LastMove check
                let logicRow = rIndex;
                let logicCol = cIndex;
                if (myColor === "red") {
                    logicRow = 7 - rIndex;
                    logicCol = 7 - cIndex;
                }
                
                // Check Last Move
                const isLastMoveSource = game.last_move?.start_row === logicRow && game.last_move?.start_col === logicCol;
                const isLastMoveDest = game.last_move?.end_row === logicRow && game.last_move?.end_col === logicCol;

                return (
                <div key={`${rIndex}-${cIndex}`} className="w-full h-full">
                    <Square
                    row={rIndex}
                    col={cIndex}
                    piece={cell}
                    isSelected={selectedSquare?.[0] === logicRow && selectedSquare?.[1] === logicCol}
                    isLastMoveSource={isLastMoveSource}
                    isLastMoveDest={isLastMoveDest}
                    isValidTarget={false} 
                    onClick={() => handleSquareClick(rIndex, cIndex)}
                    />
                </div>
                );
            })
            ))}
          </div>
          
          {/* Waiting for Opponent Overlay */}
          {!game.black_player_id && (
              <div className="absolute inset-0 z-40 bg-black/60 flex flex-col items-center justify-center text-center p-6 backdrop-blur-sm rounded-lg">
                  <div className="text-3xl font-bold text-white mb-2">Waiting for Opponent...</div>
                  <div className="text-stone-300 mb-6">Share this link with a friend:</div>
                  
                  <div className="flex gap-2 max-w-full">
                    <div className="bg-stone-800 text-amber-500 text-lg font-mono font-bold px-4 py-3 rounded-lg border-2 border-amber-500/50 shadow-lg select-all overflow-x-auto whitespace-nowrap max-w-[50vw]">
                        {window.location.href}
                    </div>
                    <button 
                        onClick={() => navigator.clipboard.writeText(window.location.href)}
                        className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded-lg font-bold transition-colors"
                        title="Copy Link"
                    >
                        Copy
                    </button>
                  </div>
              </div>
          )}
      </div>
    </div>
  );
}

export default App;
