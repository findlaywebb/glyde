/**
 * The block card family — R-BLOCKS owns this directory.
 *
 * Exports the six pause-and-show cards (one per block kind) and the BlockAheadCue chip.
 * All cards are pure presentational components over the frozen `BlockCardProps` from R-CORE
 * (`lib/domains/reader/types`). R-STAGE imports these and maps `block.kind` to the right card.
 *
 * What this module does NOT do: it contains no engine logic, no pacing math, and no global
 * listeners — those live in R-CORE's engine and R-STAGE respectively.
 */
export { default as BlockAheadCue } from './BlockAheadCue.svelte';
export { default as CodeCard } from './CodeCard.svelte';
export { default as ImageCard } from './ImageCard.svelte';
export { default as MathCard } from './MathCard.svelte';
export { default as NoteCard } from './NoteCard.svelte';
export { default as QuoteCard } from './QuoteCard.svelte';
export { default as TableCard } from './TableCard.svelte';
