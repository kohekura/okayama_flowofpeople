"use client";

import type { PlaceFeature, UserLocation } from "@/lib/types";
import HeLevel from "./HeLevel";

type SpotRailProps = {
  places: PlaceFeature[];
  stockedIds: string[];
  userLocation: UserLocation | null;
  onSelectPlace: (place: PlaceFeature) => void;
  onToggleStock: (placeId: string) => void;
};

function formatDistance(from: [number, number], to: [number, number]) {
  const toRadians = (degree: number) => (degree * Math.PI) / 180;
  const earthRadiusMeters = 6371000;
  const dLat = toRadians(to[1] - from[1]);
  const dLng = toRadians(to[0] - from[0]);
  const lat1 = toRadians(from[1]);
  const lat2 = toRadians(to[1]);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const meters = earthRadiusMeters * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

  if (meters < 1000) {
    return `現在地から約${Math.round(meters / 10) * 10}m`;
  }

  return `現在地から約${(meters / 1000).toFixed(1)}km`;
}

function getRoleLabel(place: PlaceFeature) {
  const sourceText = [
    place.properties.sourceProgram,
    place.properties.sourceEpisode,
    place.properties.talkSummary
  ].join(" ");

  if (
    place.properties.sourceStatus === "出典確認済み" &&
    (sourceText.includes("行きつけ") ||
      sourceText.includes("通った") ||
      sourceText.includes("よく行く") ||
      sourceText.includes("来ていた"))
  ) {
    return "行きつけ";
  }

  if (place.properties.sourceProgram?.includes("ベスコングルメ")) {
    return "訪問";
  }

  if (place.properties.role === "anchor") {
    return "起点";
  }

  if (place.properties.role === "column") {
    return "余談";
  }

  if (place.properties.sourceStatus === "要確認メモ") {
    return "候補";
  }

  return "手がかり";
}

export default function SpotRail({
  places,
  stockedIds,
  userLocation,
  onSelectPlace,
  onToggleStock
}: SpotRailProps) {
  if (places.length === 0) {
    return null;
  }

  return (
    <div className="pointer-events-auto">
      <div className="mb-2 flex items-center justify-between px-1">
        <p className="case-panel rounded-full px-3 py-1 text-[10px] font-bold tracking-[0.14em] text-cyan-100">
          NOTE {String(places.length).padStart(2, "0")}
        </p>
      </div>
      <div className="no-scrollbar flex snap-x gap-3 overflow-x-auto pb-[calc(12px+env(safe-area-inset-bottom))]">
        {places.slice(0, 10).map((place) => {
          const isStocked = stockedIds.includes(place.properties.id);

          return (
            <article
              key={place.properties.id}
              role="button"
              tabIndex={0}
              onClick={() => onSelectPlace(place)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelectPlace(place);
                }
              }}
              className="case-panel min-h-[116px] w-[258px] shrink-0 snap-start rounded-[20px] p-3.5 text-left transition active:scale-[0.98]"
            >
              <div className="flex items-start gap-3">
                <span
                  className={`grid h-11 w-11 shrink-0 place-items-center rounded-full border text-[10px] font-black ${
                    place.properties.role === "anchor"
                      ? "border-red-200/45 bg-red-400/15 text-red-100 shadow-[0_0_18px_rgba(248,113,113,0.28)]"
                      : place.properties.role === "column"
                        ? "border-slate-400/20 bg-slate-700/30 text-slate-300"
                        : "border-cyan-100/20 bg-cyan-300/10 text-cyan-200 shadow-[0_0_18px_rgba(34,211,238,0.26)]"
                  }`}
                >
                  {place.properties.category.slice(0, 2)}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center justify-between gap-2">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-[10px] font-bold ${
                        place.properties.role === "anchor"
                          ? "bg-red-400/15 text-red-100"
                          : place.properties.sourceStatus === "要確認メモ"
                            ? "bg-amber-300/15 text-amber-200"
                            : place.properties.role === "column"
                              ? "bg-slate-700/60 text-slate-300"
                              : "bg-cyan-300/10 text-cyan-200"
                      }`}
                    >
                      {getRoleLabel(place)}
                    </span>
                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        onToggleStock(place.properties.id);
                      }}
                      className={`rounded-full border px-2 py-0.5 text-[10px] font-black tracking-[0.08em] ${
                        isStocked
                          ? "border-amber-200/40 bg-amber-300/20 text-amber-100"
                          : "border-cyan-100/10 bg-slate-950/40 text-slate-400"
                      }`}
                      aria-label={isStocked ? "ストックから外す" : "ストックする"}
                    >
                      {isStocked ? "保存済" : "保存"}
                    </button>
                  </span>
                  <span className="mt-1 block truncate text-[12px] font-bold text-cyan-300/95">
                    {place.properties.catch}
                  </span>
                  <span className="mt-1 block truncate text-[15px] font-bold text-cyan-50">
                    {place.properties.name}
                  </span>
                  <span className="mt-1 block text-xs font-semibold text-slate-400">
                    {userLocation
                      ? formatDistance(userLocation.coordinates, place.geometry.coordinates)
                      : `${place.properties.category}・${place.properties.area}`}
                  </span>
                </span>
              </div>
              <div className="mt-2">
                <HeLevel value={place.properties.heLevel} compact />
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
