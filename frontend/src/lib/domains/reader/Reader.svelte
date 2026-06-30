<script lang="ts">
	/**
	 * The composing reader stage — R-STAGE owns this file.
	 *
	 * Wires the frozen reader pieces into one working reader: it constructs the R-CORE engine
	 * (`createReaderEngine`) over the digest's segments, routes the active mode view (R-MODES
	 * `Rsvp` for `rsvp`, `Focus` for `focus`, `Flow` for `guided`/`fading`), the R-BLOCKS
	 * pause-and-show card for the active block segment, the block-ahead cue, the R-CHROME
	 * `Transport` + `Progress`, and the slide-out `SettingsPanel` — passing each its frozen prop
	 * contract (§5.7) computed from engine state. Preferences flow in through PREF's
	 * `createPrefsStore` (§5.10), injected as a prop so the persist round-trip is testable.
	 *
	 * The reader carries TWO intentional mode switchers — the always-visible header quick toggle and
	 * the SettingsPanel's full mode control — both writing through the one shared `store`, so they
	 * stay consistent. A SettingsPanel edit (`store.set`) re-paces through the existing
	 * `effectivePrefs` $derived → `setPrefs` $effect and updates the reading CSS vars live, with no
	 * reload and no pacing recomputed in the panel; R-STAGE owns only the panel's `open` boolean.
	 *
	 * R-STAGE is the SOLE owner of the reader's global input (§5.7): one `$effect` binds the single
	 * `window` keydown (via the pure `keyToIntent` map) and the single stage swipe (via `bindSwipe`);
	 * no mode, block, or chrome unit registers a global listener. It also owns the single
	 * coordinated `aria-live` announcer, focus-scoped key dispatch (shortcuts fire only while the
	 * stage holds focus, never while typing), and roving focus that keeps the stage focused on
	 * advance. It owns the REAL wpm clamp (`clampWpm`) — Transport only display-clamps (§5.7).
	 *
	 * What it does NOT do: it amends none of the frozen contracts it imports (R-CORE engine/types,
	 * R-MODES, R-BLOCKS, R-CHROME, PREF), recomputes no pacing (the engine is the sole owner), and
	 * fetches nothing (the route's `load` reads the digest through the typed seam). The default
	 * reading mode is Guided on first run; the last-used mode persists through PREF and is restored
	 * on the next open (the store reads its localStorage mirror synchronously at construction).
	 */
	import type { Component } from 'svelte';
	import { untrack } from 'svelte';
	import { Settings } from '@lucide/svelte';
	import { resolve } from '$app/paths';
	import Icon from '$lib/components/ui/Icon.svelte';
	import type { PrefsStore } from '$lib/domains/preferences/prefs.svelte';
	import { createReaderEngine } from './index';
	import type { BlockCardProps, BlockView, Mode, ReaderClock, SegmentView } from './index';
	import { Flow, Focus, Rsvp } from './modes';
	import {
		BlockAheadCue,
		CodeCard,
		ImageCard,
		MathCard,
		NoteCard,
		QuoteCard,
		TableCard
	} from './blocks';
	import Progress from './Progress.svelte';
	import Transport from './Transport.svelte';
	import SettingsPanel from './SettingsPanel.svelte';
	import { bindSwipe, clampWpm, keyToIntent, type ReaderIntent } from './input';

	interface ReaderProps {
		/** The digest's reading-timeline segments (prose, pauses, blocks). */
		segments: SegmentView[];
		/** PREF's reactive preferences store (§5.10) — injected so the round-trip is testable. */
		store: PrefsStore;
		/** The digest's display title, shown in the reader header. */
		title?: string;
		/** Injected clock for the engine; defaults to the real rAF clock (overridden in tests). */
		clock?: ReaderClock;
	}

	let { segments, store, title, clock }: ReaderProps = $props();

	// The header quick-toggle of the reading modes, canonical labels (docs/glossary.md), in switch
	// order. INTENTIONAL DUPLICATION: this is one of two mode switchers. The slide-out SettingsPanel
	// below carries the full mode control too. Both write through the SAME shared `store` (via
	// `store.set`), so they never disagree — keep BOTH (the header is the always-visible quick
	// toggle; the panel the full settings surface). Do not deduplicate them.
	const MODES: { value: Mode; label: string }[] = [
		{ value: 'guided', label: 'Guided sweep' },
		{ value: 'rsvp', label: 'RSVP' },
		{ value: 'fading', label: 'Fading trail' },
		{ value: 'focus', label: 'Focus' }
	];

	/** Map each block kind to its R-BLOCKS card; R-STAGE mounts the right one per `block.kind`. */
	const blockCards: Record<BlockView['kind'], Component<BlockCardProps>> = {
		code: CodeCard,
		table: TableCard,
		image: ImageCard,
		math: MathCard,
		quote: QuoteCard,
		note: NoteCard
	};

	// Clamped, reactive view of the reading preferences. R-STAGE owns the real wpm clamp (§5.7);
	// every consumer below (engine pacing + the Transport speed it displays) reads the already-
	// clamped speed from here, so an out-of-range stored value never reaches pacing.
	const effectivePrefs = $derived({ ...store.current, wpm: clampWpm(store.current.wpm) });

	// The headless engine — the sole owner of position, pivot, dwell and the block state machine.
	// Constructed ONCE over this digest (the route remounts via {#key slug} on navigation), so the
	// reads are deliberately one-time-captured under `untrack`; preferences are pushed in afterwards
	// imperatively via the setPrefs `$effect` below.
	const engine = untrack(() => createReaderEngine({ segments, prefs: effectivePrefs, clock }));

	let stageEl = $state<HTMLElement | null>(null);
	// The slide-out SettingsPanel's open state — R-STAGE owns it (the panel takes `open` as a plain
	// boolean, NOT $bindable) and flips it false via the panel's onClose. The panel writes through
	// the SAME shared `store`, so a change re-paces through the existing effectivePrefs $derived →
	// setPrefs $effect path and updates the CSS vars instantly — no reload, no pacing recomputed here.
	let settingsOpen = $state(false);
	// True only while the current block card was surfaced by the ArrowLeft re-show (the subtle
	// "again" affordance, §5.7) — not while playback auto-paused on a freshly reached block.
	let reshown = $state(false);

	const activeBlock = $derived(engine.activeBlock);

	// The ordered block segments, aligned 1:1 with engine.blockNotches, so the block-ahead cue can
	// label the upcoming block's kind (the engine exposes the cue window as a boolean, not a kind).
	// One-time capture (segments is static per mount) under `untrack`.
	const blockSegments = untrack(() => segments.filter((s): s is BlockView => s.type === 'block'));

	const cueKind = $derived.by((): BlockView['kind'] | null => {
		if (!engine.blockAhead) return null;
		const wi = engine.wordIndex;
		const notches = engine.blockNotches;
		for (let i = 0; i < notches.length; i++) {
			const notch = notches[i];
			// Strictly ahead: a block's notch is the ordinal of the FIRST word after it, so `notch
			// === wi` means that block is already behind us (we are on its first trailing word).
			if (notch !== undefined && notch > wi) return blockSegments[i]?.kind ?? null;
		}
		return null;
	});

	// The single coordinated screen-reader announcement (§5.7): a $derived of only the coarse
	// transport state — never wordIndex — so it speaks play/pause, the shown block, speed and the
	// end, but does NOT fire on every word advance (which would flood a screen reader).
	const announcement = $derived.by((): string => {
		const block = engine.activeBlock;
		if (block) {
			const lead = block.lead ? `${block.lead} ` : '';
			return `${block.kind} block shown. ${lead}Press space to continue.`;
		}
		if (engine.atEnd) return 'End of digest.';
		if (engine.isPlaying) return `Playing at ${effectivePrefs.wpm} words per minute.`;
		return 'Paused.';
	});

	// Bridge the reactive prefs into the imperative engine: push the clamped prefs through the
	// engine's setPrefs API whenever they change (user edits here, or a server reconcile in the
	// route). Reads only effectivePrefs, never engine state, so there is no update cycle — the
	// escape-hatch use of $effect (driving a state machine), not naive state mirroring.
	$effect(() => {
		engine.setPrefs(effectivePrefs);
	});

	/** Whether `el` is (or sits within) an interactive control that should own its own keys. */
	function isInteractive(el: Element | null): boolean {
		return (
			el?.closest(
				'button, a, input, select, textarea, [role="button"], [contenteditable="true"]'
			) != null
		);
	}

	// Focus-scoped key dispatch (§5.7 / assay §11): shortcuts fire only while the stage region (or
	// nothing) holds focus, never while a control or editable element is focused — so Space on the
	// Transport play button is not double-handled, and arrows neither scroll nor type.
	function shouldHandleKeys(): boolean {
		const active = document.activeElement;
		if (active === null || active === document.body) return true;
		if (active === stageEl) return true;
		if (stageEl?.contains(active)) return !isInteractive(active);
		return false;
	}

	/** Apply a keyboard/tap intent to the engine, tracking the re-show affordance. */
	function run(intent: ReaderIntent): void {
		switch (intent) {
			case 'toggle':
				reshown = false;
				engine.toggle();
				break;
			case 'stepForward':
				reshown = false;
				engine.stepForward();
				break;
			case 'reshowLastBlock': {
				// The "again" affordance is only honest when the engine actually re-shows a block.
				// It no-ops when we are already auto-paused on that block (a fresh auto-pause, not a
				// re-show), so derive `reshown` from the resulting state rather than assuming it fired:
				// keep a live re-show flagged, never flag a plain auto-pause.
				const wasAutoPausedOnBlock = engine.activeBlock !== null && !reshown;
				engine.reshowLastBlock();
				if (!wasAutoPausedOnBlock) reshown = engine.activeBlock !== null;
				break;
			}
		}
	}

	/** Step back one word (Transport replay / swipe-back); never a re-show. */
	function replayWord(): void {
		reshown = false;
		engine.replayWord();
	}

	// THE single global keyboard + stage-gesture owner (§5.7): one $effect binds the window keydown
	// and the stage swipe, and detaches both on teardown. No other unit registers a global listener.
	$effect(() => {
		const el = stageEl;
		if (!el) return;
		function onKeydown(event: KeyboardEvent): void {
			if (!shouldHandleKeys()) return;
			const intent = keyToIntent(event.key);
			if (intent === null) return;
			event.preventDefault();
			run(intent);
		}
		window.addEventListener('keydown', onKeydown);
		const teardownSwipe = bindSwipe(el, {
			onTap: () => run('toggle'),
			onNext: () => run('stepForward'),
			onPrev: replayWord,
			isIgnored: (t) => isInteractive(t as Element | null)
		});
		return () => {
			window.removeEventListener('keydown', onKeydown);
			teardownSwipe();
		};
	});

	// Roving focus (§5.7 / assay §11): on each position/block advance, return keyboard focus to the
	// stable stage region if it has dropped to <body>, so a keyboard reader never falls off. Never
	// steals focus from the Transport/Progress chrome (it acts only when focus is on <body>).
	$effect(() => {
		void engine.wordIndex;
		void engine.activeBlock;
		if (stageEl && document.activeElement === document.body) stageEl.focus();
	});

	// Clear the engine's timers when the reader unmounts.
	$effect(() => () => engine.destroy());

	/** Switch reading mode: update the engine instantly, then persist the last-used mode (§5.10). */
	function selectMode(mode: Mode): void {
		reshown = false;
		engine.setMode(mode);
		void store.set({ mode });
	}

	/** Transport speed-rail commit: persist the clamped wpm; the sync $effect re-paces the engine. */
	function onSpeed(wpm: number): void {
		void store.set({ wpm: clampWpm(wpm) });
	}

	/** Progress tap-to-scrub to a word ordinal. */
	function onScrub(wordIndex: number): void {
		reshown = false;
		engine.scrubTo(wordIndex);
	}
