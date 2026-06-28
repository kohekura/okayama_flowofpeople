"use client";

type CurrentLocationButtonProps = {
  onClick?: () => void;
  isLoading?: boolean;
  hasLocation?: boolean;
};

export default function CurrentLocationButton({
  onClick,
  isLoading = false,
  hasLocation = false
}: CurrentLocationButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isLoading}
      className={`case-panel grid h-12 w-12 place-items-center rounded-full text-xl transition active:scale-95 disabled:opacity-70 ${
        hasLocation ? "text-cyan-200" : "text-slate-200"
      }`}
      aria-label="現在地を表示"
      title="現在地を表示"
    >
      {isLoading ? "…" : "◎"}
    </button>
  );
}
