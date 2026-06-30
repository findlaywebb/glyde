<script lang="ts">
	// Thin wrapper over a '@lucide/svelte' icon (the §5.8 frozen primitive). Consumers import
	// the glyph from '@lucide/svelte' and pass it: <Icon icon={Play} aria-label="Play" />.
	// Colour comes from a text-* token on `class` (lucide strokes `currentColor`).
	//
	// Accessibility: pass `aria-label` for a standalone/interactive icon — it renders as a
	// labelled image (`role="img"`). Omit it and the icon is decorative — lucide marks it
	// `aria-hidden` so screen readers skip it (correct when an adjacent <button>/text already
	// carries the label).
	import type { Component } from 'svelte';
	import { cn } from '$lib/utils';

	interface Props {
		icon: Component;
		size?: number;
		class?: string;
		'aria-label'?: string;
	}

	let { icon: Glyph, size = 20, class: className, 'aria-label': ariaLabel }: Props = $props();

	// Conditionally spread the a11y attributes so a decorative icon carries NO `aria-*` key
	// (lucide only auto-hides when no a11y prop is present; an empty `aria-label` would
	// defeat that and leave an unlabelled, non-hidden image).
	const a11y = $derived(
		ariaLabel ? { role: 'img', 'aria-label': ariaLabel } : { 'aria-hidden': 'true' as const }
	);
</script>

<Glyph {size} class={cn(className)} {...a11y} />
