function isRateLimitError(message: string): boolean {
  return /rate limit/i.test(message);
}

export default function ErrorNotice({ message, className = "" }: { message: string; className?: string }) {
  if (isRateLimitError(message)) {
    return (
      <div className={`text-sm text-goldLight bg-gold/10 border border-gold/25 rounded-xl px-3.5 py-2.5 ${className}`}>
        ⏳ High demand right now — the AI provider's rate limit was hit. This usually resolves in a few minutes. Try again shortly!
      </div>
    );
  }

  return <div className={`text-sm text-rose ${className}`}>{message}</div>;
}
