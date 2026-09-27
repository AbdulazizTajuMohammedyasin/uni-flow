/**
 * Holds the JWT access token in memory only (never localStorage, so a malicious script
 * cannot read it from storage). Login fills it and the refresh logic renews it (M1.9).
 */
let accessToken: string | null = null

export const tokenStore = {
  get: (): string | null => accessToken,
  set: (token: string | null): void => {
    accessToken = token
  },
  clear: (): void => {
    accessToken = null
  },
}
