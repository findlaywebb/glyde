/**
 * The preferences store contract — PREF owns and FREEZES this file.
 *
 * `createPrefsStore` is the single reactive source of reading `Preferences` for the app:
 * R-STAGE reads `store.current` (and persists the last-used `mode` through `store.set`), and the
 * Settings page binds its controls to it. Every consumer imports this surface and never amends it.
 *
 * The model (server is source of truth, mirrored locally; assay typed-seam discipline,
 * docs/research/assay-adoption.md §2):
 *
 * - First paint reads the `localStorage` mirror SYNCHRONOUSLY — instant and offline-safe — so a
 *   reload never flashes defaults before the network answers. `reload()` then GETs `/preferences`
 *   and reconciles `current` to the server value (the server wins when reachable).
 * - `set(patch)` is WRITE-THROUGH and optimistic: it merges the patch into `current`, mirrors the
 *   COMPLETE object to `localStorage` synchronously, then `PUT /preferences` with the COMPLETE
 *   object. `PUT` is full-replace (missing fields fall to server defaults), so the client always
 *   sends the whole `PreferencesView` — never a partial — and no field (the last-used `mode`
 *   included) is silently reset on the round-trip.
 * - Every read/write branches `{ data, error }` (a 200 is not success). A failed `PUT` keeps the
 *   optimistic local value (it is already mirrored) and surfaces the error without rolling back the
 *   user's setting, so a network blip never reverts a control.
 *
 * The `fetch` is INJECTED (defaults to the platform `fetch`) so the persist round-trip is
 * unit-testable with no server. What this file does NOT do: it applies no theme/font to the DOM
 * (that is the Settings page / R-STAGE), mints no ids, and registers no listeners.
 *
 * Reactivity contract for callers: `reload()` reads no `$state` in a tracked way (it lifts
 * `owner_id` out with `untrack`), so calling it inside a consumer's `$effect` does NOT subscribe
 * that effect to `current` — a mount-time reconcile runs once, never in a loop. And a `reload()`
 * whose GET resolves after a later `set()` does NOT overwrite the newer local value.
 */
import { untrack } from 'svelte';
import { api } from '$lib/api/client';
import type { components } from '$lib/api/schema';

/** The reading preferences wire shape — every field defaulted, mirroring core `Preferences`. */
export type PreferencesView = components['schemas']['PreferencesView'];

/** The `localStorage` key the full-object mirror is persisted under. */
export const PREFS_STORAGE_KEY = 'glyde:prefs';

/**
 * The first-run defaults — byte-identical to the core `Preferences()` defaults (mode "guided"),
 * so an offline first paint and a never-persisted server agree on the same starting point.
 */
export const DEFAULT_PREFERENCES: PreferencesView = {
	owner_id: 'local',
	mode: 'guided',
	wpm: 300,
	context: 'ab',
	ctx_scale: 0.7,
	chunk: 1,
	size_px: 64,
	letter_spacing_em: 0.04,
	font: 'atkinson',
	theme: 'dark',
	ramp: true
};

/**
 * The reactive preferences store.
 *
 * Read `store.current` directly — it is a `$state` getter, so destructuring it loses reactivity
 * (Svelte-5 rule). `set` and `reload` return once the network round-trip settles; both keep
 * `current` consistent with the `localStorage` mirror.
 */
export interface PrefsStore {
	/** The current preferences — a reactive `$state` getter; NEVER destructure. */
	readonly current: PreferencesView;
	/**
	 * Merge `patch` into `current`, mirror the FULL object to `localStorage` synchronously, then
	 * `PUT` the FULL object. Optimistic: a failed `PUT` keeps the local value, never rolls back.
	 */
	set(patch: Partial<PreferencesView>): Promise<void>;
	/** GET `/preferences`, reconcile the server value with the mirror, and update `current`. */
	reload(): Promise<void>;
}

