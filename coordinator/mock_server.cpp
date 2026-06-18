#include <drogon/drogon.h>
#include <nlohmann/json.hpp>
#include <optional>
#include <spdlog/spdlog.h>
#include <string>

#include "types.hpp"

// handles everything the coordinator hits
void handle_agent_request(
    const drogon::HttpRequestPtr &req,
    std::function<void(const drogon::HttpResponsePtr &)> &&callback,
    const std::string &agent_name) {

  auto resp = drogon::HttpResponse::newHttpResponse();
  resp->setContentTypeCode(drogon::CT_APPLICATION_JSON);
  nlohmann::json response_body;

  // need to find where the input_id is hidden
  std::string input_id;
  auto body = nlohmann::json::parse(req->getBody(), nullptr, false);

  if (body.is_object()) {
    if (body.contains("input_id") && body["input_id"].is_string()) {
      input_id = body["input_id"].get<std::string>();
    } else if (body.contains("payload") && body["payload"].is_object() &&
               body["payload"].contains("input_id")) {
      // harness logger puts it inside payload
      input_id = body["payload"]["input_id"].get<std::string>();
    }
  }

  bool is_case_1 = (input_id.find("0001") != std::string::npos);
  bool is_case_2 = (input_id.find("0002") != std::string::npos);

  // logger routes - just say okay
  if (agent_name.find("logger") != std::string::npos) {
    spdlog::info("{} logged {}", agent_name, input_id);
    resp->setStatusCode(drogon::k200OK);
    resp->setBody("{\"agent\":\"" + agent_name + "\", \"status\":\"logged\"}");
    callback(resp);
    return;
  }

  // profilers return the profile blob
  if (agent_name.find("profiler") != std::string::npos) {
    bool is_human = (agent_name.find("human") != std::string::npos);
    response_body = {
        {"agent", agent_name},
        {"status", "profiled"},
        {"id", is_human ? "human" : "engine"},
        {"input_id", input_id},
        {"role", "operator"},
        {"scope", is_case_2 ? "restricted_access" : "global_access"},
        {"error_code", nlohmann::json()}};

    // alignment classifier
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

    // 06 is skipped for now but here just in case
  } else if (agent_name == "06-question-generator") {
    response_body = {
        {"agent", "06-question-generator"}, {"status", "action_required"},
        {"certainty", "uncertain"},         {"rule", "REMEDIATION_HOOK"},
        {"excerpt", "verify clearance"},    {"severity", "high"},
        {"error_code", nlohmann::json()},   {"reason", "Scope mismatch"}};

    // 13 verifier - just flags things that arent case 1 or 2
  } else if (agent_name == "13-verifier") {
    bool has_issues = !(is_case_1 || is_case_2);

    spdlog::info("13 ruling: {} for {}", has_issues ? "violation" : "clean",
                 input_id);

    response_body = {
        {"agent", "13-verifier"},
        {"status", has_issues ? "violation" : "clean"},
        {"certainty", has_issues ? "violation" : "clean"},
        {"rule",
         has_issues ? nlohmann::json("SUPREME_GUARDRAIL") : nlohmann::json()},
        {"excerpt", has_issues ? nlohmann::json("Trace payload violation")
                               : nlohmann::json()},
        {"severity", has_issues ? nlohmann::json("high") : nlohmann::json()},
        {"reason", nlohmann::json()},
        {"error_code", nlohmann::json()}};

    // specialists 07-12
  } else {
    bool clean = (is_case_1 || is_case_2);
    response_body = {{"agent", agent_name},
                     {"status", clean ? "success" : "violation"},
                     {"certainty", clean ? "clean" : "violation"},
                     {"rule", "MOCK_AUDIT_MATCH"},
                     {"excerpt", "pattern match"},
                     {"severity", "medium"},
                     {"reason", "auto trigger"},
                     {"error_code", nlohmann::json()}};
  }

  spdlog::info("{} responding with {} for {}", agent_name,
               response_body.value("status", "?"), input_id);
  resp->setStatusCode(drogon::k200OK);
  resp->setBody(response_body.dump());
  callback(resp);
}

int main() {
  spdlog::set_pattern("%^[%T.%e] [MOCK] %v%$");
  spdlog::info("running mock on 5055");

  drogon::app()
      .registerHandler(
          "/api/agent/{name}",
          [](const drogon::HttpRequestPtr &req,
             std::function<void(const drogon::HttpResponsePtr &)> &&callback,
             std::string agent_name) {
            handle_agent_request(req, std::move(callback), agent_name);
          },
          {drogon::Post})
      .addListener("127.0.0.1", 5055)
      .run();

  return 0;
}
