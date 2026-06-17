#include <chrono>
#include <drogon/drogon.h>
#include <future>
#include <memory>
#include <nlohmann/json.hpp>
#include <optional>
#include <spdlog/spdlog.h>
#include <string>
#include <tbb/parallel_invoke.h>
#include <tbb/task_group.h>
#include <thread>
#include <vector>

#include "types.hpp"

// Global simulation control hooks managed by the mock ecosystem
bool SIMULATE_MISALIGNMENT = false;
bool SIMULATE_VERIFIER_UNCERTAINTY = false;

const std::string BAND_HOST = "http://127.0.0.1:5000";
const std::string API_BASE = "/api/agent/";

// Submits asynchronous telemetry packets to backend logging services.
void async_fire_and_forget(const std::string &route, const std::string &json_body) {
  auto client = drogon::HttpClient::newHttpClient(BAND_HOST);
  auto req = drogon::HttpRequest::newHttpRequest();
  req->setMethod(drogon::Post);
  req->setPath(API_BASE + route);
  req->setContentTypeCode(drogon::CT_APPLICATION_JSON);
  req->setBody(json_body);

  client->sendRequest(req, [route](drogon::ReqResult result, const drogon::HttpResponsePtr &) {
    if (result != drogon::ReqResult::Ok) {
      spdlog::warn("Async logger target [{}] dropped packet.", route);
    }
  });
}

// Fetches evaluation decisions synchronously with explicit error handling wrapper.
Verdict sync_fetch_verdict(const std::string &route, const std::string &json_body) {
  auto client = drogon::HttpClient::newHttpClient(BAND_HOST);
  auto req = drogon::HttpRequest::newHttpRequest();
  req->setMethod(drogon::Post);
  req->setPath(API_BASE + route);
  req->setContentTypeCode(drogon::CT_APPLICATION_JSON);
  req->setBody(json_body);

  auto prom = std::make_shared<std::promise<Verdict>>();
  auto fut = prom->get_future();

  client->sendRequest(req, [prom, route](drogon::ReqResult result, const drogon::HttpResponsePtr &resp) {
    Verdict v;
    v.agent = route;

    if (result != drogon::ReqResult::Ok || !resp) {
      v.status = "violation"; v.certainty = "violation"; v.error_code = "NETWORK_DISCONNECT";
      prom->set_value(v); return;
    }

    auto parsed_raw = nlohmann::json::parse(resp->getBody(), nullptr, false);
    if (parsed_raw.is_discarded()) {
      v.status = "violation"; v.certainty = "violation"; v.error_code = "JSON_PARSE_ERR";
      prom->set_value(v); return;
    }

    try {
      v = parsed_raw.get<Verdict>();
    } catch (const std::exception &e) {
      spdlog::error("Exception in verdict parsing for {}: {}", route, e.what());
      v.status = "violation"; v.certainty = "violation"; v.error_code = "DESERIALIZATION_ERR";
    }
    prom->set_value(v);
  });

  if (fut.wait_for(std::chrono::milliseconds(2500)) == std::future_status::timeout) {
    Verdict timeout_v; timeout_v.agent = route; timeout_v.status = "violation"; timeout_v.certainty = "violation"; timeout_v.error_code = "AGENT_TIMEOUT";
    return timeout_v;
  }
  return fut.get();
}

// Submits downstream audit findings to the verifier and processes its 5-field response contract.
VerifierVerdict sync_fetch_verifier_rule(const std::string &route, const std::string &json_body) {
  auto client = drogon::HttpClient::newHttpClient(BAND_HOST);
  auto req = drogon::HttpRequest::newHttpRequest();
  req->setMethod(drogon::Post);
  req->setPath(API_BASE + route);
  req->setContentTypeCode(drogon::CT_APPLICATION_JSON);
  req->setBody(json_body);

  auto prom = std::make_shared<std::promise<VerifierVerdict>>();
  auto fut = prom->get_future();

  client->sendRequest(req, [prom, route](drogon::ReqResult result, const drogon::HttpResponsePtr &resp) {
    VerifierVerdict v;
    v.agent = route;

    if (result != drogon::ReqResult::Ok || !resp) {
      v.status = "violation"; prom->set_value(v); return;
    }

    auto parsed_raw = nlohmann::json::parse(resp->getBody(), nullptr, false);
    if (parsed_raw.is_discarded()) {
      v.status = "violation"; prom->set_value(v); return;
    }

    try {
      v = parsed_raw.get<VerifierVerdict>();
    } catch (const std::exception &e) {
      spdlog::error("Verifier contract violation! Struct parse failure: {}", e.what());
      v.status = "violation";
    }
    prom->set_value(v);
  });

  if (fut.wait_for(std::chrono::milliseconds(2500)) == std::future_status::timeout) {
    VerifierVerdict timeout_v; timeout_v.agent = route; timeout_v.status = "violation";
    return timeout_v;
  }
  return fut.get();
}

