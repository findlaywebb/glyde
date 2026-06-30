/**
 * The reading-mode views' public surface — R-MODES owns this file.
 *
 * R-STAGE imports these components and mounts one per `ReaderState.mode`: `Rsvp` for the single-word
 * RSVP view and `Flow` for both Guided sweep and Fading trail (it branches on `mode`). `Focus` is the
 * clause-granularity view for the `focus` mode; it is exported and ready, but the stage does not route
 * the `focus` mode to it yet (no consumer wires it — that is the integrator's change, not R-MODES').
 * Each takes `ModeProps` (the frozen reader prop contract) and computes no pacing of its own. The
 * shared internals (`Word` emphasis renderer, `clause` derivation, `measure` pivot maths) are
 * intentionally NOT re-exported — they are R-MODES-private.
 */
export { default as Rsvp } from './Rsvp.svelte';
export { default as Flow } from './Flow.svelte';
export { default as Focus } from './Focus.svelte';
