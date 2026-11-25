"use client";
// 설정 (B1-15, LSH). DESIGN.md 7장.

import { AiStatusBar } from "../../components/ui/AiStatusBar";
import { useState } from "react";
import { CustomerKeywords } from "./_components/CustomerKeywords";
import { SourceSettings } from "./_components/SourceSettings";

const TEXT = { title: "설정", sources: "출처", customers: "고객사 키워드" };

export default function SettingsPage() {
  const [tab, setTab] = useState<"sources" | "customers">("sources");
  return (
    <>
      <h1 style={{ fontSize: 22 }}>{TEXT.title}</h1>
      <AiStatusBar usage="AI 회사·모델은 여기서 바꾸면 모든 탭에 같이 적용됩니다. 키는 .env에만 넣습니다" />
      <div style={{ marginBottom: 12 }}>
        <button type="button" onClick={() => setTab("sources")} className={tab === "sources" ? "primary" : undefined}>{TEXT.sources}</button>{" "}
        <button type="button" onClick={() => setTab("customers")} className={tab === "customers" ? "primary" : undefined}>{TEXT.customers}</button>
      </div>
      {tab === "sources" ? <SourceSettings /> : <CustomerKeywords />}
    </>
  );
}