</script>

<div
	class="reader {effectivePrefs.theme} flex h-dvh flex-col bg-reading pb-32"
	style:--reading-size="{effectivePrefs.size_px}px"
	style:--reading-letter-spacing="{effectivePrefs.letter_spacing_em}em"
	style:--reading-size-flow="{Math.round(effectivePrefs.size_px * 0.5)}px"
>
	<header class="flex items-center gap-3 border-b border-border/60 px-4 py-2 font-ui">
		<a
			href={resolve('/')}
			class="shrink-0 rounded-md px-2 py-1 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
			aria-label="Back to library">← Library</a
		>
		{#if title}
			<h1 class="min-w-0 flex-1 truncate text-sm font-semibold text-foreground">{title}</h1>
		{:else}
			<span class="flex-1"></span>
		{/if}
		<div role="group" aria-label="Reading mode" class="flex shrink-0 gap-1">
			{#each MODES as m (m.value)}
				<button
					type="button"
					class="rounded-md px-2.5 py-1 text-xs font-medium transition focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none aria-pressed:bg-primary aria-pressed:text-primary-foreground text-muted-foreground hover:bg-accent"
					aria-pressed={engine.mode === m.value}
					onclick={() => selectMode(m.value)}>{m.label}</button
				>
			{/each}
		</div>
		<!-- Gear: opens the slide-out SettingsPanel (the full settings surface). min-h/w-11 ≥44px. -->
		<button
			type="button"
			class="flex min-h-11 min-w-11 shrink-0 items-center justify-center rounded-md text-muted-foreground transition hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
			onclick={() => (settingsOpen = true)}
			aria-label="Reading settings"
		>
			<Icon icon={Settings} size={20} />
		</button>
	</header>

	<!--
		The reading stage — R-STAGE's single focus + gesture surface. role="application" is the
		container role §5.7 offers for the reading surface: it tells assistive tech to pass keystrokes
		through (the window shortcuts) AND it legitimately wraps the interactive block cards (a code
		card's wrap toggle is a real <button>) — role="button" would nest a button inside a button.
		tabindex="-1" keeps it programmatically focusable (roving focus / tap-to-focus) without putting
		a non-activatable surface in the Tab order; every gesture has a visible control equivalent
		(Transport/Progress/header), so keyboard users are never locked out (WCAG 2.5.1). The swipe
		listener is attached imperatively via bindSwipe in the $effect above (not a markup handler) and
		the shortcuts are the focus-scoped window listener — so this surface raises no a11y warning.
	-->
	<div
		bind:this={stageEl}
		class="relative flex flex-1 items-center justify-center overflow-hidden px-4"
		role="application"
		tabindex="-1"
		aria-roledescription="speed reader"
		aria-label="Reading stage — tap or press space to play or pause"
	>
		<div class="pointer-events-none absolute top-4 left-1/2 z-10 -translate-x-1/2">
			<BlockAheadCue kind={cueKind ?? 'note'} visible={cueKind !== null} />
		</div>

		{#if activeBlock}
			{@const Card = blockCards[activeBlock.kind]}
			<div class="flex max-h-full w-full max-w-2xl items-center justify-center overflow-auto">
				<Card block={activeBlock} {reshown} />
			</div>
		{:else if engine.mode === 'rsvp'}
			<Rsvp mode={engine.mode} state={engine} words={engine.words} />
		{:else if engine.mode === 'focus'}
			<Focus mode={engine.mode} state={engine} words={engine.words} />
		{:else}
			<Flow mode={engine.mode} state={engine} words={engine.words} />
		{/if}
	</div>

	<div class="px-4 pt-2">
		<Progress
			wordIndex={engine.wordIndex}
			wordCount={engine.wordCount}
			remainingMs={engine.remainingMs}
			blockNotches={engine.blockNotches}
			{onScrub}
		/>
	</div>
</div>

<Transport
	isPlaying={engine.isPlaying}
	wpm={effectivePrefs.wpm}
	onToggle={() => run('toggle')}
	onReplayWord={replayWord}
	onStepForward={() => run('stepForward')}
	{onSpeed}
/>

<!--
	The slide-out settings panel (U2), mounted with FND's frozen SettingsPanelProps. It receives the
	SAME shared `store` the engine reads from (never a new instance), so each control's `store.set`
	flows back through this component's `effectivePrefs` $derived → setPrefs $effect (re-pacing) and
	the size/spacing/font/theme CSS vars — live, no reload. `open` is owned here; `onClose` flips it.
-->
<SettingsPanel {store} open={settingsOpen} onClose={() => (settingsOpen = false)} />

<!-- The single coordinated screen-reader announcer (§5.7): play/pause, block shown, speed, end. -->
<div class="sr-only" aria-live="polite" aria-atomic="true" data-testid="reader-announcer">
	{announcement}
</div>
