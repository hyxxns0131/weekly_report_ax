"use client";
// 이번 주 실행과 진행 현황을 layout 한 곳에서 읽어 사이드바 배지·맨 위 줄·단계 바·현황 화면이 함께 쓴다 (KHS).
import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { getLatestRun, getRunStatus } from "../../lib/api/core";
import type { RunStatus } from "../../lib/types/core";

const TEXT = {
  oldServer: "백엔드가 예전 버전이에요. 백엔드(uvicorn)를 껐다가 다시 켜 주세요.",
};

export type RunStatusState =
  | { kind: "loading" }
  | { kind: "none" }
  | { kind: "error"; message: string }
  | { kind: "ok"; status: RunStatus };

interface Ctx {
  state: RunStatusState;
  reload: () => Promise<void>;
}

const RunStatusCtx = createContext<Ctx>({ state: { kind: "loading" }, reload: async () => undefined });

export function RunStatusProvider({ refreshKey, children }: { refreshKey: string; children: ReactNode }) {
  const [state, setState] = useState<RunStatusState>({ kind: "loading" });

  const reload = useCallback(async () => {
    try {
      const run = await getLatestRun();
      if (!run) {
        setState({ kind: "none" });
        return;
      }
      const status = await getRunStatus(run.id);
      // 백엔드가 예전 버전이면(건수·단계가 없음) 화면이 깨지지 않게 안내만 한다
      if (!status.counts || !Array.isArray(status.steps)) {
        setState({ kind: "error", message: TEXT.oldServer });
        return;
      }
      setState({ kind: "ok", status });
    } catch (e) {
      setState({ kind: "error", message: e instanceof Error ? e.message : "현황을 불러오지 못했습니다" });
    }
  }, []);

  // 화면을 옮길 때마다 건수를 새로 읽는다 (다른 화면에서 고친 내용이 배지·단계 바에 바로 보이게)
  useEffect(() => {
    void reload();
  }, [reload, refreshKey]);

  return <RunStatusCtx.Provider value={{ state, reload }}>{children}</RunStatusCtx.Provider>;
}

export function useRunStatus(): Ctx {
  return useContext(RunStatusCtx);
}
