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
        "w-[85%] h-[85%] rounded-full shadow-lg flex items-center justify-center relative transition-transform hover:scale-105", // Added relative
        isRed 
            ? "bg-gradient-to-br from-red-500 to-red-700 border-4 border-red-800 shadow-[0_4px_6px_rgba(153,27,27,0.5)]" 
            : "bg-gradient-to-br from-neutral-700 to-neutral-900 border-4 border-neutral-600 shadow-[0_4px_6px_rgba(0,0,0,0.7)]"
      )}
    >
      {isKing && (
        // Crown Icon (Simple SVG)
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="absolute w-2/3 h-2/3 text-amber-400 drop-shadow-md top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
            <title>King</title>
            <path fillRule="evenodd" d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.007 5.404.433c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.433 2.082-5.006z" clipRule="evenodd" />
        </svg>
      )}
    </div>
  );
};
