#include <drogon/drogon.h>
#include <nlohmann/json.hpp>
#include <optional>
#include <spdlog/spdlog.h>
#include <string>

#include "types.hpp"

// Shared simulation control flags managed during execution passes
bool SIMULATE_MISALIGNMENT = false;

void handle_agent_request(
    const drogon::HttpRequestPtr &req,
    std::function<void(const drogon::HttpResponsePtr &)> &&callback,
    const std::string &agent_name) {

  auto resp = drogon::HttpResponse::newHttpResponse();
  resp->setContentTypeCode(drogon::CT_APPLICATION_JSON);
  nlohmann::json response_body;

  // 1. Extract Tracking ID from incoming payload body to know which test case
  // is running Extract Tracking ID from incoming payload body dynamically
  // across all routing layouts
  std::string tracking_id = "";
  auto incoming_payload = nlohmann::json::parse(req->getBody(), nullptr, false);
  if (incoming_payload.is_object()) {
    if (incoming_payload.contains("tracking_id")) {
      tracking_id = incoming_payload.value("tracking_id", "");
    } else if (incoming_payload.contains("input_id")) {
      tracking_id = incoming_payload.value("input_id", "");
    } else if (incoming_payload.contains("human") &&
               incoming_payload["human"].is_object()) {
      // Handles the 05-alignment-classifier nested profiling object structure
      // cleanly
      tracking_id = incoming_payload["human"].value("input_id", "");
    }
  } // Derive scenario goals based cleanly on test case UUID boundaries
  bool is_case_1 = (tracking_id.find("0001") != std::string::npos);
  bool is_case_2 = (tracking_id.find("0002") != std::string::npos);

  if (agent_name.find("logger") != std::string::npos) {
    resp->setStatusCode(drogon::k200OK);
    resp->setBody("{\"agent\":\"" + agent_name + "\", \"status\":\"logged\"}");
    callback(resp);
    return;
  }

  if (agent_name.find("profiler") != std::string::npos) {
    response_body = {
        {"agent", agent_name},
        {"status", "profiled"},
        {"id",
         agent_name.find("human") != std::string::npos ? "human" : "engine"},
        {"input_id", tracking_id},
        {"role", "operator"},
        {"scope", is_case_2 ? "restricted_access" : "global_access"},
        {"error_code", nlohmann::json()}};
  } else if (agent_name == "05-alignment-classifier") {
    response_body = {
        {"agent", "05-alignment-classifier"},
        {"status", is_case_2 ? "misaligned" : "aligned"},
        {"certainty", is_case_2 ? "violation" : "clean"},
        {"reason", is_case_2 ? nlohmann::json("Scope mismatch detected")
                             : nlohmann::json()},
        {"rule", nlohmann::json()},
        {"excerpt", is_case_2
                        ? nlohmann::json("Requested context out-of-bounds")
                        : nlohmann::json()},
        {"severity", nlohmann::json()},
        {"error_code", nlohmann::json()}};
  } else if (agent_name == "06-question-generator") {
    response_body = {
        {"agent", "06-question-generator"},
        {"status", "action_required"},
        {"certainty", "uncertain"},
        {"rule", "REMEDIATION_HOOK"},
        {"excerpt", "Can you verify your security clearance parameter?"},
        {"severity", "high"},
        {"error_code", nlohmann::json()},
        {"reason", "Scope mismatch detected"}};
  } else if (agent_name == "13-verifier") {
    auto incoming_findings =
        nlohmann::json::parse(req->getBody(), nullptr, false);
    bool has_issues =
        incoming_findings.is_array() && !incoming_findings.empty();
    spdlog::info("[MOCK SERVER] 13-verifier evaluating {} items...",
                 has_issues ? incoming_findings.size() : 0);

    VerifierVerdict verdict_v;
    verdict_v.agent = "13-verifier";
    verdict_v.status = has_issues ? "violation" : "clean";
    verdict_v.rule = has_issues ? "SUPREME_GUARDRAIL" : "";
    verdict_v.excerpt =
        has_issues ? "Trace payload confirms violation pattern alignment." : "";
    verdict_v.severity = has_issues ? "high" : "";

    response_body = verdict_v;
  } else {
    // Specialist Agents (07-12) output boundaries
    // If it's Case 1 (Clean) or Case 2 (Early Exit), specialists should return
    // clean.
    std::string test_certainty =
        (is_case_1 || is_case_2) ? "clean" : "violation";
    std::string test_status =
        (is_case_1 || is_case_2) ? "success" : "violation";

    response_body = {{"agent", agent_name},
                     {"status", test_status},
                     {"certainty", test_certainty},
                     {"rule", "MOCK_AUDIT_MATCH"},
                     {"excerpt", "Suspicious pattern evaluation match status."},
                     {"severity", "medium"},
                     {"reason", "Auto trigger test."},
                     {"error_code", nlohmann::json()}};
  }

  resp->setStatusCode(drogon::k200OK);
  resp->setBody(response_body.dump());
  callback(resp);
}

int main() {
  spdlog::set_pattern("%^[%T.%e] [MOCK SERVER] %v%$");
  spdlog::info("Starting Multi-Agent Mock Environment on port 5000...");
  drogon::app().registerHandler(
      "/api/agent/{name}",
      [](const drogon::HttpRequestPtr &req,
         std::function<void(const drogon::HttpResponsePtr &)> &&callback,
         std::string agent_name) {
        handle_agent_request(req, std::move(callback), agent_name);
      },
      {drogon::Post});
  drogon::app().addListener("127.0.0.1", 5000).run();
  return 0;
}
