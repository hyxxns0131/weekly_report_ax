// 단계 이름·경로 목록 (KHS). 단계 바·현황 화면·사이드바가 이 목록 하나만 쓴다 (DESIGN.md 1-0).
// key는 backend/app/core/runs/service.py의 단계 key와 같다.
import type { StepGroup } from "../../lib/types/core";

export interface StepDef {
  key: string;
  group: StepGroup;
  name: string;
  href: string;
}

export const GROUPS: Record<StepGroup, { name: string; owner: string; href: string }> = {
  b1: { name: "자료 선별·고객사 매칭", owner: "LSH", href: "/collect/" },
  b2: { name: "보고서·메일", owner: "KHW", href: "/drafts/" },
};

export const STEPS: StepDef[] = [
  { key: "select", group: "b1", name: "자료 선별", href: "/collect/" },
  { key: "match", group: "b1", name: "고객사 판단", href: "/customers/" },
  { key: "law", group: "b1", name: "법령 정리", href: "/law/" },
  { key: "report", group: "b2", name: "보고서 조립", href: "/drafts/?step=report" },
  { key: "draft", group: "b2", name: "메일 초안", href: "/drafts/?step=draft" },
  { key: "send", group: "b2", name: "승인·발송", href: "/drafts/?step=send" },
  { key: "evaluate", group: "b2", name: "검증", href: "/evaluate/" },
];

export function stepsOf(group: StepGroup): StepDef[] {
  return STEPS.filter((s) => s.group === group);
}

export function stepHref(key: string | null, group: StepGroup): string {
  return STEPS.find((s) => s.key === key)?.href ?? GROUPS[group].href;
}

const PAGE_STEPS: Record<string, { group: StepGroup; keys: string[] }> = {
  "/collect/": { group: "b1", keys: ["select"] },
  "/customers/": { group: "b1", keys: ["match"] },
  "/law/": { group: "b1", keys: ["law"] },
  "/drafts/": { group: "b2", keys: ["report", "draft", "send"] },
  "/evaluate/": { group: "b2", keys: ["evaluate"] },
};

/** 경로가 어느 탭(사이드바 항목)에 속하는지. 현황·설정·로그인은 null */
export function groupOfPath(pathname: string): StepGroup | null {
  return PAGE_STEPS[pathname]?.group ?? null;
}

/** 지금 보고 있는 단계. ?step=이 없거나 틀리면 그 화면의 첫 단계 */
export function stepOfLocation(pathname: string, step: string | null): { group: StepGroup; key: string } | null {
  const page = PAGE_STEPS[pathname];
  if (!page) return null;
  const key = step && page.keys.includes(step) ? step : page.keys[0];
  return { group: page.group, key };
}
