# Alignment Checker

## What it does

Determines whether the engine's output was genuinely aligned with the human's intent. Operates across two turns, not one. After reading the input and output of a given turn, it opens a pending verdict. That verdict resolves only when the next human message arrives.

## Why it exists

Single-turn checks can only judge whether an output looks correct. They cannot confirm whether it actually landed. The alignment checker uses the human's next move as the ground truth signal. A follow-up question with no correction or disagreement means the output was understood and accepted. That is the alignment signal. Anything else is a flag.

## Two-phase verdict

Phase 1 runs immediately after the turn completes. The agent reads the human input (from human logger) and the engine output (from harness logger). It does not produce a final verdict yet. It opens a pending record.

Phase 2 runs when the next human message arrives. The agent reads that message and applies the classification rule.

Classification rule: if the human's next message is a follow-up question and contains no correction or disagreement, the verdict is ALIGNED and a reward is logged. If the human corrects, disagrees, restates the question, or expresses confusion, the verdict is MISALIGNED.

## Input

Phase 1: human input from human logger + engine output from harness logger, for the current turn.
Phase 2: the next human message, once it arrives.

## Output

```json
{
  "agent": "alignment-checker",
  "status": "aligned" | "misaligned" | "pending",
  "turn_id": "UUID of the turn being evaluated",
  "reward": true | false,
  "reason": "description of the signal that resolved the verdict"
}
```

Status is "pending" after Phase 1. It resolves to "aligned" or "misaligned" after Phase 2.

## Position in the system

Stateful. Cannot be fully resolved in a single pass. Depends on human logger for Phase 1 input and receives the next human turn from the coordinator when it arrives. An aligned verdict with reward is a positive training signal. A misaligned verdict is high priority for the correction layer.