/** Constructor arguments for {@link createPrefsStore}. */
export interface CreatePrefsStoreArgs {
	/** Injected `fetch` (defaults to the platform `fetch`) — makes the round-trip server-free in tests. */
	fetch?: typeof fetch;
	/** SSR/load-provided prefs; else the `localStorage` mirror; else {@link DEFAULT_PREFERENCES}. */
	initial?: PreferencesView;
}

/**
 * The same-origin `/api` base. openapi-fetch builds the `Request` eagerly, and a relative base has
 * no origin outside a browser document (Node/undici and jsdom both reject it), so resolve against
 * `location.origin` when one exists and fall back to the relative base for any non-browser caller.
 */
function apiBaseUrl(): string {
	return typeof location === 'undefined' ? '/api' : `${location.origin}/api`;
}

/** Read and validate the full-object `localStorage` mirror, or `null` when absent/unusable. */
function readMirror(): PreferencesView | null {
	if (typeof localStorage === 'undefined') return null;
	const raw = localStorage.getItem(PREFS_STORAGE_KEY);
	if (raw === null) return null;
	try {
		const parsed = JSON.parse(raw) as Partial<PreferencesView>;
		// Layer over the defaults so a partial or older mirror still yields a complete object.
		return { ...DEFAULT_PREFERENCES, ...parsed };
	} catch {
		return null;
	}
}

/** Mirror the COMPLETE preferences object to `localStorage` (no-op outside a browser). */
function writeMirror(prefs: PreferencesView): void {
	if (typeof localStorage === 'undefined') return;
	localStorage.setItem(PREFS_STORAGE_KEY, JSON.stringify(prefs));
}

/**
 * Construct a reactive preferences store backed by the typed seam and a `localStorage` mirror.
 *
 * @param args Injected `fetch` and the optional `initial` seed (load/SSR > mirror > defaults).
 * @returns The {@link PrefsStore} surface the app reads and persists through.
 */
export function createPrefsStore(args: CreatePrefsStoreArgs = {}): PrefsStore {
	const fetchImpl = args.fetch;
	const baseUrl = apiBaseUrl();

	// First paint: load/SSR seed wins, else the synchronous mirror, else the first-run defaults.
	let prefs = $state<PreferencesView>(args.initial ?? readMirror() ?? DEFAULT_PREFERENCES);
	// Monotonic write counter: a `reload()` whose GET resolves after a newer `set()` is discarded
	// rather than clobbering the user's optimistic change. Plain bookkeeping, not reactive state.
	let writeSeq = 0;

	return {
		get current(): PreferencesView {
			return prefs;
		},

		async set(patch: Partial<PreferencesView>): Promise<void> {
			writeSeq += 1;
			const next = { ...prefs, ...patch };
			prefs = next;
			writeMirror(next); // synchronous, before the network — instant and offline-safe
			try {
				const { error } = await api.PUT('/preferences', { body: next, fetch: fetchImpl, baseUrl });
				// A non-2xx (error) or a thrown network failure: keep the optimistic value (already
				// mirrored) and surface, never roll back the user's setting.
				if (error) console.warn('glyde: preferences PUT failed; keeping local value', error);
			} catch (cause) {
				console.warn('glyde: preferences PUT failed (offline); keeping local value', cause);
			}
		},

		async reload(): Promise<void> {
			const seqAtStart = writeSeq;
			// Lift the only `$state` read out of the tracked window: a consumer that calls
			// `reload()` from an `$effect` must not subscribe that effect to `current` (else a
			// successful reload's `prefs = data` would re-fire it — an unbounded GET loop).
			const ownerId = untrack(() => prefs.owner_id);
			try {
				const { data, error } = await api.GET('/preferences', {
					params: { query: { owner_id: ownerId } },
					fetch: fetchImpl,
					baseUrl
				});
				if (error || data === undefined) return; // offline/rejected: keep the mirror value
				if (writeSeq !== seqAtStart) return; // a set() landed during the GET — keep the newer value
				prefs = data;
				writeMirror(data); // reconcile the mirror to the server (source of truth)
			} catch {
				// Network failure: keep the mirror value already in `current` (offline-safe).
			}
		}
	};
}
