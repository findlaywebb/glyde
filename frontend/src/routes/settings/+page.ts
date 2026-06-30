/**
 * Settings page options — PREF owns.
 *
 * The Settings page is client-rendered (`ssr = false`): its first paint reads the `localStorage`
 * preferences mirror synchronously (§5.10), which only exists in the browser, so server-rendering
 * would paint defaults and then mismatch on hydration. Skipping SSR makes the instant-mirror paint
 * the single source of the first frame; the store reconciles from the server on mount.
 */
export const ssr = false;
