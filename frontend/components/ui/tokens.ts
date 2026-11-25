// 색 토큰 (KHS). 화면에서 색을 직접 적지 않고 이 값만 쓴다 (DESIGN.md 11장).
// 테마: 하늘색 + 흰색, 글자는 진한 남색으로 대비를 높인다.
// 색만으로 구분하지 않는다: 배지에는 항상 글자를 함께 쓴다.
export const color = {
  danger: "#c62828", // 불일치, 수집 실패, 오류
  warning: "#b45309", // 담당자 수정, 검토 필요
  muted: "#5b6b7f", // 확인, 승인됨, 보조 글자
  info: "#1565c0", // AI 결과 · 담당자 확인 전
  success: "#1b7a3a", // 일치, 발송됨
  text: "#0f2a44", // 본문 글자 (진한 남색)
  border: "#cfe3f5", // 테두리 (옅은 하늘)
  background: "#f2f8fd", // 화면 바탕 (아주 옅은 하늘)
  surface: "#ffffff", // 카드·표 바탕
  primary: "#1e88e5", // 주 버튼·강조
  primarySoft: "#e3f2fd", // 표 머리·선택 행
  sidebar: "#e8f4fd", // 왼쪽 메뉴 바탕
} as const;

export type Tone = "danger" | "warning" | "muted" | "info" | "success";

export const space = { xs: 4, sm: 8, md: 16, lg: 24 } as const;
