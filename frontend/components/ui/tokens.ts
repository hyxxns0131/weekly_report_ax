// 색 토큰 (KHS). 화면에서 색을 직접 적지 않고 이 값만 쓴다 (DESIGN.md 11장).
// 테마 (11/25 변경): 파란 바탕 위 흰 본문 카드, 진한 파랑 사이드바(흰 글자), 옅은 회청색 둥근 카드.
// 색만으로 구분하지 않는다: 배지에는 항상 글자를 함께 쓴다.
export const color = {
  danger: "#d93025", // 불일치, 수집 실패, 오류
  warning: "#b45309", // 담당자 수정, 검토 필요
  muted: "#6b7a90", // 확인, 승인됨, 보조 글자
  info: "#1f5fc4", // AI 결과 · 담당자 확인 전
  success: "#188038", // 일치, 발송됨
  text: "#1f2a3c", // 본문 글자
  border: "#e4e9f1", // 테두리 (아주 옅은 회청색)
  background: "#ffffff", // 본문 바탕 (흰색)
  surface: "#ffffff", // 표·입력칸 바탕
  card: "#f2f5fa", // 카드 바탕 (옅은 회청색, 테두리 없이)
  primary: "#2463cf", // 주 버튼·강조·사이드바
  primarySoft: "#e8f0fc", // 표 머리·선택 행
  sidebar: "#2463cf", // 왼쪽 메뉴 바탕 (진한 파랑, 글자는 흰색)
  frame: "#1f58bd", // 화면 바깥 바탕 (흰 본문 카드를 감싸는 파랑)
} as const;

export type Tone = "danger" | "warning" | "muted" | "info" | "success";

export const space = { xs: 4, sm: 8, md: 16, lg: 24 } as const;
