"use client";
// 알림 종 (KHS, DESIGN.md 3-2). 모든 화면 맨 위 줄 오른쪽. 안 읽은 소식이 있으면 빨간 원 + 숫자.
import { useCallback, useEffect, useRef, useState } from "react";
import { getNotices, markNotice } from "../../lib/api/core";
import type { Notice, NoticeAction, NoticeList } from "../../lib/types/core";
import { NoticePopup } from "./NoticePopup";
import { color } from "./tokens";

export function NoticeBell({ runId, refreshKey }: { runId: number | null; refreshKey: string }) {
  const [data, setData] = useState<NoticeList | null>(null);
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    if (runId === null) {
      setData({ items: [], unread: 0, total: 0 });
      return;
    }
    setData(await getNotices(runId).catch(() => null));
  }, [runId]);

  useEffect(() => {
    void load();
  }, [load, refreshKey]);

  // 팝업 밖을 누르면 닫는다
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  async function act(n: Notice, action: NoticeAction) {
    if (runId === null) return;
    await markNotice(n.id, action, runId).catch(() => undefined);
    await load();
  }

  const unread = data?.unread ?? 0;
  const label = unread > 0 ? `알림 열기, 안 읽은 소식 ${unread}건` : "알림 열기";

  return (
    <div ref={box} style={{ position: "relative" }}>
      <button
        type="button"
        aria-label={label}
        aria-expanded={open}
        title={label}
        onClick={() => setOpen((v) => !v)}
        style={{ width: 44, height: 44, borderRadius: 999, padding: 0, fontSize: 20, position: "relative" }}
      >
        <span aria-hidden>🔔</span>
        {unread > 0 && (
          <span
            aria-hidden
            style={{
              position: "absolute",
              top: -4,
              right: -4,
              minWidth: 20,
              height: 20,
              padding: "0 5px",
              borderRadius: 999,
              background: color.danger,
              color: "#fff",
              fontSize: 12,
              fontWeight: 800,
              lineHeight: "20px",
            }}
          >
            {unread}
          </span>
        )}
      </button>
      {open && <NoticePopup data={data} onRead={(n) => void act(n, "read")} onDismiss={(n) => void act(n, "dismiss")} />}
    </div>
  );
}
