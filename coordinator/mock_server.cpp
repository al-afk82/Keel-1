#include <drogon/drogon.h>
#include <nlohmann/json.hpp>
#include <optional>
#include <spdlog/spdlog.h>
#include <string>

// true forces remediation branch down in the main coordinator
bool SIMULATE_MISALIGNMENT = true;

struct Verdict {
  std::string agent;
  std::string status;
  std::optional<std::string> rule;
  std::optional<std::string> excerpt;
  std::optional<std::string> severity;
  std::optional<std::string> reason; 
  std::optional<std::string> error_code;
};

// nlohmann macros are picking this up for auto json conversions
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Verdict, agent, status, rule, excerpt,
                                   severity, reason, error_code)

void handle_agent_request(
    const drogon::HttpRequestPtr &req,
    std::function<void(const drogon::HttpResponsePtr &)> &&callback,
    const std::string &agent_name) { 

  auto resp = drogon::HttpResponse::newHttpResponse();
  resp->setContentTypeCode(drogon::CT_APPLICATION_JSON);

  nlohmann::json response_body;

  // loggers just get an immediate generic okay status back
  if (agent_name.find("logger") != std::string::npos) {
    resp->setStatusCode(drogon::k200OK);
    resp->setBody("{\"agent\":\"" + agent_name + "\", \"status\":\"logged\"}");
    callback(resp);
    return;
  }

  // profiler needs to fake either global or restricted depending on test toggle
  if (agent_name.find("profiler") != std::string::npos) {
    response_body = {
        {"agent", agent_name}, 
        {"status", "profiled"},
        {"id",
         agent_name.find("human") != std::string::npos ? "human" : "engine"},
        {"input_id", "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"},
        {"role", "operator"},
        {"scope",
         SIMULATE_MISALIGNMENT ? "restricted_access" : "global_access"},
        {"error_code", nullptr}};
  }
  // classifier block determines whether we enter remediation or auditing
  else if (agent_name == "05-alignment-classifier") {
    response_body["agent"] = "05-alignment-classifier";
    response_body["status"] = SIMULATE_MISALIGNMENT ? "misaligned" : "aligned";
    if (SIMULATE_MISALIGNMENT) {
      response_body["reason"] = "Scope mismatch detected";
    } else {
      response_body["reason"] = nlohmann::json(); 
    }
    response_body["rule"] = nlohmann::json();
    response_body["excerpt"] = nlohmann::json();
    response_body["severity"] = nlohmann::json();
    response_body["error_code"] = nlohmann::json();
  }
  // generator won't be called unless 05 returns misaligned
  else if (agent_name == "06-question-generator") {
    response_body = {
        {"agent", "06-question-generator"},
        {"status", "action_required"},
        {"rule", "REMEDIATION_HOOK"},
        {"excerpt", "Can you verify your security clearance parameter?"},
        {"severity", "high"},
        {"error_code", nullptr},
        {"reason", "Scope mismatch detected"}}; // needs reason here or macro will fail parser
  }
  // standard fallback for all regular audit checkers
  else {
    response_body = {{"agent", agent_name},  {"status", "clean"},
                     {"rule", nullptr},      {"excerpt", nullptr},
                     {"severity", nullptr},  {"reason", nullptr},
                     {"error_code", nullptr}};
  }

  resp->setStatusCode(drogon::k200OK);
  resp->setBody(response_body.dump());
  callback(resp);
}

int main() {
  spdlog::set_pattern("%^[%T.%e] [MOCK SERVER] %v%$");
  spdlog::info("Starting Multi-Agent Mock Environment on port 5000...");

  /*
  // commented out the 5s loop toggle so state stays hard-locked for testing
  drogon::app().getLoop()->runEvery(5.0, []() {
    SIMULATE_MISALIGNMENT = !SIMULATE_MISALIGNMENT;
    spdlog::info("--- Switching Mock Mode: SIMULATE_MISALIGNMENT = {}",
  SIMULATE_MISALIGNMENT);
  });
  */

  // {name} parameter explicitly maps route tags into the handler argument
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
