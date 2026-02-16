import React from "react";
import clsx from "clsx";

interface PieceProps {
  type: string; // "r", "b", "R", "B"
}

export const Piece: React.FC<PieceProps> = ({ type }) => {
  const isRed = type.toLowerCase() === "r";
  const isKing = type === "R" || type === "B";

  return (
    <div
      className={clsx(
        "w-4/5 h-4/5 rounded-full shadow-lg flex items-center justify-center transition-transform hover:scale-105",
        isRed 
            ? "bg-red-600 border-4 border-red-800 shadow-[0_4px_6px_rgba(153,27,27,0.5)]" 
            : "bg-zinc-800 border-4 border-zinc-500 shadow-[0_4px_6px_rgba(0,0,0,0.7)]", // Improved Black visibility
        isKing && "ring-4 ring-yellow-400"
      )}
    >
      {isKing && (
        <span className="text-yellow-400 font-bold text-xl drop-shadow-md">K</span>
      )}
    </div>
  );
};
