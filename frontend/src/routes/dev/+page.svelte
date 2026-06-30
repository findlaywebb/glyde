<script lang="ts">
	// X1's owned, unlinked harness route: a token + primitive gallery rendered three times,
	// each wrapped in a .dark / .light / .sepia scope, so the frozen §5.8 shell contract can be
	// eyeballed (PATH B) and DOM-asserted (PATH A, §5.9) in isolation — no backend, no other
	// unit's route. It exists to verify the shell, not to ship to users.
	import { Pause, Play, RotateCcw, SkipForward } from '@lucide/svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Icon from '$lib/components/ui/Icon.svelte';
	import Sheet from '$lib/components/ui/Sheet.svelte';
	import Slider from '$lib/components/ui/Slider.svelte';

	let speed = $state(350);
	let sheetOpen = $state(false);

	const themes = ['dark', 'light', 'sepia'] as const;

	const surfaceSwatches = [
		['background', 'bg-background'],
		['card', 'bg-card'],
		['primary', 'bg-primary'],
		['secondary', 'bg-secondary'],
		['muted', 'bg-muted'],
		['accent', 'bg-accent'],
		['destructive', 'bg-destructive'],
		['reading', 'bg-reading'],
		['pivot', 'bg-pivot'],
		['cue', 'bg-cue']
	] as const;
</script>

{#snippet swatch(label: string, boxClass: string)}
	<div class="flex flex-col gap-1">
		<div class="h-10 rounded-md border border-border {boxClass}"></div>
		<span class="font-mono text-[11px] text-muted-foreground">{label}</span>
	</div>
{/snippet}

{#snippet gallery(theme: string)}
	<section
		class="flex flex-col gap-6 rounded-2xl border border-border bg-background p-5 text-foreground"
	>
		<h2 class="font-ui text-base font-semibold capitalize">{theme}</h2>

		<!-- reading line: the coral ORP pivot on the Atkinson reading face -->
		<p class="font-reading text-3xl text-reading-foreground">
			re<span class="text-pivot">a</span>ding
			<span class="text-reading-dim text-base">· dimmed context</span>
		</p>

		<!-- faces -->
		<div class="flex flex-col gap-1 text-sm">
			<span class="font-reading text-reading-foreground">Atkinson Hyperlegible — font-reading</span>
			<span class="font-ui text-foreground">Lexend — font-ui</span>
			<span class="font-mono text-muted-foreground">two-word-slug — font-mono</span>
		</div>

		<!-- colour tokens -->
		<div class="grid grid-cols-5 gap-3">
			{#each surfaceSwatches as [label, boxClass] (label)}
				{@render swatch(label, boxClass)}
			{/each}
		</div>

		<!-- buttons -->
		<div class="flex flex-wrap items-center gap-3">
			<Button variant="primary">Primary</Button>
			<Button variant="secondary">Secondary</Button>
			<Button variant="destructive">Destructive</Button>
			<Button variant="ghost">Ghost</Button>
			<Button variant="primary"><Icon icon={Play} />Play</Button>
		</div>

		<!-- icons + the block-ahead cue chip -->
		<div class="flex flex-wrap items-center gap-4">
			<Icon icon={Play} aria-label="Play" class="text-pivot" />
			<Icon icon={Pause} aria-label="Pause" class="text-foreground" />
			<Icon icon={RotateCcw} aria-label="Replay word" class="text-muted-foreground" />
			<Icon icon={SkipForward} aria-label="Step forward" class="text-muted-foreground" />
			<span class="rounded-full bg-cue/15 px-3 py-1 font-ui text-xs font-semibold text-cue">
				code ahead
			</span>
		</div>

		<!-- slider -->
		<Slider bind:value={speed} min={100} max={900} step={25} aria-label="Reading speed ({theme})" />
		<span class="font-mono text-xs text-muted-foreground">{speed} wpm</span>

		<!-- sheet trigger -->
		<Button variant="secondary" onclick={() => (sheetOpen = true)}>Open sheet</Button>
	</section>
{/snippet}

<div class="mx-auto flex max-w-md flex-col gap-6 p-4">
	<header class="flex flex-col gap-1">
		<h1 class="font-ui text-xl font-bold text-foreground">
			Glyde shell — token &amp; primitive gallery
		</h1>
		<p class="font-ui text-sm text-muted-foreground">
			The §5.8 frozen contract in all three theme scopes.
		</p>
	</header>

	{#each themes as theme (theme)}
		<div class={theme}>
			{@render gallery(theme)}
		</div>
	{/each}
</div>

<Sheet bind:open={sheetOpen} title="Settings preview" side="bottom">
	<p class="font-ui text-sm text-muted-foreground">
		A bottom Sheet — Escape or a backdrop tap dismisses it. Motion is gated on
		prefers-reduced-motion.
	</p>
	<Slider bind:value={speed} min={100} max={900} step={25} aria-label="Reading speed (sheet)" />
	<Button variant="primary" onclick={() => (sheetOpen = false)}>Done</Button>
</Sheet>
