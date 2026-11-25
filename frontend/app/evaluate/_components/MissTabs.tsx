"use client";
// B2-06 누락·과다·틀린 판단 (KHW)
import { useState } from "react";
import type { EvalResult } from "../../../lib/types/core";

export function MissTabs({ result }: { result: EvalResult }) {
  const tabs = [
    ["누락 항목", result.missed_items],
    ["과다 항목", result.extra_items],
    ["틀린 고객사 판단", result.wrong_matches],
  ] as const;
  const [tab, setTab] = useState(0);
  return (
    <div style={{ marginTop: 16 }}>
      {tabs.map(([name, list], i) => (
        <button key={name} type="button" onClick={() => setTab(i)} className={tab === i ? "primary" : undefined} style={{ marginRight: 6 }}>
          {name} ({list.length})
        </button>
      ))}
      <ul>{tabs[tab][1].map((x) => <li key={x}>{x}</li>)}</ul>
    </div>
  );
}
