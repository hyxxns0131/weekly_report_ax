"use client";
// 이번 주 실행이 있어야 쓰는 화면의 공통 틀 (KHS). 불러오는 중·오류·실행 없음을 처리한다.
import Link from "next/link";
import type { ReactNode } from "react";
import type { Run } from "../../lib/types/core";
import { useCurrentRun } from "../../lib/hooks/useCurrentRun";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";
import { Loading } from "./Loading";
import { color } from "./tokens";

export function RunGate({ title, children }: { title: string; children: (run: Run) => ReactNode }) {
  const state = useCurrentRun();
  return (
    <>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>{title}</h1>
        {state.kind === "ok" && (
          <span style={{ color: color.muted }}>
            {state.run.week_label} ({state.run.period_start} ~ {state.run.period_end})
          </span>
        )}
      </div>
      {state.kind === "loading" && <Loading />}
      {state.kind === "error" && <ErrorState message={state.message} />}
      {state.kind === "none" && (
        <EmptyState
          message="이번 주 실행이 없습니다. 이번 주 현황에서 [주간 실행 만들기]를 먼저 눌러 주세요."
          action={<Link href="/">이번 주 현황으로</Link>}
        />
      )}
      {state.kind === "ok" && children(state.run)}
    </>
  );
}
