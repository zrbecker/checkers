import React from "react";
import clsx from "clsx";
import { Piece } from "./Piece";

interface SquareProps {
  row: number;
  col: number;
  piece: string | null;
  isSelected: boolean;
  isLastMoveSource: boolean;
  isLastMoveDest: boolean;
  isValidTarget: boolean; // Optional: if we implement client-side validation later
  onClick: () => void;
}

export const Square: React.FC<SquareProps> = ({
  row,
  col,
  piece,
  isSelected,
  isLastMoveSource,
  isLastMoveDest,
  isValidTarget,
  onClick,
}) => {
  const isDark = (row + col) % 2 === 1;

  return (
    <div
      onClick={onClick}
      className={clsx(
        "w-full h-full flex items-center justify-center relative cursor-pointer transition-colors duration-200",
        isDark ? "bg-[#5c4033] hover:bg-[#6d4c3d]" : "bg-[#d2b48c] hover:bg-[#e6c9a3]", // Classic Wood Colors
        isSelected && "ring-inset ring-4 ring-yellow-400 bg-amber-900",
        (isLastMoveSource || isLastMoveDest) && "bg-yellow-500/40", // Highlight Last Move
        isValidTarget && "after:content-[''] after:absolute after:w-4 after:h-4 after:bg-green-500/50 after:rounded-full"
      )}
    >
        {/* Coordinate Labels */}
        {col === 0 && (
            <span className={clsx("absolute left-0.5 top-0.5 text-[10px] font-bold select-none", isDark ? "text-[#d2b48c]" : "text-[#5c4033]")}>
                {8 - row}
            </span>
        )}
        {row === 7 && (
            <span className={clsx("absolute right-0.5 bottom-0 text-[10px] font-bold select-none", isDark ? "text-[#d2b48c]" : "text-[#5c4033]")}>
                {String.fromCharCode(97 + col)}
            </span>
        )}

      {piece && <Piece type={piece} />}
    </div>
  );
};
