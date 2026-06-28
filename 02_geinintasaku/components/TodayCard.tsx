type TodayCardProps = {
  areaName: string;
  vibe?: string;
  isPreparing?: boolean;
};

export default function TodayCard({ areaName, vibe, isPreparing = false }: TodayCardProps) {
  return (
    <div className="case-panel w-[min(340px,calc(100vw-24px))] rounded-[20px] px-3.5 py-3">
      <p className="case-eyebrow">area note</p>
      <p className="mt-0.5 text-sm font-bold text-cyan-50">今夜の探索：{areaName}</p>
      <p className="mt-1.5 text-[12px] leading-[1.72] text-slate-300">
        {isPreparing
          ? "このエリアの芸人ゆかりスポットは準備中です"
          : vibe ?? "劇場・飲食店・芸人ゆかりスポットが集まっています"}
      </p>
      <div className="mt-3 space-y-2 border-t border-cyan-100/10 pt-2.5">
        <div className="flex items-start gap-2">
          <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full border border-red-200/70 bg-red-400/20 shadow-[0_0_12px_rgba(248,113,113,0.45)]">
            <span className="h-1.5 w-1.5 rounded-full bg-red-100 shadow-[0_0_8px_#f87171]" />
          </span>
          <p className="text-[11px] font-semibold leading-snug text-slate-400">
            劇場やテレビ局など、芸人が集まる場。まずはここから探索してはどうか。
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full bg-cyan-200 shadow-[0_0_12px_#67e8f9]" />
          <p className="text-[11px] font-semibold text-slate-400">発言の手がかり</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-3 w-3 rounded-full border border-cyan-100/25 bg-slate-700" />
          <p className="text-[11px] font-semibold text-slate-400">余談スポット</p>
        </div>
      </div>
    </div>
  );
}
