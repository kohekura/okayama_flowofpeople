"use client";

import type { PlaceFeature } from "@/lib/types";
import HeLevel from "./HeLevel";

type PinCardProps = {
  place: PlaceFeature | null;
  isStocked: boolean;
  onToggleStock: (placeId: string) => void;
  onClose: () => void;
};

const SOURCE_CONFIRMED = "\u51fa\u5178\u78ba\u8a8d\u6e08\u307f";
const CANDIDATE = "\u5019\u88dc";
const PROGRAM = "\u756a\u7d44";
const CAME = "\u6765\u3066\u3044\u305f";
const REGULAR_SPOT = "\u884c\u304d\u3064\u3051";
const WENT_OFTEN = "\u901a\u3063\u305f";
const OFTEN_GO = "\u3088\u304f\u884c\u304f";
const BESCON = "\u30d9\u30b9\u30b3\u30f3\u30b0\u30eb\u30e1";

function getClueLabel(place: PlaceFeature) {
  const { properties } = place;
  const text = [
    properties.sourceProgram,
    properties.sourceEpisode,
    properties.talkSummary
  ].join(" ");
  const hasTalkContext =
    text.includes(PROGRAM) || text.includes(CAME) || text.includes(REGULAR_SPOT);
  const hasRegularContext =
    text.includes(REGULAR_SPOT) ||
    text.includes(WENT_OFTEN) ||
    text.includes(OFTEN_GO) ||
    text.includes(CAME);

  if (hasRegularContext && properties.sourceStatus === SOURCE_CONFIRMED) {
    return "\u884c\u304d\u3064\u3051\u7cfb";
  }

  if (properties.sourceProgram?.includes(BESCON)) {
    return "\u756a\u7d44\u8a2a\u554f";
  }

  if (hasTalkContext && properties.sourceStatus === SOURCE_CONFIRMED) {
    return "\u767a\u8a00\u3042\u308a";
  }

  if (hasTalkContext) {
    return "\u767a\u8a00\u5019\u88dc";
  }

  if (properties.role === "anchor") {
    return "\u8d77\u70b9\u78ba\u8a8d";
  }

  return "\u516c\u958b\u60c5\u5831";
}

export default function PinCard({ place, isStocked, onToggleStock, onClose }: PinCardProps) {
  if (!place) {
    return null;
  }

  const { properties } = place;
  const sourceStatus = properties.sourceStatus ?? CANDIDATE;
  const clueLabel = getClueLabel(place);

  return (
    <section className="case-panel-solid fixed inset-x-0 bottom-0 z-30 mx-auto max-w-xl rounded-t-[28px]">
      <div className="mx-auto mt-2.5 h-1.5 w-12 rounded-full bg-cyan-200/35" />
      <div className="max-h-[72dvh] overflow-y-auto px-4 pb-[calc(18px+env(safe-area-inset-bottom))] pt-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="case-eyebrow">field note</p>
            <p className="mt-1 text-sm font-bold leading-snug text-cyan-200">{properties.catch}</p>
            <h2 className="mt-1 text-[23px] font-black leading-tight text-cyan-50">{properties.name}</h2>
          </div>
          <div className="flex shrink-0 gap-2">
            <button
              type="button"
              onClick={() => onToggleStock(properties.id)}
              className={`min-h-11 rounded-full border px-3 text-[11px] font-black tracking-[0.12em] transition active:scale-[0.96] ${
                isStocked
                  ? "border-amber-200/45 bg-amber-300/20 text-amber-100 shadow-[0_0_18px_rgba(252,211,77,0.2)]"
                  : "border-cyan-100/15 bg-slate-900 text-slate-300"
              }`}
              aria-label={isStocked ? "\u30b9\u30c8\u30c3\u30af\u304b\u3089\u5916\u3059" : "\u30b9\u30c8\u30c3\u30af\u3059\u308b"}
            >
              {isStocked ? "STOCKED" : "STOCK"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="grid h-11 w-11 place-items-center rounded-full border border-cyan-100/15 bg-slate-900 text-2xl leading-none text-cyan-100"
              aria-label="\u30ab\u30fc\u30c9\u3092\u9589\u3058\u308b"
            >
              x
            </button>
          </div>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="case-chip text-sm">{properties.category}</span>
          <span className="case-chip text-sm text-cyan-200">{clueLabel}</span>
          <span className="case-chip text-sm text-blue-200">{sourceStatus}</span>
          <HeLevel value={properties.heLevel} compact />
        </div>

        <div className="mt-4">
          <p className="case-eyebrow text-slate-400">cast</p>
          <p className="mt-1 text-[14px] font-semibold leading-relaxed text-cyan-50">
            {properties.relatedComedians.join(" / ")}
          </p>
        </div>

        {(properties.sourceProgram || properties.talkSummary) ? (
          <div className="mt-4 rounded-2xl border border-cyan-100/20 bg-cyan-300/8 px-4 py-3 shadow-[0_0_22px_rgba(34,211,238,0.08)]">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded-full px-2.5 py-1 text-xs font-bold ${
                  sourceStatus === SOURCE_CONFIRMED
                    ? "bg-cyan-300 text-slate-950"
                    : "bg-amber-300/15 text-amber-200"
                }`}
              >
                {sourceStatus}
              </span>
              <span className="case-eyebrow text-cyan-200">source</span>
            </div>
            {properties.sourceProgram ? (
              <p className="mt-2 text-[15px] font-bold leading-snug text-cyan-50">
                {properties.sourceProgram}
              </p>
            ) : null}
            {properties.sourceEpisode ? (
              <p className="mt-1 text-sm font-semibold leading-snug text-slate-300">
                {properties.sourceEpisode}
              </p>
            ) : null}
            {properties.talkSummary ? (
              <p className="mt-2 text-[14px] leading-relaxed text-slate-100">
                {properties.talkSummary}
              </p>
            ) : null}
            {properties.sourceDate ? (
              <p className="mt-2 text-xs font-semibold text-slate-400">{properties.sourceDate}</p>
            ) : null}
            {properties.sourceUrl ? (
              <a
                href={properties.sourceUrl}
                target="_blank"
                rel="noreferrer"
                className="mt-2 inline-flex text-sm font-bold text-cyan-300"
              >
                {"\u51fa\u5178\u3092\u898b\u308b"}
              </a>
            ) : null}
          </div>
        ) : null}

        {properties.scene ? (
          <div className="mt-4 rounded-2xl border border-cyan-100/10 bg-slate-900 px-4 py-3">
            <p className="case-eyebrow text-slate-400">why here</p>
            <p className="mt-1 text-[14px] font-semibold leading-relaxed text-slate-100">
              {properties.scene}
            </p>
          </div>
        ) : null}

        <div className="mt-4 rounded-2xl border border-cyan-100/10 bg-slate-900 px-4 py-3">
          <p className="case-eyebrow">note</p>
          <p className="mt-1 text-[14px] leading-relaxed text-slate-100">{properties.story}</p>
        </div>

        <a
          href={properties.googleMapsUrl}
          target="_blank"
          rel="noreferrer"
          className="case-action sticky bottom-0 mt-5 flex items-center justify-center"
        >
          {"Google\u30de\u30c3\u30d7\u3067\u958b\u304f"}
        </a>
      </div>
    </section>
  );
}
