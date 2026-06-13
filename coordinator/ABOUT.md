# Coordinator — About

Every output passes through here before it reaches the user. The coordinator does not check anything itself. It routes, collects, decides, and delivers. The intelligence lives in the agents. The coordinator's job is to trust them and act on what they return.

---

## The principle

The coordinator is the decision layer. Four agents run. Four verdicts come back. The coordinator looks at those verdicts and answers one question: does this output need to be corrected before the user sees it?

If yes, it sends the output to the corrector. If no, it passes the output through. Either way, it logs the event.

That is the entire job.

---

## Why the coordinator does not check anything

The temptation when building is to add logic here — check the severity threshold, add exceptions, handle edge cases. Resist this.

The coordinator that does not check anything is the coordinator that is easy to debug. When something goes wrong, you know immediately whether the problem is in an agent (bad verdict) or in the coordinator (bad routing decision). Keep the coordinator dumb and the agents smart.

---

## The builder's job

Build three things: the routing function that fans out to all four agents in parallel, the decision function that reads the verdicts and determines whether correction fires, and the logging function that writes every event to the catch log regardless of outcome.

The corrector is a separate file. The catch log is a separate file. The coordinator calls both. It does not contain the logic for either.

---

## Where this sits

The coordinator is the entry point to the entire system. Every output flows through it. If the coordinator breaks, nothing reaches the user. Build it to be the most reliable piece of the system.
