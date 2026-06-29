# How-to guide — task-oriented

A how-to guide helps a **competent** user achieve a **specific goal**. They already know the basics; they have a job to do and probably a deadline. Answer "how do I X?" and get out of the way. (Diátaxis: practice + application.)

## The discipline

- **Assume competence.** Don't teach fundamentals — link to the tutorial for that. The reader knows the tool; they need this particular recipe.
- **One goal per guide.** The title is the goal: "How to rotate the signing key", "How to add a new Kafka consumer". If you're covering two goals, write two guides.
- **A sequence of actions, not a lecture.** Numbered steps toward the result. Minimal prose between them.
- **Address the real-world messiness.** Unlike a tutorial, a how-to can and should handle variations: "if you're on staging, also…", "for the legacy path, instead…". The reader has a real situation, not a sandbox.
- **Name the end state.** What does success look like, and how do they confirm it?

## Shape

1. Title = the goal, phrased as a task.
2. One line of context / when you'd do this (and any prerequisite or precondition).
3. Numbered steps to the outcome.
4. Verification: how to confirm it worked.
5. Optional: common variations, and links to related guides.

## How-to vs tutorial

The line that trips people up: a tutorial onboards someone from zero with a guaranteed path; a how-to serves someone who already knows the ropes and needs *this* task done. If your "how-to" starts with "first, install Python and learn the basics", it's a tutorial wearing the wrong label.
