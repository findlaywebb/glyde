/**
 * The reader domain's public surface — R-CORE owns this file.
 *
 * Consuming units (R-MODES, R-BLOCKS, R-CHROME, R-STAGE) import the engine factory and the prop
 * contract from here. The pure `cadence.ts` is intentionally NOT re-exported: pacing is the
 * engine's alone, so no presentational unit can reach in and recompute it.
 */
export { createReaderEngine } from './engine.svelte';
export type {
	BlockAheadCueProps,
	BlockCardProps,
	BlockView,
	CreateReaderEngineArgs,
	Mode,
	ModeProps,
	PauseView,
	PreferencesView,
	ProgressProps,
	ProseSegmentView,
	ReaderClock,
	ReaderEngine,
	ReaderState,
	SegmentView,
	TokenView,
	TransportProps
} from './types';
