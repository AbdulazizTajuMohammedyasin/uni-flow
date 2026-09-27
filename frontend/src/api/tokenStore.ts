/**
 * Holds the access token in memory only (never localStorage), so injected scripts cannot
 * read it from storage. It is lost on page reload and restored from the refresh-token
 * cookie (see AuthContext).
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
