"use client";
// 알림 팝업 — 이번 주 바뀐 점 (KHS, DESIGN.md 3-2). 버튼은 소식 누르기(읽음)·×(지우기)·[원문 보기]뿐.
import type { Notice, NoticeList } from "../../lib/types/core";
import { AiBadge, Badge } from "./Badge";
import { color } from "./tokens";

const TEXT = {
  title: "이번 주 바뀐 점",
  help1: "눌러서 읽으면 빨간 표시가 사라져요.",
  help2: "계속 볼 소식은 두고, 필요 없으면 ×로 지우세요.",
  none: "이번 주 새로 시행된 법령 개정·검사지시는 해당 없음.",
  allGone: "남은 알림이 없어요.",
  law: "법령 개정",
  inspection: "통관단계 검사지시",
  fresh: "새 소식",
  read: (by: string | null, at: string | null) => `읽음 · ${by ?? ""} ${at ? at.slice(5, 10).replace("-", "/") : ""}`,
  dismiss: "지우기",
  open: "원문 보기",
  noUrl: "원문 링크 확인 필요",
  check: "확인 필요",
  effective: "시행",
  foodTypes: "관련 식품유형",
  customers: "관련 고객사",
  source: "출처",
  crossMatch: "공문과 일치",
  crossCheck: "공문 확인 필요",
};

const SOURCE: Record<string, string> = {
  impfood_unfit: "정보마루 부적합",
  impfood_inspection: "정보마루 검사지시",
  impfood_law_policy: "정보마루 법령·정책",
  mfds_notice: "식약처 제개정고시",
  gyeongin_newsletter: "경인청 뉴스레터",
  law_api: "법제처",
  gmail_inbox: "Gmail 수신",
  manual: "직접 올림",
};

function Line({ n }: { n: Notice }) {
  if (n.kind === "law_change") {
    return (
      <>
        {TEXT.effective} {n.effective_at ?? TEXT.check}
        {n.food_types.length > 0 && ` · ${TEXT.foodTypes}: ${n.food_types.join(", ")}`}
      </>
    );
  }
  return (
    <>
      {TEXT.customers}: {n.customers.length ? n.customers.join(", ") : "-"}
      {n.source && ` · ${TEXT.source}: ${SOURCE[n.source] ?? n.source}`}
    </>
  );
}

export function NoticePopup({
  data,
  onRead,
  onDismiss,
}: {
  data: NoticeList | null;
  onRead: (n: Notice) => void;
  onDismiss: (n: Notice) => void;
}) {
  return (
    <div
      role="dialog"
      aria-label={TEXT.title}
      style={{
        position: "absolute",
        right: 0,
        top: 52,
        width: 400,
        maxWidth: "90vw",
        maxHeight: "70vh",
        overflowY: "auto",
        background: color.surface,
        border: `1px solid ${color.border}`,
        borderRadius: 14,
        boxShadow: "0 8px 24px rgba(15, 42, 68, 0.16)",
        padding: 16,
        zIndex: 50,
        textAlign: "left",
      }}
    >
      <div style={{ fontWeight: 800, fontSize: 16 }}>{TEXT.title}</div>
      <p style={{ margin: "4px 0 12px", fontSize: 13, color: color.muted }}>
        {TEXT.help1}
        <br />
        {TEXT.help2}
      </p>
      {data && data.total === 0 && <p style={{ color: color.muted }}>{TEXT.none}</p>}
      {data && data.total > 0 && data.items.length === 0 && <p style={{ color: color.muted }}>{TEXT.allGone}</p>}
      {data?.items.map((n) => {
        const unread = n.read_at === null;
        return (
          <article
            key={n.id}
            onClick={() => unread && onRead(n)}
            style={{
              position: "relative",
              border: `1px solid ${unread ? "#f5c98a" : color.border}`,
              background: unread ? "#fff7ec" : color.surface,
              borderRadius: 10,
              padding: "10px 40px 10px 12px",
              marginBottom: 10,
              cursor: unread ? "pointer" : "default",
              fontWeight: unread ? 600 : 400,
            }}
          >
            <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", marginBottom: 4 }}>
              {unread && <span aria-hidden style={{ width: 8, height: 8, borderRadius: 999, background: color.danger }} />}
              <Badge tone={n.kind === "law_change" ? "info" : "warning"}>
                {n.kind === "law_change" ? TEXT.law : TEXT.inspection}
              </Badge>
              <span style={{ fontSize: 12, color: unread ? color.danger : color.muted }}>
                {unread ? TEXT.fresh : TEXT.read(n.read_by, n.read_at)}
              </span>
            </div>
            <div style={{ fontWeight: 700 }}>{n.title}</div>
            <div style={{ fontSize: 14 }}>
              {n.summary ?? TEXT.check} {n.summary_is_ai && <AiBadge />}
            </div>
            {n.kind === "law_change" && (
              <div style={{ marginTop: 4 }}>
                <Badge tone={n.crosscheck === "match" ? "success" : "warning"}>
                  {n.crosscheck === "match" ? TEXT.crossMatch : TEXT.crossCheck}
                </Badge>
              </div>
            )}
            <div style={{ fontSize: 13, color: color.muted, marginTop: 4 }}>
              <Line n={n} />
            </div>
            <div style={{ marginTop: 4, fontSize: 13 }}>
              {n.url ? (
                <a
                  href={n.url}
                  target="_blank"
                  rel="noreferrer"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (unread) onRead(n);
                  }}
                >
                  {TEXT.open}
                </a>
              ) : (
                <span style={{ color: color.muted }}>{TEXT.noUrl}</span>
              )}
            </div>
            <button
              type="button"
              aria-label={`${TEXT.dismiss}: ${n.title}`}
              title={TEXT.dismiss}
              onClick={(e) => {
                e.stopPropagation();
                onDismiss(n);
              }}
              style={{ position: "absolute", top: 6, right: 6, padding: "2px 9px", fontSize: 16, lineHeight: 1.4 }}
            >
              ×
            </button>
          </article>
        );
      })}
    </div>
  );
}
