import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { createGame, getGame, makeMove, joinGame, makeAiMove, resignGame, offerDraw, acceptDraw, rejectDraw } from "./api";
import type { GameState } from "./types";
import { Square } from "./components/Square";
import clsx from "clsx";

const POLLING_INTERVAL = 2000;

// New PlayerControls Component
const PlayerControls = ({ 
    game, 
    myColor, 
    playerId, 
    targetColor, 
    playerName,
    onGameUpdate 
}: { 
    game: GameState, 
    myColor: string | null, 
    playerId: string, 
    targetColor: "red" | "black",
    playerName: string,
    onGameUpdate: (game: GameState) => void
}) => {
    const [isBusy, setIsBusy] = useState(false);

    // Determine if these controls should be visible/active
    // Visible if: 
    // 1. Local Mode (always visible for both sides)
    // 2. Online Mode AND I am this color
    // Use playerName just to silence unused var warning if needed, or remove it from props if truly unused
    // Actually let's use it for the confirmation dialog
    const isVisible = game.mode === "local" || (game.mode !== "local" && myColor === targetColor);
    
    if (!isVisible || game.status !== "active") return null;

    const handleResign = async () => {
        // Use playerName in confirmation
        if (!window.confirm(`Resign as ${targetColor.toUpperCase()} (${playerName})?`)) return;
        setIsBusy(true);
        try {
            const updatedGame = await resignGame(game.id, playerId);
            onGameUpdate(updatedGame);
        } catch (err: any) {
            console.error(err);
            alert("Failed to resign");
        } finally {
            setIsBusy(false);
        }
    };

    const handleOfferDraw = async () => {
        setIsBusy(true);
        try {
            if (game.mode === "cpu") {
                // Artificial delay to mimic thinking
                await new Promise(r => setTimeout(r, 500));
            }
            const updatedGame = await offerDraw(game.id, playerId);
            
            // If mode is CPU and no draw offer was set, it means rejected
            if (game.mode === "cpu" && !updatedGame.draw_offer) {
                 // We could use a toast, but alert is consistent with existing error handling
                 // Adding a small timeout to let the UI settle if needed, or just alert immediately
                 // Since we waited 500ms, it should feel like a response.
                 alert("Computer rejected the draw.");
            }
            onGameUpdate(updatedGame);
        } catch (err: any) {
            console.error(err);
            alert("Failed to offer draw");
        } finally {
            setIsBusy(false);
        }
    };

    const handleAcceptDraw = async () => {
        setIsBusy(true);
        try {
            const updatedGame = await acceptDraw(game.id, playerId);
            onGameUpdate(updatedGame);
        } catch (err: any) {
            console.error(err);
            alert("Failed to accept draw");
        } finally {
            setIsBusy(false);
        }
    };

    const handleRejectDraw = async () => {
        setIsBusy(true);
        try {
            const updatedGame = await rejectDraw(game.id, playerId);
            onGameUpdate(updatedGame);
        } catch (err: any) {
            console.error(err);
            alert("Failed to reject draw");
        } finally {
            setIsBusy(false);
        }
    };

    if (isBusy) {
        return (
            <div className="flex gap-2 justify-center w-full mt-2">
                <span className="text-stone-400 text-sm animate-pulse">Processing...</span>
            </div>
        );
    }

    return (
        <div className="flex gap-2 justify-center w-full mt-2">
             {/* Draw Logic */}
             {game.draw_offer ? (
                game.draw_offer !== targetColor ? (
                    <>
                        <button onClick={handleAcceptDraw} className="bg-green-600 hover:bg-green-500 text-white font-bold py-1 px-3 text-sm rounded shadow transition-colors">
                            Accept Draw
                        </button>
                        <button onClick={handleRejectDraw} className="bg-gray-600 hover:bg-gray-500 text-white font-bold py-1 px-3 text-sm rounded shadow transition-colors">
                            Reject Draw
                        </button>
                    </>
                ) : (
                     <div className="text-stone-400 font-bold py-1 px-3 text-sm border border-stone-600 rounded bg-stone-800 cursor-not-allowed">
                        Draw Offered...
                    </div>
                )
            ) : (
                <button onClick={handleOfferDraw} className="bg-stone-700 hover:bg-stone-600 text-stone-200 font-bold py-1 px-3 text-sm rounded border border-stone-600 shadow transition-colors">
                    Offer Draw
                </button>
            )}
            
            <button onClick={handleResign} className="bg-red-900/50 hover:bg-red-800/80 text-red-200 font-bold py-1 px-3 text-sm rounded border border-red-800/50 shadow transition-colors">
                Resign
            </button>
        </div>
    );
};

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
  const [playerName, setPlayerName] = useState<string>("");
  const [player2Name, setPlayer2Name] = useState<string>("");
  const [selectedMode, setSelectedMode] = useState<"online" | "cpu" | "local">("online");

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

  // Initialize Player ID and Name
  useEffect(() => {
    let storedId = localStorage.getItem("checkers_player_id");
    if (!storedId) {
        storedId = crypto.randomUUID();
        localStorage.setItem("checkers_player_id", storedId);
    }
    setPlayerId(storedId);

    const storedName = localStorage.getItem("checkers_player_name");
    if (storedName) {
        setPlayerName(storedName);
    }
  }, []);

  // Handle Routing / Game Checking
  useEffect(() => {
      if (gameId && playerId && !game) {
          const checkGameStatus = async () => {
              setLoading(true);
              try {
                  const fetchedGame = await getGame(gameId);
                  
                  // Check if I am a participant
                  const isParticipant = fetchedGame.red_player_id === playerId || fetchedGame.black_player_id === playerId;
                  
                  // Check if game is full
                  const isFull = fetchedGame.red_player_id && fetchedGame.black_player_id;
                  
                  if (isParticipant || isFull) {
                      // Go straight to board (Rejoin or Spectate)
                      setGame(fetchedGame);
                  } else {
                      // Game is open and I'm not in it -> Show Join Screen
                      setJoinInputId(gameId);
                  }
              } catch (err: any) {
                  console.error(err);
                  setJoinInputId(gameId);
                  if (err.response?.status === 404) {
                      setError("Game not found");
                  }
              } finally {
                  setLoading(false);
              }
          };
          checkGameStatus();
      } else if (!gameId && game) {
          // URL is root but we have game state -> Clear it (user went back)
          setGame(null);
      }
  }, [gameId, playerId]); // Run when ID or PlayerID is ready 

  // Polling for updates
  useEffect(() => {
    if (!game || game.status === "finished") return;

    // AI Trigger
    if (game.mode === "cpu" && game.current_turn === "black" && game.black_player_id === "CPU") {
        const triggerAi = async () => {
            try {
                // Small delay for better UX
                await new Promise(r => setTimeout(r, 500));
                const updatedGame = await makeAiMove(game.id);
                setGame(updatedGame);
                playTurnSound();
            } catch (err) {
                console.error("AI Move failed", err);
            }
        };
        triggerAi();
        return; // Skip polling if we are waiting for AI
    }

    const interval = setInterval(async () => {
      try {
        const updatedGame = await getGame(game.id);
        
        const stateChanged = JSON.stringify(updatedGame.board) !== JSON.stringify(game.board) || 
                             updatedGame.current_turn !== game.current_turn ||
                             updatedGame.black_player_id !== game.black_player_id ||
                             updatedGame.draw_offer !== game.draw_offer ||
                             updatedGame.status !== game.status ||
                             updatedGame.winner !== game.winner;

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

  const saveName = (name: string) => {
      setPlayerName(name);
      localStorage.setItem("checkers_player_name", name);
  };

  const handleCreateGame = async () => {
      if (!playerName || playerName.length < 5) {
          setError("Name must be at least 5 characters");
          return;
      }
      saveName(playerName);
      
      setLoading(true);
      try {
      const newGame = await createGame(playerId, playerName, selectedMode, player2Name);
      setGame(newGame);
      setError(null);
      navigate(`/game/${newGame.id}`);
      } catch (err: any) {
          console.error(err);
          setError(err.response?.data?.detail?.[0]?.msg || "Failed to create game");
      } finally {
          setLoading(false);
      }
  };

  const handleManualJoin = async () => {
      if (!joinInputId) return;
      if (!playerName || playerName.length < 5) {
          setError("Name must be at least 5 characters");
          return;
      }
      saveName(playerName);
      
      // If we are already on the correct URL, navigating won't trigger anything.
      // We must explicitly call the API.
      setLoading(true);
      try {
          const joinedGame = await joinGame(joinInputId, playerId, playerName);
          setGame(joinedGame);
          setError(null);
          // Update URL if we came from root
          if (!gameId) {
              navigate(`/game/${joinInputId}`);
          }
      } catch (err: any) {
          console.error(err);
          setError(err.response?.data?.detail || "Failed to join game");
      } finally {
          setLoading(false);
      }
  };

  const handleBackToLobby = () => {
      setGame(null);
      navigate("/");
  };

  let myColor: "red" | "black" | "spectator" | null = null;
  if (game) {
      if (game.mode === "local" && game.red_player_id === playerId) {
          // In local mode, if I own the game, I control whoever's turn it is
          myColor = game.current_turn;
      } else {
          if (game.red_player_id === playerId) myColor = "red";
          else if (game.black_player_id === playerId) myColor = "black";
          else myColor = "spectator";
      }
  }

  const handleSquareClick = async (visualRow: number, visualCol: number) => {
    if (!game || !myColor) return;

    // Transform Visual -> Logic
    let row = visualRow;
    let col = visualCol;
    if (myColor === "red" && game.mode !== "local") {
        row = 7 - visualRow;
        col = 7 - visualCol;
    }

    if (game.current_turn !== myColor) return;

    const piece = game.board[row][col];
    
    // Logic for selection:
    const pieceIsRed = piece?.toLowerCase() === "r";
    const pieceIsBlack = piece?.toLowerCase() === "b";
    
    if ((myColor === "red" && pieceIsRed) || (myColor === "black" && pieceIsBlack)) {
        if (selectedSquare && selectedSquare[0] === row && selectedSquare[1] === col) {
            setSelectedSquare(null); 
        } else {
            setSelectedSquare([row, col]); 
            setError(null);
        }
        return;
    }

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

  // LOBBY VIEW (No Game Loaded)
  if (!game) {
      // SCENARIO 1: We are at a specific game URL (gameId is present)
      // Show "Join THIS Game" screen
      if (gameId) {
          return (
            <div className="min-h-screen bg-stone-900 text-stone-100 flex flex-col items-center justify-center p-4 font-sans">
                <h1 className="text-5xl font-black mb-8 text-amber-500 tracking-wider drop-shadow-lg">CHECKERS</h1>
                
                <div className="bg-stone-800 p-8 rounded-xl shadow-2xl border border-stone-700 w-full max-w-md space-y-6">
                    <h2 className="text-xl font-bold text-center text-white mb-2">Join Game</h2>
                    <div className="text-center text-stone-400 font-mono text-sm mb-6 bg-stone-900 p-2 rounded truncate">
                        {gameId}
                    </div>

                    <div>
                        <label className="block text-stone-300 text-sm font-bold mb-2">Your Name</label>
                        <input 
                            type="text" 
                            placeholder="Enter your name (min 5 chars)"
                            value={playerName}
                            onChange={(e) => setPlayerName(e.target.value)}
                            className="w-full bg-stone-900 border border-stone-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition-colors"
                        />
                    </div>

                    <button 
                        onClick={handleManualJoin}
                        disabled={!playerName || playerName.length < 5}
                        className="w-full py-4 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xl rounded-lg transition-colors shadow-lg"
                    >
                        Join Game
                    </button>

                    <div className="text-center">
                        <button onClick={() => navigate("/")} className="text-stone-500 hover:text-stone-300 text-sm underline">
                            Cancel & Go to Lobby
                        </button>
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

      // SCENARIO 2: Root Lobby
      return (
        <div className="min-h-screen bg-stone-900 text-stone-100 flex flex-col items-center justify-center p-4 font-sans">
            <h1 className="text-6xl font-black mb-8 text-amber-500 tracking-wider drop-shadow-lg">CHECKERS</h1>
            
            <div className="bg-stone-800 p-8 rounded-xl shadow-2xl border border-stone-700 w-full max-w-md space-y-6">
                
                {/* Name Input */}
                <div>
                    <label className="block text-stone-300 text-sm font-bold mb-2">Your Name</label>
                    <input 
                        type="text" 
                        placeholder="Enter your name (min 5 chars)"
                        value={playerName}
                        onChange={(e) => setPlayerName(e.target.value)}
                        className="w-full bg-stone-900 border border-stone-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition-colors"
                    />
                </div>

                {selectedMode === "local" && (
                    <div>
                        <label className="block text-stone-300 text-sm font-bold mb-2">Player 2 Name</label>
                        <input 
                            type="text" 
                            placeholder="Enter opponent's name"
                            value={player2Name}
                            onChange={(e) => setPlayer2Name(e.target.value)}
                            className="w-full bg-stone-900 border border-stone-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-amber-500 transition-colors"
                        />
                    </div>
                )}

                <div className="border-t border-stone-600 my-4"></div>

                {/* Create Game */}
                <div className="text-center">
                    <div className="flex gap-2 mb-4">
                        <button 
                            onClick={() => setSelectedMode("online")}
                            className={clsx("flex-1 py-2 rounded-lg border-2 font-bold transition-all", selectedMode === "online" ? "border-amber-500 bg-amber-500/20 text-amber-500" : "border-stone-700 text-stone-500 hover:border-stone-600")}
                        >
                            Online
                        </button>
                        <button 
                            onClick={() => setSelectedMode("cpu")}
                            className={clsx("flex-1 py-2 rounded-lg border-2 font-bold transition-all", selectedMode === "cpu" ? "border-amber-500 bg-amber-500/20 text-amber-500" : "border-stone-700 text-stone-500 hover:border-stone-600")}
                        >
                            VS CPU
                        </button>
                        <button 
                            onClick={() => setSelectedMode("local")}
                            className={clsx("flex-1 py-2 rounded-lg border-2 font-bold transition-all", selectedMode === "local" ? "border-amber-500 bg-amber-500/20 text-amber-500" : "border-stone-700 text-stone-500 hover:border-stone-600")}
                        >
                            Local
                        </button>
                    </div>

                    <button 
                        onClick={handleCreateGame}
                        disabled={!playerName || playerName.length < 5}
                        className="w-full py-4 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold text-xl rounded-lg transition-colors shadow-lg"
                    >
                        Create New Game
                    </button>
                    <p className="mt-2 text-stone-400 text-sm">
                        {selectedMode === "online" && "Play against a friend online (share link)"}
                        {selectedMode === "cpu" && "Play against the computer"}
                        {selectedMode === "local" && "Pass and play on the same device"}
                    </p>
                </div>

                <div className="relative flex items-center justify-center my-2">
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
                            disabled={!joinInputId || !playerName || playerName.length < 5}
                            className="px-6 bg-stone-700 hover:bg-stone-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-lg transition-colors"
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

  const isMyTurn = game.current_turn === myColor;

  // Prepare Render Board (Flip if Red)
  let renderBoard = game.board;
  let displayBoard = [...renderBoard.map(r => [...r])]; 
  
  if (myColor === "red" && game.mode !== "local") {
      displayBoard = displayBoard.reverse().map(row => row.reverse());
  }

  // Define Player Names for Layout
  let topPlayerName = "Waiting...";
  let bottomPlayerName = "Waiting...";
  let topPlayerColor = "spectator";
  let bottomPlayerColor = "spectator";

  if (myColor === "red") {
      bottomPlayerName = game.red_player_name || "You (Red)";
      bottomPlayerColor = "red";
      topPlayerName = game.black_player_name || "Waiting for Black...";
      topPlayerColor = "black";
  } else if (myColor === "black") {
      bottomPlayerName = game.black_player_name || "You (Black)";
      bottomPlayerColor = "black";
      topPlayerName = game.red_player_name || "Waiting for Red...";
      topPlayerColor = "red";
  } else {
      // Spectator View (Standard: Red Top, Black Bottom)
      topPlayerName = game.red_player_name || "Red";
      topPlayerColor = "red";
      bottomPlayerName = game.black_player_name || "Black";
      bottomPlayerColor = "black";
  }

  return (
    <div className="min-h-screen bg-stone-900 text-stone-100 flex flex-col items-center justify-start pt-8 p-4 font-sans">
      
      {/* Header Info */}
      <div className="mb-4 w-full max-w-lg flex flex-col items-center gap-2">
        <div className="bg-stone-800 px-4 py-1 rounded-full text-stone-400 font-mono text-xs border border-stone-700 max-w-full overflow-hidden text-ellipsis whitespace-nowrap">
            Game ID: <span className="text-amber-500 font-bold text-xs">{game.id}</span>
        </div>
      </div>
      
      {/* Game Layout Container - Aligns Width of Nameplates & Board */}
      <div className="flex flex-col gap-2 w-full max-w-[600px]" style={{ width: "min(80vh, 80vw)" }}>
          
          {/* TOP PLAYER (Opponent) */}
          <div className={clsx(
              "w-full px-6 py-3 rounded-t-xl border-t-4 flex flex-col justify-between items-center transition-all duration-300",
              topPlayerColor === "red" ? "bg-red-900/20 border-red-600" : "bg-zinc-800/50 border-zinc-500",
              game.current_turn === topPlayerColor && "shadow-[0_0_15px_rgba(255,255,255,0.1)] bg-opacity-40"
          )}>
              <div className="w-full flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className={clsx("w-3 h-3 rounded-full", topPlayerColor === "red" ? "bg-red-500" : "bg-zinc-400")}></div>
                    <span className="font-bold text-xl tracking-wide text-stone-200">{topPlayerName}</span>
                </div>
                {game.current_turn === topPlayerColor && (
                    <span className="text-xs font-bold uppercase tracking-widest text-stone-400 animate-pulse">Thinking...</span>
                )}
              </div>
              
              {/* Top Controls */}
              {topPlayerColor !== "spectator" && (
                  <PlayerControls 
                    game={game} 
                    myColor={myColor} 
                    playerId={playerId} 
                    targetColor={topPlayerColor as "red" | "black"} 
                    playerName={topPlayerName}
                    onGameUpdate={setGame}
                  />
              )}
          </div>

          {/* Board Container */}
          <div className={clsx("relative p-3 bg-stone-700 shadow-2xl transition-opacity duration-300 w-full aspect-square", !isMyTurn && "opacity-95")}>
              <div 
                className="grid grid-cols-8 gap-0 border-4 border-[#5c4033] bg-[#5c4033] w-full h-full" 
              >
                {displayBoard.map((row, rIndex) => (
                row.map((cell, cIndex) => {
                    // Determine logic coords for isSelected/LastMove check
                    let logicRow = rIndex;
                    let logicCol = cIndex;
                    if (myColor === "red" && game.mode !== "local") {
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
              {game.winner && (
                <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm transition-opacity duration-1000">
                    <div className="bg-stone-800 p-12 rounded-2xl border-4 border-amber-500 text-center shadow-2xl animate-fade-in-up">
                        <h2 className="text-6xl font-black text-amber-400 mb-4 tracking-tight drop-shadow-xl">
                            {game.winner === "draw" ? "GAME DRAWN!" : `${game.winner.toUpperCase()} WINS!`}
                        </h2>
                        <div className="text-2xl text-stone-300 mb-8">
                            {game.winner === "draw" ? (
                                <span className="text-stone-400">By Agreement</span>
                            ) : (
                                <>
                                    Winner: <span className="text-amber-400 font-bold">
                                        {game.winner === "red" ? game.red_player_name : game.black_player_name}
                                    </span>
                                </>
                            )}
                        </div>
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
                <div className="absolute top-4 left-4 right-4 z-50 mb-6 text-red-200 font-semibold bg-red-900/80 border border-red-500 px-6 py-3 rounded-lg shadow-lg animate-pulse text-center">
                  ⚠️ {error}
                </div>
              )}
          </div>

          {/* BOTTOM PLAYER (Me) */}
          <div className={clsx(
              "w-full px-6 py-3 rounded-b-xl border-b-4 flex flex-col justify-between items-center transition-all duration-300",
              bottomPlayerColor === "red" ? "bg-red-900/20 border-red-600" : "bg-zinc-800/50 border-zinc-500",
              game.current_turn === bottomPlayerColor && "shadow-[0_0_15px_rgba(255,255,255,0.1)] bg-opacity-40"
          )}>
              <div className="w-full flex justify-between items-center">
                <div className="flex items-center gap-3">
                    <div className={clsx("w-3 h-3 rounded-full", bottomPlayerColor === "red" ? "bg-red-500" : "bg-zinc-400")}></div>
                    <span className="font-bold text-xl tracking-wide text-stone-200">{bottomPlayerName}</span>
                </div>
                {game.current_turn === bottomPlayerColor && (
                    <span className="text-xs font-bold uppercase tracking-widest text-green-400 animate-pulse">YOUR TURN</span>
                )}
              </div>

              {/* Bottom Controls */}
              {bottomPlayerColor !== "spectator" && (
                  <PlayerControls 
                    game={game} 
                    myColor={myColor} 
                    playerId={playerId} 
                    targetColor={bottomPlayerColor as "red" | "black"} 
                    playerName={bottomPlayerName}
                    onGameUpdate={setGame}
                  />
              )}
          </div>
      
      </div>

    </div>
  );
}

export default App;
