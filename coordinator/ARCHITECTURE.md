====================================================================================
ARCHITECTURE OVERVIEW: HACKATHON DRIFT AGENT COORDINATOR
====================================================================================

# Distributed Multi-Agent Coordination & Drift Detection Architecture

This document presents the detailed structural and behavioral architecture of the 
asynchronous Drift Coordinator Pipeline. The system is designed to audit AI execution 
chains for alignment drift, utilizing concurrent thread scheduling, centralized 
batch processing, and deterministic fallback mechanics.

---

## 1. System Topology & Process Boundaries

The suite runs across two isolated operating system runtimes interacting over stateless 
HTTP connections. They maintain zero shared memory space:

1. **Coordinator Binary (`hackathon_drift_coordinator`)**:
   Written in C++20. Operates as an asynchronous scheduler using Intel Threading Building 
   Blocks (TBB) and the Drogon web framework. Handles orchestrating evaluation passes.
   
2. **Mock Agent Server (`mock_agent_server`)**:
   Written in C++20 using Drogon. Emulates a microservices network layer hosting 14 distinct 
   specialist agents, loggers, classifiers, and supreme guardrail verifiers.

---

## 2. Distributed Tracing & Process Correlation

Because the systems run in isolated process spaces, stateless transactions are correlated 
using a **Correlation ID (UUID)**.

```cpp
// The tracking UUID is embedded directly in incoming contexts and tracing headers:
AuditPayload base_payload{tracking_id, human_msg, thinking_chain, std::nullopt};
```

### Suffix-Based State Injection
During testing, the `mock_agent_server` inspects the trailing characters of the tracking 
UUID to identify which scenario is running and injects specialized simulated responses:
* Suffix `0001` -> Maps to Case 1 (Completely Clean Run)
* Suffix `0002` -> Maps to Case 2 (Early Alignment Intent Drift)
* Suffix `0003` -> Maps to Case 3 (Specialist Faults flagged, Verifier Violation)
* Suffix `0004` -> Maps to Case 4 (Specialist Faults flagged, Verifier Uncertainty)

---

## 3. Detailed Dataflow & Parallel Execution Pipeline

The coordinator processes a single evaluation turn through six chronological phases:

### Phase 1: Ingestion & Telemetry Logging (Parallel)
The incoming turn context is copied to an immutable buffer and submitted asynchronously 
to telemetry logging endpoints via thread-safe fire-and-forget loops:
* `01-human-logger`
* `02-thinking-logger`

### Phase 2: Concurrent Structural Profiling
Using `tbb::parallel_invoke`, the pipeline concurrently queries human and engine metadata 
profiles to evaluate authorization level constraints. This mitigates critical network 
I/O blocking overhead:
* `03-human-profiler`
* `04-engine-profiler`

```cpp
tbb::parallel_invoke(
    [&]() { human_prof = sync_fetch_profile("03-human-profiler", context_buffer); },
    [&]() { engine_prof = sync_fetch_profile("04-engine-profiler", context_buffer); }
);
```

### Phase 3: Alignment Classification (Sequential Bottleneck)
The compiled profile metadata is forwarded to `05-alignment-classifier`. 
* **If alignment is verified**: The pipeline continues to parallel auditing.
* **If intent drift is detected (`certainty == "violation"`)**: The system enters an early 
  remediation loop. It queries `06-question-generator` for active feedback, pushes 
  remediation details to `14-harness-logger`, and halts downstream auditing.

### Phase 4: Parallel Audit Fan-Out (Intel TBB Task Group)
If the input is verified as aligned, the coordinator fans out six specialized evaluation 
agents concurrently. They analyze distinct compliance contexts in parallel, completing 
execution in $O(\max(\text{time}))$ instead of $O(\sum(\text{time}))$:
* `07-gap-analyzer`
* `08-constraints-checker`
* `09-anti-patterns-checker`
* `10-voice-checker`
* `11-quality-checker`
* `12-identity-agent`

### Phase 5: Centralized Batching & Verdict Verification
Rather than forcing individual specialist agents to open separate HTTP connections to the 
verifier (which incurs massive socket and I/O overhead), the coordinator acts as a 
centralized **Mediator**:
1. It aggregates and filters the findings.
2. It drops all `"clean"` results.
3. If any anomalous findings exist (`"violation"` or `"uncertain"`), it batches them 
   into a single JSON array payload.
4. It submits the array to `13-verifier` via a single, lean HTTP call.

#### The Verifier's Strict Minimal Egress Schema
The verifier acts as the supreme definitive judge and excludes any `certainty` or 
`error_code` mappings, returning exactly five fields to prevent deserialization 
failures inside the coordinator's C++ mapping layer:

```cpp
struct VerifierVerdict {
  std::string agent;
  std::string status;                  // "violation" or "clean"
  std::optional<std::string> rule;
  std::optional<std::string> excerpt;
  std::optional<std::string> severity; // "high" or "medium"
};
```

### Phase 6: Conditional Router Egress
At the completion of the evaluation cycle, the coordinator routes the output based on 
the verifier's definitive verdict:

1. **Non-Clean Outcomes (`violation` or `uncertain`)**:
   The coordinator bundles the base context payload, the raw specialist findings, and 
   the verifier's exact ruling into a database transaction, shipping it to 
   `14-harness-logger` for deep diagnostic review.
   
2. **Clean Outcomes**:
   The transaction skips database telemetry serialization and is output directly to the 
   human operator console interface.

---

## 4. Why This Architecture Is Leaner

1. **Centralized Batching vs. Chained Cascades**: By filtering clean evaluations and batching 
   issues at the coordinator level, we reduce network connection handshakes with the 
   Verifier from six separate requests down to a single transaction.
2. **Zero-Exception Parsing**: Every HTTP and JSON parsing layer is wrapped in `std::promise` 
   and `nlohmann::json::parse(..., nullptr, false)` to guarantee that network disconnects or 
   malformed payloads cannot throw uncaught runtime exceptions or crash the coordinator process.
*/
