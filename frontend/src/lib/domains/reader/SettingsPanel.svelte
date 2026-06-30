<!--
  SettingsPanel (R-CHROME / U2).

  A slide-out right panel that ports the /settings controls into the reader. Props are exactly
  FND's frozen `SettingsPanelProps` — `{ store, open, onClose }` — imported from `types.ts`.
  `open` is NOT `$bindable`: the INTEGRATOR (Reader.svelte) owns the open state and passes it
  as a plain boolean; the panel emits `onClose` when it wishes to close and the integrator flips
  `open` to false in response.

  Writes: every control calls `store.set(patch)` — identical pattern to the /settings route.
  The panel constructs no store of its own and renders nothing pacing-related (no word position,
  no time remaining, no block state).

  Close paths: (1) the Sheet's backdrop button, (2) the Sheet's built-in Esc handler, and
  (3) the explicit close button rendered at the top of the panel — all route through `onClose`.

  Mode persistence: the mode control writes through the reader's shared store via `store.set`,
  giving apply-live immediately. The durable browser-round-trip round-trip waits on the separate
  LAN-token PR and is out of scope here.
-->
<script lang="ts">
	import { X } from '@lucide/svelte';
	import Icon from '$lib/components/ui/Icon.svelte';
	import Sheet from '$lib/components/ui/Sheet.svelte';
	import Slider from '$lib/components/ui/Slider.svelte';
	import type { SettingsPanelProps, PreferencesView } from './types';

	let { store, open, onClose }: SettingsPanelProps = $props();

	// --- Option lists: canonical mode names (match /settings), plus the v2 Focus mode ---

	const MODES = [
		{ value: 'guided', label: 'Guided sweep' },
		{ value: 'rsvp', label: 'RSVP' },
		{ value: 'fading', label: 'Fading trail' },
		{ value: 'focus', label: 'Focus' }
	] as const satisfies { value: PreferencesView['mode']; label: string }[];

	const FONTS = [
		{ value: 'atkinson', label: 'Atkinson Hyperlegible' },
		{ value: 'lexend', label: 'Lexend' },
		{ value: 'opendyslexic', label: 'OpenDyslexic' },
		{ value: 'system', label: 'System' },
		{ value: 'serif', label: 'Serif' },
		{ value: 'mono', label: 'Monospace' }
	] as const satisfies { value: PreferencesView['font']; label: string }[];

	const THEMES = [
		{ value: 'dark', label: 'Dark' },
		{ value: 'light', label: 'Light' },
		{ value: 'sepia', label: 'Sepia' }
	] as const satisfies { value: PreferencesView['theme']; label: string }[];

	const CONTEXTS = [
		{ value: 'off', label: 'Off' },
		{ value: 'ab', label: 'A·B' },
		{ value: 'line', label: 'Line' },
		{ value: 'sentence', label: 'Sentence' }
	] as const satisfies { value: PreferencesView['context']; label: string }[];

	// --- Slider live-drag buffers (reassignable $derived, same pattern as Transport's railWpm) ---
	// Each follows `store.current` reactively (recomputes when the store commits or server
	// reconciles) and is OVERRIDDEN by the Slider's `bind:value` during a drag — so the label
	// tracks the thumb live without extra $state or $effect. On pointer release, `onValueChange`
	// calls `store.set(...)`, `store.current` advances, and the derived recomputes to the new
	// committed value — no synchronisation loop and no $effect needed.
	let wpm = $derived(store.current.wpm);
	let chunk = $derived(store.current.chunk);
	let sizePx = $derived(store.current.size_px);
	let letterSpacing = $derived(store.current.letter_spacing_em);
	let ctxScale = $derived(store.current.ctx_scale);
</script>

<!--
  One enum control: a labelled native <select>. One-way `selected` reflects the stored value;
  `onpick` persists the new DOM value back through the store. Same snippet pattern as /settings.
