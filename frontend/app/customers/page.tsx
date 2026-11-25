"use client";
// 고객사 판단 (B1-11, LSH). DESIGN.md 5장. 고객사 이름은 이 PC 화면에서만 보인다.

import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "../../components/ui/EmptyState";
import { ErrorState } from "../../components/ui/ErrorState";
import { Loading } from "../../components/ui/Loading";
import { RunGate } from "../../components/ui/RunGate";
import { color } from "../../components/ui/tokens";
import { getCustomers } from "../../lib/api/b1/settings";
import { getMatches, setMatch } from "../../lib/api/b1/match";
import type { CustomerSetting, MatchRow } from "../../lib/types/b1";
import type { Run } from "../../lib/types/core";
import { MatchByCustomer } from "./_components/MatchByCustomer";
import { MatchByItem } from "./_components/MatchByItem";

const TEXT = {
  title: "고객사 판단",
  byItem: "항목별",
  byCustomer: "고객사별",
  empty: "고객사 판단 결과가 없습니다. 수집·선별에서 [분석 실행]을 먼저 눌러 주세요.",
  add: "+ 고객사 추가",
};

function Body({ run }: { run: Run }) {
  const [rows, setRows] = useState<MatchRow[] | null>(null);
  const [customers, setCustomers] = useState<CustomerSetting[]>([]);
  const [view, setView] = useState<"item" | "customer">("item");
  const [error, setError] = useState<string | null>(null);
  const [addItem, setAddItem] = useState("");
  const [addCust, setAddCust] = useState("");

  const load = useCallback(async () => {
    try {
      const [m, c] = await Promise.all([getMatches(run.id), getCustomers()]);
      setRows(m);
      setCustomers(c);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "불러오지 못했습니다");
    }
  }, [run.id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onSet(m: MatchRow, v: boolean) {
    await setMatch(m.item_id, m.customer_id, v);
    await load();
  }

  if (error) return <ErrorState message={error} onRetry={load} />;
  if (rows === null) return <Loading />;
  const items = [...new Map(rows.map((r) => [r.item_id, r.item_title])).entries()];
  return (
    <>
      <div style={{ marginBottom: 12 }}>
        보기:{" "}
        <button type="button" onClick={() => setView("item")} className={view === "item" ? "primary" : undefined}>{TEXT.byItem}</button>{" "}
        <button type="button" onClick={() => setView("customer")} className={view === "customer" ? "primary" : undefined}>{TEXT.byCustomer}</button>
      </div>
      {rows.length === 0 ? (
        <EmptyState message={TEXT.empty} />
      ) : view === "item" ? (
        <MatchByItem rows={rows} onSet={onSet} />
      ) : (
        <MatchByCustomer rows={rows} />
      )}
      {items.length > 0 && (
        <div style={{ marginTop: 16, padding: 12, background: color.surface, border: `1px solid ${color.border}` }}>
          {TEXT.add}:{" "}
          <select value={addItem} onChange={(e) => setAddItem(e.target.value)}>
            <option value="">항목 선택</option>
            {items.map(([id, t]) => <option key={id} value={id}>{t}</option>)}
          </select>{" "}
          <select value={addCust} onChange={(e) => setAddCust(e.target.value)}>
            <option value="">고객사 선택</option>
            {customers.map((c) => <option key={c.customer_id} value={c.customer_id}>{c.display_name} ({c.customer_id})</option>)}
          </select>{" "}
          <button type="button" disabled={!addItem || !addCust} onClick={async () => { await setMatch(addItem, addCust, true); await load(); }}>
            추가
          </button>
        </div>
      )}
    </>
  );
}

export default function CustomersPage() {
  return <RunGate title={TEXT.title}>{(run) => <Body run={run} />}</RunGate>;
}
