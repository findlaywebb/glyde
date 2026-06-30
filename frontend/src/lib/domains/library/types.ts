/**
 * Primitive prop types for the library domain.
 *
 * Components receive flattened primitive props rather than the wire `DigestListItemView`
 * so presentational components stay blind to the Digest IR shape. The page `load` flattens
 * each `DigestListItemView` into a `DigestCardProps` before passing it down, insulating the
 * card from future wire changes.
 */

/** Primitive props for a single digest card in the library feed. */
export interface DigestCardProps {
	/** Memorable two-word slug; the deep-link key for /d/{slug}. */
	slug: string;
	/** Agent-given semantic title, shown as the card heading. */
	name: string;
	/** The kind of source the digest came from (e.g. "cli", "agent"). */
	sourceKind: string;
	/** The producing agent/model label, if available; null otherwise. */
	producer: string | null;
	/** ISO-8601 UTC creation timestamp. */
	createdAt: string;
	/** Total word tokens across the digest's prose. */
	wordCount: number;
	/** Reading-time estimate in ms at the baseline wpm. */
	estReadingMs: number;
	/** Count of blocks keyed by block kind (e.g. { code: 2, table: 1 }). */
	blocksByKind: Record<string, number>;
}