-->
{#snippet selectField(
	label: string,
	current: string,
	options: readonly { value: string; label: string }[],
	onpick: (value: string) => void
)}
	<label class="flex flex-col gap-1 font-ui text-sm text-foreground">
		<span>{label}</span>
		<select
			class="min-h-11 rounded-md border border-border bg-input px-3 text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
			onchange={(e) => onpick(e.currentTarget.value)}
		>
			{#each options as o (o.value)}
				<option value={o.value} selected={o.value === current}>{o.label}</option>
			{/each}
		</select>
	</label>
{/snippet}

<!--
  The Sheet primitive handles Esc and the backdrop tap — both route through its `onClose`
  callback, which is our `onClose` prop. `open` is passed one-way (NOT $bindable): the Sheet
  manages its own visibility on close, then calls our `onClose`; the INTEGRATOR responds by
  setting its `open` state to false, completing the round-trip.
-->
<Sheet {open} side="right" title="Reading settings" {onClose}>
	<!-- Close button — third close path alongside backdrop and Esc. Aligned to the top-right of
	     the panel contents (below Sheet's own <h2> title). min-h-11/min-w-11 for ≥44px target. -->
	<div class="flex justify-end">
		<button
			type="button"
			class="flex min-h-11 min-w-11 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
			onclick={onClose}
			aria-label="Close settings"
		>
			<Icon icon={X} size={20} />
		</button>
	</div>

	<!-- ── Reading ──────────────────────────────────────────────────────────── -->
	<section class="flex flex-col gap-4">
		<h3 class="font-ui text-xs font-semibold tracking-wide text-foreground uppercase">Reading</h3>

		<!-- Mode — radio group; includes Focus (added by FND). -->
		<fieldset class="flex flex-col gap-2">
			<legend class="font-ui text-sm text-foreground">Mode</legend>
			<div class="flex flex-wrap gap-2">
				{#each MODES as m (m.value)}
					<label
						class="flex min-h-11 cursor-pointer items-center gap-2 rounded-md border border-border bg-card px-3 font-ui text-sm text-card-foreground has-[:checked]:bg-primary has-[:checked]:text-primary-foreground"
					>
						<input
							type="radio"
							name="panel-mode"
							class="accent-pivot"
							checked={store.current.mode === m.value}
							onchange={() => void store.set({ mode: m.value })}
						/>
						{m.label}
					</label>
				{/each}
			</div>
		</fieldset>

		<!-- Speed -->
		<div class="flex flex-col gap-1">
			<div class="flex items-baseline justify-between font-ui text-sm text-foreground">
				<span>Speed</span>
				<span class="font-mono text-xs text-muted-foreground tabular-nums">{wpm} wpm</span>
			</div>
			<Slider
				bind:value={wpm}
				min={100}
				max={800}
				step={10}
				aria-label="Reading speed in words per minute"
				onValueChange={(v) => void store.set({ wpm: v })}
			/>
		</div>

		<!-- Chunk -->
		<div class="flex flex-col gap-1">
			<div class="flex items-baseline justify-between font-ui text-sm text-foreground">
				<span>Words per flash</span>
				<span class="font-mono text-xs text-muted-foreground tabular-nums">{chunk}</span>
			</div>
			<Slider
				bind:value={chunk}
				min={1}
				max={4}
				step={1}
				aria-label="Words shown per flash"
				onValueChange={(v) => void store.set({ chunk: v })}
			/>
		</div>

		<!-- Ramp -->
		<label class="flex min-h-11 items-center justify-between font-ui text-sm text-foreground">
			<span>Ease into speed (ramp)</span>
			<input
				type="checkbox"
				class="size-5 accent-pivot"
				checked={store.current.ramp}
				onchange={(e) => void store.set({ ramp: e.currentTarget.checked })}
			/>
		</label>
	</section>

	<!-- ── Comfort ───────────────────────────────────────────────────────────── -->
	<section class="flex flex-col gap-4">
		<h3 class="font-ui text-xs font-semibold tracking-wide text-foreground uppercase">Comfort</h3>

		{@render selectField(
			'Typeface',
			store.current.font,
			FONTS,
			(v) => void store.set({ font: v as PreferencesView['font'] })
		)}

		<!-- Word size -->
		<div class="flex flex-col gap-1">
			<div class="flex items-baseline justify-between font-ui text-sm text-foreground">
				<span>Word size</span>
				<span class="font-mono text-xs text-muted-foreground tabular-nums">{sizePx}px</span>
			</div>
			<Slider
				bind:value={sizePx}
				min={24}
				max={120}
				step={2}
				aria-label="Reading word size in pixels"
				onValueChange={(v) => void store.set({ size_px: v })}
			/>
		</div>

		<!-- Letter spacing -->
		<div class="flex flex-col gap-1">
			<div class="flex items-baseline justify-between font-ui text-sm text-foreground">
				<span>Letter spacing</span>
				<span class="font-mono text-xs text-muted-foreground tabular-nums"
					>{letterSpacing.toFixed(2)}em</span
				>
			</div>
			<Slider
				bind:value={letterSpacing}
				min={0}
				max={0.2}
				step={0.01}
				aria-label="Letter spacing in em"
				onValueChange={(v) => void store.set({ letter_spacing_em: v })}
			/>
		</div>

		{@render selectField(
			'Theme',
			store.current.theme,
			THEMES,
			(v) => void store.set({ theme: v as PreferencesView['theme'] })
		)}
	</section>

	<!-- ── Context ───────────────────────────────────────────────────────────── -->
	<section class="flex flex-col gap-4">
		<h3 class="font-ui text-xs font-semibold tracking-wide text-foreground uppercase">Context</h3>

		{@render selectField(
			'Context window',
			store.current.context,
			CONTEXTS,
			(v) => void store.set({ context: v as PreferencesView['context'] })
		)}

		<!-- Context scale -->
		<div class="flex flex-col gap-1">
			<div class="flex items-baseline justify-between font-ui text-sm text-foreground">
				<span>Context size</span>
				<span class="font-mono text-xs text-muted-foreground tabular-nums"
					>{Math.round(ctxScale * 100)}%</span
				>
			</div>
			<Slider
				bind:value={ctxScale}
				min={0.4}
				max={1}
				step={0.05}
				aria-label="Relative size of context words"
				onValueChange={(v) => void store.set({ ctx_scale: v })}
			/>
		</div>
	</section>
</Sheet>
