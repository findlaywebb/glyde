<script lang="ts">
	// Mobile-first overlay (the §5.8 frozen primitive): a bottom sheet (default) or right
	// drawer for the Settings quick-panel / mode switcher. `open` is $bindable (the parent
	// owns visibility); Escape and a backdrop tap both dismiss. The entrance is a
	// compositor-only CSS animation gated by `motion-safe:` — a reduced-motion user gets the
	// instant outcome, and there is no JS-transition dependency (assay motion discipline, §5.11).
	//
	// v1 scope: `aria-modal` signals modal intent and focus moves into the panel on open, but
	// background focus is not trapped — a full focus-trap is a later enhancement.
	import type { Snippet } from 'svelte';
	import { cn } from '$lib/utils';

	interface Props {
		open: boolean;
		side?: 'bottom' | 'right';
		title: string;
		onClose?: () => void;
		children: Snippet;
	}

	let { open = $bindable(), side = 'bottom', title, onClose, children }: Props = $props();

	let panel = $state<HTMLDivElement>();

	function close() {
		open = false;
		onClose?.();
	}

	function onKeydown(event: KeyboardEvent) {
		if (open && event.key === 'Escape') {
			event.preventDefault();
			close();
		}
	}

	// Move focus into the sheet when it opens (it lands on the labelled dialog region).
	$effect(() => {
		if (open) panel?.focus();
	});

	const sideClasses = {
		bottom:
			'inset-x-0 bottom-0 max-h-[85dvh] rounded-t-2xl border-t motion-safe:animate-sheet-bottom',
		right:
			'inset-y-0 right-0 w-[min(22rem,92vw)] rounded-l-2xl border-l motion-safe:animate-sheet-right'
	};
</script>

<svelte:window onkeydown={onKeydown} />

{#if open}
	<button
		type="button"
		aria-label={`Close ${title}`}
		class="fixed inset-0 z-40 bg-overlay motion-safe:animate-overlay-in"
		onclick={close}
	></button>

	<div
		bind:this={panel}
		role="dialog"
		aria-modal="true"
		aria-label={title}
		tabindex="-1"
		class={cn(
			'fixed z-50 flex flex-col gap-4 overflow-y-auto border-border bg-card p-5 text-card-foreground shadow-2xl outline-none',
			sideClasses[side]
		)}
	>
		<h2 class="font-ui text-lg font-semibold">{title}</h2>
		{@render children()}
	</div>
{/if}
