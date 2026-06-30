/**
 * Formatting utilities for the library domain.
 *
 * Pure functions that transform digest primitive fields into human-readable strings for
 * the library feed. No side effects, no DOM access; safe to call in both server and browser
 * environments. Every function takes only primitive values so it is straightforwardly testable.
 */

/**
 * Format a reading-time estimate in milliseconds to a short human string.
 *
 * @param ms Reading-time estimate in milliseconds.
 * @returns A string like "~1m 30s", "~2m", or "~45s".
 */
export function formatReadingTime(ms: number): string {
	const totalSec = Math.round(ms / 1000);
	const min = Math.floor(totalSec / 60);
	const sec = totalSec % 60;
	if (min === 0) return `~${sec}s`;
	if (sec === 0) return `~${min}m`;
	return `~${min}m ${sec}s`;
}

/**
 * Format a block-kind count map into a shape badge string.
 *
 * @param blocksByKind Map of block kind to count (e.g. \{ code: 3, table: 1 \}).
 * @returns A readable string like "3 code · 1 table", or an empty string when there are no blocks.
 */
export function formatBlockMix(blocksByKind: Record<string, number>): string {
	const parts = Object.entries(blocksByKind)
		.filter(([, count]) => count > 0)
		.map(([kind, count]) => `${count} ${kind}`);
	return parts.join(' · ');
}

/**
 * Format a provenance summary from its constituent parts.
 *
 * Uses the 'en-GB' locale for deterministic output across server and browser environments
 * (locale-dependent rendering would cause SSR/hydration mismatches on non-English systems).
 *
 * @param sourceKind The kind of source (e.g. "cli", "agent").
 * @param producer The producing agent/model label, if any; null otherwise.
 * @param createdAt ISO-8601 UTC creation timestamp.
 * @returns A concise string like "agent · claude-3 · 15 Jan 2024", or "—" for an unparseable date.
 */
export function formatProvenance(
	sourceKind: string,
	producer: string | null,
	createdAt: string
): string {
	const parsed = new Date(createdAt);
	const date = isNaN(parsed.getTime())
		? '—'
		: parsed.toLocaleDateString('en-GB', {
				year: 'numeric',
				month: 'short',
				day: 'numeric'
			});
	const parts: string[] = [sourceKind];
	if (producer) parts.push(producer);
	parts.push(date);
	return parts.join(' · ');
}
