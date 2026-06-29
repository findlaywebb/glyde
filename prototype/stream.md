Research synthesis: context display and technical content in the RSVP reader.

Three agents are back so far. Code, science, and technical. The products agent is still running, but the findings already converge, so here is the picture.

First, how to show context words. The engineering research found that modern readers put context on separate rows above and below the focal word, dimmed to about a third of the size and very low opacity, decoupled from the pivot row. They also use a CSS grid for the x-lock. This directly fixes the not-quite-there feeling.

The science agent reached the same conclusion from a different direction. Words placed too close together cause visual crowding, and dyslexic readers need roughly one and a half times more separation than other readers. Crowding is the single biggest failure mode. Putting context above and below sidesteps the horizontal crowding that hurts most. The verdict is one word each side, dimmed, never more.

So context above and below is the rare answer that is both cleaner engineering and the safer choice for dyslexia.

Two science caveats are worth acting on. First, OpenDyslexic has no proven benefit and is sometimes slower. A plain sans like our Atkinson default is as good or better, so we keep OpenDyslexic as an option but do not push it. Second, the biggest proven win for comprehension is not RSVP at all. It is guided reading and text fading, which cut reading errors by about seventy percent in one study. That is a possible future mode, out of scope for now.

Now the technical content question, the code, tables, and diagrams. The evidence here is decisive. Code is read non-linearly. Eye tracking shows programmers jump around following execution order, and experts do this even more than novices. Streaming code one word at a time destroys the structure. The only sane approach is to detect a block, pause the stream, and render it statically.

By type, the plan is this. Code pauses and shows in monospace with highlighting. A table pauses and shows the grid. An image pauses, shows, and streams its caption. Inline maths gets linearised into the prose, while a display equation pauses like a figure. The reader should classify blocks up front so pauses are deterministic, and show a small block ahead cue a few words before each stop so it is not jarring.

That is the synthesis. The plan is a context redesign, a block pause system driven by markers, and an instructions update for prose flow between pauses. Once you confirm the recommended path and the last agent lands, I will build all three in one pass.
