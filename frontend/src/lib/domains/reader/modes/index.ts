/**
 * The reading-mode views' public surface — R-MODES owns this file.
 *
 * R-STAGE imports these two components and mounts one per `ReaderState.mode`: `Rsvp` for the
 * single-word RSVP view, `Flow` for both Guided sweep and Fading trail (it branches on `mode`).
 * Both take `ModeProps` (the frozen reader prop contract) and compute no pacing of their own.
 */
export { default as Rsvp } from './Rsvp.svelte';
export { default as Flow } from './Flow.svelte';
