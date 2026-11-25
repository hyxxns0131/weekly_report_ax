"use client";
// 이번 주 실행(가장 최근 run) 찾기 (KHS 공통). 화면마다 같은 run을 쓴다.
import { useEffect, useState } from "react";
import { getLatestRun } from "../api/core";
import type { Run } from "../types/core";

export type RunState =
  | { kind: "loading" }
  | { kind: "none" }
  | { kind: "error"; message: string }
  | { kind: "ok"; run: Run };

export function useCurrentRun(): RunState {
  const [state, setState] = useState<RunState>({ kind: "loading" });
  useEffect(() => {
    getLatestRun()
      .then((run) => setState(run ? { kind: "ok", run } : { kind: "none" }))
      .catch((e: unknown) => setState({ kind: "error", message: e instanceof Error ? e.message : "오류" }));
  }, []);
  return state;
}
