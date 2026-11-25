import { color } from "./tokens";

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" style={{ padding: 16, border: `1px solid ${color.danger}`, color: color.danger }}>
      <p>✖ {message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry}>
          다시 시도
        </button>
      )}
    </div>
  );
}
