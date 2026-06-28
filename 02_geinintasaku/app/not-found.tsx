"use client";

import { useEffect } from "react";

export default function NotFound() {
  useEffect(() => {
    window.location.href = "http://localhost:3002";
  }, []);

  return (
    <main className="grid h-dvh place-items-center bg-zinc-100 px-6 text-center">
      <div className="rounded-3xl bg-white px-6 py-5 shadow-map">
        <p className="text-base font-bold text-zinc-900">マップを開き直しています</p>
        <a className="mt-3 inline-block text-sm font-bold text-[#1a73e8]" href="http://localhost:3002">
          http://localhost:3002
        </a>
      </div>
    </main>
  );
}
