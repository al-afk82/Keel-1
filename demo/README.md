# Demo

Everything needed to run the two-minute demo for judges.

## Files in this folder

- `violations.md` — five deliberate violations, one per agent plus a combined case. Each entry has: the prompt, the broken output, which agent should catch it, and the expected corrected output.
- `script.md` — the two-minute demo script. What to say, what to click, what the judge should see.
- `test-run-log.md` — results from each dry-run. What fired, what did not, what needed fixing.

## The demo moment

Judge sees a prompt go in. A broken output appears briefly (or is shown in the catch log). The agent flags it. The corrected output is what actually gets delivered. The catch log shows what was wrong and which agent caught it.

The before-and-after comparison is the demo. Everything else supports it.
