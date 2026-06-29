import type { KnipConfig } from 'knip';

// Dead-code sweep. Run warn-level / non-fatal (`knip --no-exit-code`) — informational,
// like the backend's vulture sweep, not a commit gate. Add `playwright`/`storybook` entry
// blocks here if those toolchains are reintroduced (their runners are invisible to knip's
// static graph, so their config + entry files must be named explicitly).
const config: KnipConfig = {};

export default config;
