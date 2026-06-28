type HeLevelProps = {
  value: number;
  compact?: boolean;
};

export default function HeLevel({ value, compact = false }: HeLevelProps) {
  const safeValue = Math.max(0, Math.min(5, value));

  return (
    <div className={`flex items-center gap-2 ${compact ? "text-xs" : "text-sm"}`}>
      <span className="font-semibold text-slate-300">濃さ</span>
      <span aria-label={`濃さ ${safeValue} / 5`} className="tracking-normal text-cyan-300">
        {"★".repeat(safeValue)}
        <span className="text-slate-700">{"★".repeat(5 - safeValue)}</span>
      </span>
    </div>
  );
}
