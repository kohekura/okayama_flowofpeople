"use client";

type SearchBarProps = {
  value: string;
  onChange: (value: string) => void;
};

export default function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <label className="case-panel flex min-h-[52px] items-center gap-3 rounded-full px-4">
      <span className="grid h-8 w-8 place-items-center rounded-full border border-cyan-100/15 bg-cyan-300/10 text-base font-black text-cyan-200" aria-hidden="true">
        ⌕
      </span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="min-w-0 flex-1 bg-transparent text-base text-cyan-50 outline-none placeholder:text-slate-400"
        placeholder="芸人名・番組名・店名で探す"
        type="search"
      />
      {value ? (
        <button
          type="button"
          onClick={() => onChange("")}
          className="grid h-9 w-9 place-items-center rounded-full bg-slate-800 text-lg text-cyan-100"
          aria-label="検索を消す"
        >
          ×
        </button>
      ) : null}
    </label>
  );
}