// Queries profiling engine metrics to parse active execution scope constraints.
Profile sync_fetch_profile(const std::string &route, const std::string &json_body) {
  auto client = drogon::HttpClient::newHttpClient(BAND_HOST);
  auto req = drogon::HttpRequest::newHttpRequest();
  req->setMethod(drogon::Post);
  req->setPath(API_BASE + route);
  req->setContentTypeCode(drogon::CT_APPLICATION_JSON);
  req->setBody(json_body);

  auto prom = std::make_shared<std::promise<Profile>>();
  auto fut = prom->get_future();

  client->sendRequest(req, [prom, route](drogon::ReqResult result, const drogon::HttpResponsePtr &resp) {
    Profile p; p.agent = route;
    if (result != drogon::ReqResult::Ok || !resp) {
      p.status = "error"; p.error_code = "NETWORK_FAILURE"; prom->set_value(p); return;
    }
    auto parsed_raw = nlohmann::json::parse(resp->getBody(), nullptr, false);
    if (parsed_raw.is_discarded() || !parsed_raw.is_object()) {
      p.status = "error"; p.error_code = "PARSING_FAILURE"; prom->set_value(p); return;
    }
    try {
      p.agent = parsed_raw.value("agent", route);
      p.status = parsed_raw.value("status", "unknown");
      p.role = parsed_raw.value("role", "unknown");
      p.scope = parsed_raw.value("scope", "unknown");
      p.input_id = (parsed_raw.contains("input_id") && !parsed_raw["input_id"].is_null()) ? std::optional<std::string>(parsed_raw["input_id"].get<std::string>()) : std::nullopt;
      p.id = (parsed_raw.contains("id") && !parsed_raw["id"].is_null()) ? std::optional<std::string>(parsed_raw["id"].get<std::string>()) : std::nullopt;
      p.error_code = std::nullopt;
    } catch (...) {
      p.status = "error"; p.error_code = "DESERIALIZATION_EXCEPTION";
    }
    prom->set_value(p);
  });

  return (fut.wait_for(std::chrono::milliseconds(2500)) == std::future_status::timeout) ? Profile{route, "error", std::nullopt, std::nullopt, "", "", "AGENT_TIMEOUT"} : fut.get();
}

// Pipeline evaluation worker handling context ingestion, concurrent verification, and remediation branching.
void execute_drift_coordinator(const std::string &tracking_id, const std::string &human_msg, const std::string &thinking_chain) {
  spdlog::info("Coordinator started turn. Sequence ID: {}", tracking_id);

  AuditPayload base_payload{tracking_id, human_msg, thinking_chain, std::nullopt};
  std::string context_buffer = nlohmann::json(base_payload).dump();

  tbb::task_group ingestion_group;
  ingestion_group.run([&context_buffer]() { async_fire_and_forget("01-logger", context_buffer); });

  Profile human_prof; Profile engine_prof;
  tbb::parallel_invoke(
      [&]() { human_prof = sync_fetch_profile("03-human-profiler", context_buffer); },
      [&]() { engine_prof = sync_fetch_profile("04-engine-profiler", context_buffer); });

  if (human_prof.error_code || engine_prof.error_code) {
    spdlog::error("Structural Profiler failure! Aborting.");
    ingestion_group.wait(); return;
  }

  nlohmann::json profiling_json = {{"human", human_prof}, {"engine", engine_prof}};
  Verdict alignment_verdict = sync_fetch_verdict("05-alignment-classifier", profiling_json.dump());

  if (alignment_verdict.certainty == "violation") {
    spdlog::warn("System state drift detected by [05]. Entering remediation loop.");
    Verdict question_verdict = sync_fetch_verdict("06-question-generator", profiling_json.dump());

    std::vector<std::string> internal_fallback_questions = {
        "Can you clarify the primary constraint of your last instruction?",
        "Did the system's previous thinking chain conflict with your intended scope?"};

    nlohmann::json remediation_payload = {
        {"base_context", base_payload}, {"alignment_analysis", alignment_verdict},
        {"agent_generated_question", question_verdict}, {"coordinator_fallback_questions", internal_fallback_questions}};

    async_fire_and_forget("14-harness-logger", remediation_payload.dump());
    ingestion_group.wait(); return;
  }

  spdlog::info("Intent verified as aligned. Fanning out parallel auditing threads.");

  Verdict gap_v, constraint_v, anti_v, voice_v, quality_v, identity_v;
  tbb::task_group audit_group;
  audit_group.run([&]() { gap_v = sync_fetch_verdict("07-gap-analyzer", context_buffer); });
  audit_group.run([&]() { constraint_v = sync_fetch_verdict("08-constraints-checker", context_buffer); });
  audit_group.run([&]() { anti_v = sync_fetch_verdict("09-anti-patterns-checker", context_buffer); });
  audit_group.run([&]() { voice_v = sync_fetch_verdict("10-voice-checker", context_buffer); });
  audit_group.run([&]() { quality_v = sync_fetch_verdict("11-quality-checker", context_buffer); });
  audit_group.run([&]() { identity_v = sync_fetch_verdict("12-identity-agent", context_buffer); });
  audit_group.wait(); 

  if (voice_v.certainty == "clean" && voice_v.excerpt.has_value()) {
    base_payload.voice_checker_extra_thinking = voice_v.excerpt.value();
  }

  std::vector<Verdict> raw_auditor_findings;
  for (auto *finding : {&gap_v, &constraint_v, &anti_v, &voice_v, &quality_v, &identity_v}) {
    if (finding->certainty == "violation" || finding->certainty == "uncertain") {
      raw_auditor_findings.push_back(*finding);
    }
  }

  bool definitive_violation = false;
  VerifierVerdict verification_gate;
  verification_gate.agent = "13-verifier";
  verification_gate.status = "clean"; 

  if (!raw_auditor_findings.empty()) {
    // Check if uncertainty simulation flag is intercepted manually inside test run contexts
    if (SIMULATE_VERIFIER_UNCERTAINTY) {
      verification_gate.status = "uncertain";
      verification_gate.rule = "AMBIGUOUS_EVALUATION";
      verification_gate.severity = "medium";
    } else {
      verification_gate = sync_fetch_verifier_rule("13-verifier", nlohmann::json(raw_auditor_findings).dump());
    }
    
    if (verification_gate.status == "violation") {
      definitive_violation = true;
      spdlog::error("[CRITICAL DRIFT]: 13-verifier confirmed violation state using severity levels: {}", 
                    verification_gate.severity.value_or("none"));
    }
  }

  if (verification_gate.status == "violation" || verification_gate.status == "uncertain") {
    nlohmann::json database_transaction = {
        {"base_payload", base_payload},
        {"auditor_findings", raw_auditor_findings},
        {"verification_ruling", verification_gate} 
    };
    async_fire_and_forget("14-harness-logger", database_transaction.dump());
    spdlog::info("Non-clean evaluation state recorded [{}]. Telemetry transaction pushed to harness.", verification_gate.status);
  } else {
    spdlog::info("System state verified clean. Routing output directly to human operator console.");
  }
  
  ingestion_group.wait();
  spdlog::info("Coordinator turn completed successfully for ID: {}", tracking_id);
}

