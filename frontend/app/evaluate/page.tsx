"use client";
// 검증 (B2-06, KHW). DESIGN.md 9장.

import { useEffect, useState } from "react";
import { RunGate } from "../../components/ui/RunGate";
import { getEval } from "../../lib/api/b2/evaluate";
import type { EvalResult, Run } from "../../lib/types/core";
import { EvalRunner } from "./_components/EvalRunner";
import { MetricTable } from "./_components/MetricTable";
import { MissTabs } from "./_components/MissTabs";

const TEXT = { title: "검증" };

function Body({ run }: { run: Run }) {
  const [result, setResult] = useState<EvalResult | null>(null);
  useEffect(() => {
    getEval(run.id).then(setResult).catch(() => setResult(null));
  }, [run.id]);
  return (
    <>
      <EvalRunner runId={run.id} onResult={setResult} />
      {result && (
        <>
          <p>비교한 과거 보고서: {result.golden_week}</p>
          <MetricTable result={result} />
          <MissTabs result={result} />
        </>
      )}
    </>
  );
}

export default function EvaluatePage() {
  return <RunGate title={TEXT.title}>{(run) => <Body run={run} />}</RunGate>;
}
