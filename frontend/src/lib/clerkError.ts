/** Clerk API 에러에서 사람이 읽을 메시지를 안전하게 뽑는다. */
export function clerkErrorMessage(err: unknown, fallback: string): string {
  const errors = (err as { errors?: { message?: string; longMessage?: string }[] })?.errors;
  return errors?.[0]?.longMessage || errors?.[0]?.message || fallback;
}