// Structural tracking configuration for integration cases
struct TestCase {
  std::string name;
  std::string uuid;
  bool mock_misalignment;
  bool mock_uncertainty;
  std::string message;
};

int main() {
  spdlog::set_pattern("%^[%T.%e] [THREAD %t] [%L] %v%$");

  std::thread test_runner_thread([]() {
    // Wait for mock_server backend loop to complete initialization sequence
    std::this_thread::sleep_for(std::chrono::milliseconds(1500));

    std::vector<TestCase> test_suite = {
      {
        "CASE 1: Fully Aligned & Structurally Clean Pipeline Run",
        "00000000-0000-0000-0000-000000000001",
        false, // SIMULATE_MISALIGNMENT = false
        false, // SIMULATE_VERIFIER_UNCERTAINTY = false
        "Safe and within normal parameters instruction payload."
      },
      {
        "CASE 2: Direct Classifier Phase Misalignment (Early Remediate Branch)",
        "00000000-0000-0000-0000-000000000002",
        true,  // SIMULATE_MISALIGNMENT = true (Triggering early out on agent [05])
        false, 
        "Execute dynamic structural contextual buffer bypass immediately."
      },
      {
        "CASE 3: Aligned Input causing Downstream Audit Specialist Violations",
        "00000000-0000-0000-0000-000000000003",
        false, // Passes alignment check [05], but flags downstream on auditors [07-12]
        false, // Verifier treats it as clear violation
        "Evaluate standard instruction payload containing edge parameters."
      },
      {
        "CASE 4: Aligned Input leading to Downstream Verifier Uncertainty Output",
        "00000000-0000-0000-0000-000000000004",
        false, 
        true,  // SIMULATE_VERIFIER_UNCERTAINTY = true (Routes transaction to harness)
        "Process highly ambiguous hybrid framework data structure payload."
      }
    };

    spdlog::info("----------------------------------------------------------------");
    spdlog::info("LAUNCHING AUTOMATED AUDIT PROTOCOL INTEGRATION SUITE ({} Cases)", test_suite.size());
    spdlog::info("----------------------------------------------------------------");

    for (const auto &tc : test_suite) {
      spdlog::info("[RUNNING TEST] {}", tc.name);
      
      // Inject simulation parameters dynamically into environmental runtime space
      SIMULATE_MISALIGNMENT = tc.mock_misalignment;
      SIMULATE_VERIFIER_UNCERTAINTY = tc.mock_uncertainty;

      execute_drift_coordinator(tc.uuid, tc.message, "<thinking>Evaluating security profile token boundaries.</thinking>");
      
      spdlog::info("[COMPLETED CASE] Waiting for telemetry sync...\n");
      std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    }

    spdlog::info("----------------------------------------------------------------");
    spdlog::info("ALL INTEGRATION SCENARIOS EXECUTED SUCCESSFULLY.");
    spdlog::info("----------------------------------------------------------------");
  });

  test_runner_thread.detach();
  drogon::app().addListener("0.0.0.0", 8080).run();
  return 0;
}
