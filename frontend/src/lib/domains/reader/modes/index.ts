/**
 * The reading-mode views' public surface — R-MODES owns this file.
 *
 * R-STAGE imports these components and mounts one per `ReaderState.mode`: `Rsvp` for the single-word
 * RSVP view, `Focus` for the clause-granularity focus view, and `Flow` for both Guided sweep and
 * Fading trail (it branches on `mode`). Each takes `ModeProps` (the frozen reader prop contract) and
 * computes no pacing of its own. The shared internals (`Word` emphasis renderer, `clause` derivation,
 * `measure` pivot maths) are intentionally NOT re-exported — they are R-MODES-private.
 */
export { default as Rsvp } from './Rsvp.svelte';
export { default as Flow } from './Flow.svelte';
export { default as Focus } from './Focus.svelte';
