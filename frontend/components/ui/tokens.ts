// 색 토큰 (KHS). 화면에서 색을 직접 적지 않고 이 값만 쓴다 (DESIGN.md 11장).
// 테마 (11/28 변경): 아주 옅은 회청색 바탕 위 흰 둥근 카드(옅은 그림자), 왼쪽 파란 둥근 띠 + 흰 메뉴,
// 선택한 항목은 옅은 파랑, 지금 단계는 꽉 찬 파랑. 홈은 위쪽 파란 그라데이션 띠.
// 색만으로 구분하지 않는다: 배지에는 항상 글자를 함께 쓴다.
export const color = {
  danger: "#d93025", // 불일치, 수집 실패, 오류
  warning: "#b45309", // 담당자 수정, 검토 필요
  muted: "#6b7a90", // 확인, 승인됨, 보조 글자
  info: "#1f67c9", // AI 결과 · 담당자 확인 전
  success: "#188038", // 일치, 발송됨
  text: "#1d2939", // 본문 글자
  border: "#e3e9f2", // 테두리 (아주 옅은 회청색)
  background: "#ffffff", // 본문 바탕 (흰색)
  surface: "#ffffff", // 표·입력칸 바탕
  card: "#ffffff", // 카드 바탕 (흰색, 회청색 화면 바탕 위)
  primary: "#2672de", // 주 버튼·강조·지금 단계
  primarySoft: "#e8f2fd", // 선택한 메뉴·선택 행
  sidebar: "#ffffff", // 왼쪽 메뉴 바탕 (흰색, 바깥쪽에 파란 띠)
  frame: "#eef3fa", // 화면 바탕 (아주 옅은 회청색)
  rail: "#2f86ea", // 맨 왼쪽 둥근 띠 (파랑)
  shadow: "0 4px 18px rgba(30, 70, 140, 0.08)", // 흰 카드 그림자
} as const;

export type Tone = "danger" | "warning" | "muted" | "info" | "success";

export const space = { xs: 4, sm: 8, md: 16, lg: 24 } as const;
