# Quality bar (Lead-owned)

Updated: 2026-11-20. The user's requirement: this ships as a professional tool, not something that looks generated in one go. "Professional" is defined here as things that can be checked. The Lead judges every increment against this page as well as its brief. Numbers marked *target* are budgets to be measured, not results.

## 1. It is right, and it can show why
- A run is reconciled with the ticks before anything is analysed (ARCHITECTURE.md, "Accuracy rules").
- Every finding stores the numbers that triggered it and the detector version and thresholds that produced it.
- Same inputs give the same findings, every time. A test runs the analysis twice and compares the results exactly.
- Hand-checked golden cases live in the test suite. Changing an expected answer needs a decision.
- No detector, and no measurement, without tests for: must flag, must not flag, the threshold edge.
- Where the tool cannot know something, it says so on screen. "Not evaluated" is never shown as "clean".

## 2. A run can be repeated and compared
- Every run records: the EA file's hash, its settings, the tester settings, which tick days were used (with their hashes), and the tool version.
- Any old run can be reopened exactly as it was. Two runs can be compared defect by defect.

## 3. It does not break, and when something fails it says what to do
- Every file write is atomic; every long job can be stopped and resumed.
- No silent failure: a failed step stops with a plain-language message naming the cause and the next action.
- `losslens doctor` checks the whole setup (Python, Node, browser, MT4 copy, tick store, disk space) and prints what is wrong in plain words.
- A log file per run, so a problem on the expert's PC can be diagnosed from the log alone.

## 4. It is fast enough that speed is never noticed (*targets*)
- App opens to a usable screen in under 2 seconds with a full year of results.
- Any filter, sort or search answers in under 100 ms on 100,000 findings.
- Opening a trade's replay takes under 300 ms; playback and scrubbing stay at 60 frames per second on a day of ticks.
- Clicking a defect moves the MT4 chart in under 1 second.
- These are measured by an automated benchmark that runs with the tests, not by impression.

## 5. Replay is a first-class feature
- Tick-by-tick playback of any trade or any time window: play, pause, step one tick, speed control, scrub.
- Bid and ask as separate lines, spread shown, with entry, exit, stop and target (including every stop or target change) drawn at the tick where they happened.
- The defect's proof is drawn on the replay: the level that was touched, the spread spike, the gap, the moment the target would have been hit.
- When the EA has a decision log, the rule that fired is shown at its tick.
- The same moment opens in MT4 with one click, and the replay and the list stay in step.

## 6. It is designed, not assembled
- The screens are designed before they are built: one visual system (type, colour, spacing, states), reviewed by the Lead with real data before the builder writes the app.
- Every screen has its empty, loading and error states. No dead ends, no placeholder text, no sample data in a shipped screen.
- Everything can be done from the keyboard. Next and previous defect are single keys.
- The expert's first session is tested: can he go from install to his first inspected defect without help?

## 7. The code is kept like a product
- Typed Python and TypeScript, one formatter and one linter per language, both enforced by the tests.
- Tests run on GitHub for every change. `main` only ever holds work the Lead has reviewed and accepted.
- Small, single-purpose modules with one owner each; the data formats between them are written down and versioned.
- No `TODO`, stub, mock or commented-out code in a shipped path.
- Versioned releases with a changelog. One-step install on a clean Windows PC, tested on a clean PC.
- Short documentation that is true: setup, daily use, adding a defect, what the tool cannot tell you.

## 8. How the bar is held
- One finishable step at a time, each with checks that can fail.
- The Lead runs every check itself on this PC. A report without real output is not accepted.
- At the risky steps (MT4 run, measurements, replay) a second, independent reviewer checks the work before it is accepted.
- An increment with a known defect is sent back, not accepted with a note.
- The no-live-trading guard (D-14) is part of every review.
