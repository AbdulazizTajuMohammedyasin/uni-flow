/**
 * The UniFlow phone app (the uniflow-mobile repository) shows this website in a WebView. It
 * announces itself with `window.UniFlowApp` and the phone's push address; the website, which
 * holds the login, registers the phone with the API. Everything here does nothing in an
 * ordinary browser. Never send login tokens or personal data to the app.
 */

type Platform = 'android' | 'ios'

declare global {
  interface Window {
    UniFlowApp?: { bridgeVersion: 1; platform: Platform; appVersion: string; pushToken: string | null }
    ReactNativeWebView?: { postMessage(message: string): void }
  }
}

/** The app's event with the phone's push address (`token` is null when notifications are off). */
export const PUSH_TOKEN_EVENT = 'uniflow:push-token'
export type PushTokenDetail = { token: string | null; platform?: Platform }

/** Whether the website is running inside the UniFlow app. */
export const inApp = () => window.UniFlowApp !== undefined

/** The phone's push address, when the app has one. */
export const pushToken = () => window.UniFlowApp?.pushToken ?? null

/** A message to the app, e.g. tellApp({ type: 'session', signedIn: true }). */
export function tellApp(message: Record<string, unknown>) {
  window.ReactNativeWebView?.postMessage(JSON.stringify({ v: 1, ...message }))
}
