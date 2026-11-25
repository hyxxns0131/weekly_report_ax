"use client";
// 이번 주 현황 (C-06, KHS). DESIGN.md 3장: 진행 칸 2개 + 사람이 확인할 일.
// 버튼은 [주간 실행 만들기](실행이 없을 때만)와 [이어서 하기]뿐이다.

import { useState } from "react";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { Loading } from "../components/ui/Loading";
import { useRunStatus } from "../components/ui/RunStatusContext";
import { createRun } from "../lib/api/core";
import { LaneCard } from "./_components/LaneCard";
import { TodoList } from "./_components/TodoList";

const TEXT = {
  title: "이번 주 현황",
  empty: "이번 주 실행이 없습니다.",
  create: "주간 실행 만들기",
  createFailed: "주간 실행을 만들지 못했습니다",
};

export default function HomePage() {
  const { state, reload } = useRunStatus();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onCreate() {
    setBusy(true);
    setError(null);
    try {
      await createRun();
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : TEXT.createFailed);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <h1 style={{ margin: "0 0 16px", fontSize: 22 }}>{TEXT.title}</h1>
      {error && <ErrorState message={error} />}
      {state.kind === "loading" && <Loading />}
      {state.kind === "error" && <ErrorState message={state.message} onRetry={reload} />}
      {state.kind === "none" && (
        <EmptyState
          message={TEXT.empty}
          action={
            <button type="button" className="primary" onClick={onCreate} disabled={busy}>
              {TEXT.create}
            </button>
          }
        />
      )}
      {state.kind === "ok" && (
        <>
          <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
            <LaneCard group="b1" status={state.status} />
            <LaneCard group="b2" status={state.status} />
          </div>
          <TodoList todos={state.status.todos} />
        </>
      )}
    </>
  );
}
