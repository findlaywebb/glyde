<script lang="ts">
	// The Settings page — PREF owns. Grouped reading-preference controls bound to the frozen
	// `createPrefsStore` (§5.10), with a live preview word that reflects the current font, size,
	// spacing, pivot colour and theme. Every change is write-through: a control commit calls
	// `store.set(patch)`, which mirrors the full object to localStorage and PUTs it (full-replace),
	// so the last-used choice — `mode` included — is restored on the next open.
	//
	// SSR is off for this route (`+page.ts`): the first paint comes from the localStorage mirror,
	// then `store.reload()` reconciles from the server (source of truth) once mounted.
	import { browser } from '$app/environment';
	import Slider from '$lib/components/ui/Slider.svelte';
	import { createPrefsStore, type PreferencesView } from '$lib/domains/preferences/prefs.svelte';

	const store = createPrefsStore();

	// Client-only reconcile from the server. `reload()` reads no reactive state in a tracked way
	// (§5.10), so this effect runs once on mount, not on every `store.current` change.
	$effect(() => {
		if (browser) void store.reload();
	});

	// Live editing buffers for the range controls: bound to the sliders so the preview word and the
	// numeric readouts track the drag in real time. The committed value is persisted on release
	// (onValueChange → store.set). The sync effect below re-seeds them whenever the store changes
	// externally (the mount reconcile); it stays dormant mid-drag because `store.current` only moves
	// on a commit, so it never yanks a slider out from under an in-progress drag.
	let wpm = $state(store.current.wpm);
	let chunk = $state(store.current.chunk);
	let sizePx = $state(store.current.size_px);
	let letterSpacing = $state(store.current.letter_spacing_em);
	let ctxScale = $state(store.current.ctx_scale);

	$effect(() => {
		const p = store.current;
		wpm = p.wpm;
		chunk = p.chunk;
		sizePx = p.size_px;
		letterSpacing = p.letter_spacing_em;
		ctxScale = p.ctx_scale;
	});

	// Typed option lists. `satisfies` keeps each `value` a literal, so the radio handler typechecks
	// with no cast; the select handler casts the DOM string once (the `<select>` value is `string`).
	const MODES = [
		{ value: 'guided', label: 'Guided sweep' },
		{ value: 'rsvp', label: 'RSVP' },
		{ value: 'fading', label: 'Fading trail' }
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

	// The preview's font family. The three token-backed faces reference the X1-owned CSS variables
	// (so the preview can never drift from the rest of the app); the other three have no shell token
	// yet, so a literal stack stands in.
	const FONT_FAMILY: Record<PreferencesView['font'], string> = {
		atkinson: 'var(--font-reading)',
		lexend: 'var(--font-ui)',
		opendyslexic: "'OpenDyslexic', 'Comic Sans MS', system-ui, sans-serif",
		system: 'system-ui, sans-serif',
		serif: "Georgia, 'Times New Roman', serif",
		mono: 'var(--font-mono)'
	};

	const previewStyle = $derived(
		`font-family: ${FONT_FAMILY[store.current.font]}; ` +
			`font-size: ${sizePx}px; ` +
			`letter-spacing: ${letterSpacing}em;`
	);
</script>

<svelte:head><title>Settings · Glyde</title></svelte:head>

<!-- One enum control: a labelled native <select> (keyboard + a11y for free). One-way `selected`
	reflects the stored value; `onpick` persists the new DOM value. -->
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

<div class="mx-auto flex max-w-md flex-col gap-8 p-4">
	<header class="flex flex-col gap-1">
		<h1 class="font-ui text-xl font-bold text-foreground">Reading settings</h1>
		<p class="font-ui text-sm text-muted-foreground">
			Tune the reader to your eyes. Changes save instantly and sync across your devices.
		</p>
	</header>

	<!-- Live preview: the streamed word at the current face, sized and spaced, with the coral
		pivot, shown inside the chosen theme scope so colours reflect the selection. -->
	<section class="{store.current.theme} flex flex-col gap-2" aria-label="Live preview">
		<span class="font-ui text-xs font-semibold text-muted-foreground uppercase">Preview</span>
		<div
			class="flex min-h-32 items-center justify-center rounded-2xl border border-border bg-reading px-4 py-6"
		>
			<span class="font-reading text-reading-foreground" style={previewStyle}>
				Re<span class="text-pivot">a</span>ding
			</span>
		</div>
	</section>

	<!-- Reading: mode / speed / chunk / ramp -->
	<section class="flex flex-col gap-4">
		<h2 class="font-ui text-sm font-semibold tracking-wide text-foreground uppercase">Reading</h2>

		<fieldset class="flex flex-col gap-2">
			<legend class="font-ui text-sm text-foreground">Mode</legend>
			<div class="flex flex-wrap gap-2">
				{#each MODES as m (m.value)}
					<label
						class="flex min-h-11 cursor-pointer items-center gap-2 rounded-md border border-border bg-card px-3 font-ui text-sm text-card-foreground has-[:checked]:bg-primary has-[:checked]:text-primary-foreground"
					>
						<input
							type="radio"
							name="mode"
							class="accent-pivot"
							checked={store.current.mode === m.value}
							onchange={() => store.set({ mode: m.value })}
						/>
						{m.label}
					</label>
				{/each}
			</div>
		</fieldset>

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
				onValueChange={(v) => store.set({ wpm: v })}
			/>
		</div>

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
				onValueChange={(v) => store.set({ chunk: v })}
			/>
		</div>

		<label class="flex min-h-11 items-center justify-between font-ui text-sm text-foreground">
			<span>Ease into speed (ramp)</span>
			<input
				type="checkbox"
				class="size-5 accent-pivot"
				checked={store.current.ramp}
				onchange={(e) => store.set({ ramp: e.currentTarget.checked })}
			/>
		</label>
	</section>

	<!-- Comfort: font / size / spacing / theme -->
	<section class="flex flex-col gap-4">
		<h2 class="font-ui text-sm font-semibold tracking-wide text-foreground uppercase">Comfort</h2>

		{@render selectField('Typeface', store.current.font, FONTS, (v) =>
			store.set({ font: v as PreferencesView['font'] })
		)}

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
				onValueChange={(v) => store.set({ size_px: v })}
			/>
		</div>

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
				onValueChange={(v) => store.set({ letter_spacing_em: v })}
			/>
		</div>

		{@render selectField('Theme', store.current.theme, THEMES, (v) =>
			store.set({ theme: v as PreferencesView['theme'] })
		)}
	</section>

	<!-- Context: treatment / size -->
	<section class="flex flex-col gap-4">
		<h2 class="font-ui text-sm font-semibold tracking-wide text-foreground uppercase">Context</h2>

		{@render selectField('Context window', store.current.context, CONTEXTS, (v) =>
			store.set({ context: v as PreferencesView['context'] })
		)}

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
				onValueChange={(v) => store.set({ ctx_scale: v })}
			/>
		</div>
	</section>
</div>
