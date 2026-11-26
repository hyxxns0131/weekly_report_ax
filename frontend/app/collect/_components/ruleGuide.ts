// ? 말풍선에 붙이는 규칙 설명 (LSH, /collect). 근거 문장(ai_reason, tip) 위에 "어떤 규칙으로 정했는지"를 한 줄로 보여 준다.
// 규칙 원본: backend/app/b1_select/classify/keyword_rules.py (선별 Q1~Q4), backend/app/b1_select/match/rules/ (고객사 판단).

export const SELECT_RULE_GUIDE: Record<string, string> = {
  Q1: "Q1 목록 출처(부적합·검사지시)면 관련. 제외 단어만 있고 식품 단어가 없으면 검토 필요",
  Q2: "Q2 제외 단어(의약품·화장품 등)면 무관. 식품 단어가 같이 있으면 검토 필요",
  Q3: "Q3 강한 단어(수입식품·검사지시 등)면 관련. 약한 단어(수입·통관)는 식품 단어와 같이 있을 때만 관련",
  Q4: "Q4 위 조건에 안 걸리면 검토 필요 (누락 방지)",
};

export const MATCH_RULE_GUIDE: Record<string, string> = {
  maker: "제조사 일치: 회사 꼬리(Co., Ltd., 주식회사 등)를 빼고 비교 → 높음",
  hs_code: "HS 코드 일치 → 높음",
  origin_food_type: "원산지 + 식품유형이 고객사 키워드와 둘 다 맞음 → 높음",
  food_type_parent: "원산지만 맞고 식품유형은 상위 분류만 맞음 → 검토 필요",
  food_type_only: "식품유형만 맞고 원산지는 다름 → 검토 필요",
};

/** ai_reason 앞의 "Qn"으로 규칙 설명을 찾는다. 없으면 빈 문자열 */
export function selectRuleGuide(reason: string): string {
  const q = reason.match(/^(Q[1-4])\b/)?.[1];
  return q ? (SELECT_RULE_GUIDE[q] ?? "") : "";
}
