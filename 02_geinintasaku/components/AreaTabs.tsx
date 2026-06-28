"use client";

import type { Area } from "@/lib/types";

type AreaTabsProps = {
  areas: Area[];
  activeAreaId: string;
  onSelect: (area: Area) => void;
};

export default function AreaTabs({ areas, activeAreaId, onSelect }: AreaTabsProps) {
  return (
    <div className="no-scrollbar flex snap-x gap-2 overflow-x-auto px-1 pb-1.5">
      {areas.map((area) => {
        const isActive = area.id === activeAreaId;

        return (
          <button
            key={area.id}
            type="button"
            onClick={() => onSelect(area)}
            className={`h-9 min-w-16 shrink-0 snap-start rounded-full px-4 text-[13px] font-bold shadow-sm transition active:scale-95 ${
              isActive
                ? "bg-cyan-300 text-slate-950 shadow-[0_0_18px_rgba(103,232,249,0.48)]"
                : "case-panel text-cyan-50 hover:bg-slate-900"
            }`}
          >
            {area.name}
          </button>
        );
      })}
    </div>
  );
}
