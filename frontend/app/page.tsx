"use client";
// 이번 주 현황 (C-06, KHS). DESIGN.md 3장.

import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { Loading } from "../components/ui/Loading";
import { createRun, getLatestRun, getRunStatus } from "../lib/api/core";
import type { RunStatus } from "../lib/types/core";
import { RunHeader } from "./_components/RunHeader";
import { StageTable } from "./_components/StageTable";

const TEXT = {
  empty: "이번 주 실행이 없습니다.",
  create: "주간 실행 만들기",
  loadFailed: "현황을 불러오지 못했습니다",
};

type State =
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "error"; message: string }
  | { kind: "ok"; data: RunStatus };

export default function HomePage() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      const run = await getLatestRun();
      if (!run) {
        setState({ kind: "empty" });
        return;
      }
      setState({ kind: "ok", data: await getRunStatus(run.id) });
    } catch (e) {
      setState({ kind: "error", message: e instanceof Error ? e.message : TEXT.loadFailed });
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function onCreate() {
    setBusy(true);
    try {
      await createRun();
      await load();
    } catch (e) {
      setState({ kind: "error", message: e instanceof Error ? e.message : TEXT.loadFailed });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <RunHeader run={state.kind === "ok" ? state.data.run : null} onCreate={onCreate} busy={busy} />
      {state.kind === "loading" && <Loading />}
      {state.kind === "error" && <ErrorState message={state.message} onRetry={load} />}
      {state.kind === "empty" && (
        <EmptyState
          message={TEXT.empty}
          action={
            <button type="button" onClick={onCreate} disabled={busy}>
              {TEXT.create}
            </button>
          }
        />
      )}
      {state.kind === "ok" && <StageTable stages={state.data.stages} />}
    </>
  );
}
