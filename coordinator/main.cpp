#include <chrono>
#include <drogon/drogon.h>
#include <future>
#include <memory>
#include <nlohmann/json.hpp>
#include <optional>
#include <random>
#include <spdlog/spdlog.h>
#include <sstream>
#include <string>
#include <tbb/parallel_invoke.h>
#include <tbb/task_group.h>
#include <thread>
#include <vector>

#include "types.hpp"

std::string generate_uuid() {
  thread_local std::mt19937 gen(std::random_device{}());
  std::uniform_int_distribution<uint32_t> hex_dis(0, 15);
  std::uniform_int_distribution<uint32_t> var_dis(8, 11);
  std::ostringstream ss;
  ss << std::hex;
  for (int i = 0; i < 8; i++) ss << hex_dis(gen);
  ss << "-";
  for (int i = 0; i < 4; i++) ss << hex_dis(gen);
  ss << "-4";
  for (int i = 0; i < 3; i++) ss << hex_dis(gen);
  ss << "-";
  ss << var_dis(gen);
  for (int i = 0; i < 3; i++) ss << hex_dis(gen);
  ss << "-";
  for (int i = 0; i < 12; i++) ss << hex_dis(gen);
  return ss.str();
}

// split host and path prefix so drogon doesn't lose its mind over urls
const std::string BAND_HOST = "http://127.0.0.1:5000";
const std::string API_BASE = "/api/agent/";

// ============================================================================
// NETWORK STUFF (Zero-exception wraps around nlohmann + drogon)
// ============================================================================

void async_fire_and_forget(const std::string &route,
                           const std::string &json_body) {
  auto client = drogon::HttpClient::newHttpClient(BAND_HOST);
  auto req = drogon::HttpRequest::newHttpRequest();
  req->setMethod(drogon::Post);
  req->setPath(API_BASE + route);
  req->setContentTypeCode(drogon::CT_APPLICATION_JSON);
  req->setBody(json_body);

  client->sendRequest(
      req, [route](drogon::ReqResult result, const drogon::HttpResponsePtr &) {
        if (result != drogon::ReqResult::Ok) {
          spdlog::warn("Async logger target [{}] dropped packet.", route);
        }
      });
}

Verdict sync_fetch_verdict(const std::string &route,
                           const std::string &json_body) {
  auto client = drogon::HttpClient::newHttpClient(BAND_HOST);
  auto req = drogon::HttpRequest::newHttpRequest();
  req->setMethod(drogon::Post);
  req->setPath(API_BASE + route);
  req->setContentTypeCode(drogon::CT_APPLICATION_JSON);
  req->setBody(json_body);

  auto prom = std::make_shared<std::promise<Verdict>>();
  auto fut = prom->get_future();

  client->sendRequest(req, [prom, route](drogon::ReqResult result,
                                         const drogon::HttpResponsePtr &resp) {
    Verdict v;
    v.agent = route;

    if (result != drogon::ReqResult::Ok || !resp) {
      v.status = "violation";
      v.error_code = "NETWORK_DISCONNECT";
      prom->set_value(v);
      return;
    }

    auto parsed_raw = nlohmann::json::parse(resp->getBody(), nullptr, false);
    if (parsed_raw.is_discarded()) {
      v.status = "violation";
      v.error_code = "JSON_PARSE_ERR";
      prom->set_value(v);
      return;
    }

    try {
      v = parsed_raw.get<Verdict>();
    } catch (const std::exception &e) {
      spdlog::error("Exception in verdict parsing for {}: {}", route, e.what());
      v.status = "violation";
      v.error_code = "DESERIALIZATION_ERR";
    }
    prom->set_value(v);
  });

  // 2.5s guard timeout so we don't hang the loop forever if an agent dies
  if (fut.wait_for(std::chrono::milliseconds(2500)) ==
      std::future_status::timeout) {
    Verdict timeout_v;
    timeout_v.agent = route;
    timeout_v.status = "violation";
    timeout_v.error_code = "AGENT_TIMEOUT";
    return timeout_v;
  }

  return fut.get();
}

Profile sync_fetch_profile(const std::string &route,
                           const std::string &json_body) {
  auto client = drogon::HttpClient::newHttpClient(BAND_HOST);
  auto req = drogon::HttpRequest::newHttpRequest();
  req->setMethod(drogon::Post);
  req->setPath(API_BASE + route);
  req->setContentTypeCode(drogon::CT_APPLICATION_JSON);
  req->setBody(json_body);

  auto prom = std::make_shared<std::promise<Profile>>();
  auto fut = prom->get_future();

  client->sendRequest(req, [prom, route](drogon::ReqResult result,
                                         const drogon::HttpResponsePtr &resp) {
    Profile p;
    p.agent = route;

    if (result != drogon::ReqResult::Ok || !resp) {
      p.status = "error";
      p.error_code = "NETWORK_FAILURE";
      prom->set_value(p);
      return;
    }

    auto parsed_raw = nlohmann::json::parse(resp->getBody(), nullptr, false);
    if (parsed_raw.is_discarded() || !parsed_raw.is_object()) {
      p.status = "error";
      p.error_code = "PARSING_FAILURE";
      prom->set_value(p);
      spdlog::info("Errored body: {}", resp->getBody());
      spdlog::info("Raw json: {}", parsed_raw.dump());
      return;
    }

    // manual extraction here to keep nlohmann from crashing on missing keys
    try {
      p.agent = parsed_raw.value("agent", route);
      p.status = parsed_raw.value("status", "unknown");
      p.role = parsed_raw.value("role", "unknown");
      p.scope = parsed_raw.value("scope", "unknown");

      if (parsed_raw.contains("input_id") &&
          !parsed_raw["input_id"].is_null()) {
        p.input_id = parsed_raw["input_id"].get<std::string>();
      } else {
        p.input_id = std::nullopt;
      }

      if (parsed_raw.contains("id") && !parsed_raw["id"].is_null()) {
        p.id = parsed_raw["id"].get<std::string>();
      } else {
        p.id = std::nullopt;
      }

      p.error_code = std::nullopt;
    } catch (const std::exception &e) {
      spdlog::error("Exception in profile parsing for {}: {}", route, e.what());
      p.status = "error";
      p.error_code = "DESERIALIZATION_EXCEPTION";
    }

    prom->set_value(p);
  });

  if (fut.wait_for(std::chrono::milliseconds(2500)) ==
      std::future_status::timeout) {
    Profile timeout_p;
    timeout_p.agent = route;
    timeout_p.status = "error";
    timeout_p.error_code = "AGENT_TIMEOUT";
    return timeout_p;
  }

  return fut.get();
}

// ============================================================================
// MAIN PIPELINE COORDINATOR
// ============================================================================

void execute_drift_coordinator(const std::string &tracking_id,
                               const std::string &human_msg,
                               const std::string &thinking_chain) {
  spdlog::info("Coordinator started turn. Sequence ID: {}", tracking_id);

  AuditPayload base_payload{tracking_id, human_msg, thinking_chain,
                            std::nullopt};
  std::string context_buffer = nlohmann::json(base_payload).dump();

  // dump raw data to loggers in background threads
  tbb::task_group ingestion_group;
  ingestion_group.run([&context_buffer]() {
    async_fire_and_forget("01-human-logger", context_buffer);
  });
  ingestion_group.run([&context_buffer]() {
    async_fire_and_forget("02-thinking-logger", context_buffer);
  });

  // check profiles for user vs engine in parallel
  Profile human_prof;
  Profile engine_prof;

  tbb::parallel_invoke(
      [&]() {
        human_prof = sync_fetch_profile("03-human-profiler", context_buffer);
      },
      [&]() {
        engine_prof = sync_fetch_profile("04-engine-profiler", context_buffer);
      });

  // blow up early if profilers flunk out
  if (human_prof.error_code || engine_prof.error_code) {
    spdlog::error("Structural Profiler failure! Human Error: '{}', Engine "
                  "Error: '{}'. Terminating execution path.",
                  human_prof.error_code.value_or("None"),
                  engine_prof.error_code.value_or("None"));
    ingestion_group.wait();
    return;
  }

  nlohmann::json profiling_json;
  profiling_json["human"] = human_prof;
  profiling_json["engine"] = engine_prof;
  std::string profiling_aggregation = profiling_json.dump();
  Verdict alignment_verdict =
      sync_fetch_verdict("05-alignment-classifier", profiling_aggregation);

  // Remediation hook if drift occurs
  if (alignment_verdict.status == "misaligned") {
    spdlog::warn(
        "System state drift detected by [05]. Entering remediation loop.");

    // ask agent to make a clarification query
    Verdict question_verdict =
        sync_fetch_verdict("06-question-generator", profiling_aggregation);

    std::vector<std::string> internal_fallback_questions = {
        "Can you clarify the primary constraint of your last instruction?",
        "Did the system's previous thinking chain conflict with your intended "
        "scope?"};

    // pack up everything and ship it straight to the harness
    nlohmann::json remediation_payload = {
        {"base_context", base_payload},
        {"alignment_analysis", alignment_verdict},
        {"agent_generated_question", question_verdict},
        {"coordinator_fallback_questions", internal_fallback_questions}};

    async_fire_and_forget("13-harness-logger", remediation_payload.dump());

    spdlog::info("[System Output - Clarification Hook Dispatched to Harness]");
    ingestion_group.wait();
    return;
  }

  // Everything looks aligned, fire off auditing checks all at once
  spdlog::info(
      "Intent verified as aligned. Fanning out auditing execution threads.");

  // constraints agent gets profiler scope — it checks against pre-extracted scope, not raw text
  nlohmann::json constraints_payload = nlohmann::json::parse(context_buffer);
  constraints_payload["human_scope"] = human_prof.scope;
  constraints_payload["engine_scope"] = engine_prof.scope;
  std::string constraints_buffer = constraints_payload.dump();

  Verdict gap_v, constraint_v, anti_v, voice_v, quality_v, identity_v;

  tbb::task_group audit_group;
  audit_group.run(
      [&]() { gap_v = sync_fetch_verdict("07-gap-analyzer", context_buffer); });
  audit_group.run([&]() {
    constraint_v = sync_fetch_verdict("08-constraints-checker", constraints_buffer);
  });
  audit_group.run([&]() {
    anti_v = sync_fetch_verdict("09-anti-patterns-checker", context_buffer);
  });
  audit_group.run([&]() {
    voice_v = sync_fetch_verdict("10-voice-checker", context_buffer);
  });
  audit_group.run([&]() {
    quality_v = sync_fetch_verdict("11-quality-checker", context_buffer);
  });
  audit_group.run([&]() {
    identity_v = sync_fetch_verdict("12-identity-agent", context_buffer);
  });

  audit_group.wait(); // sync up before checking findings

  // save internal notes if voice checker has any
  if (voice_v.status == "clean" && voice_v.excerpt.has_value()) {
    base_payload.voice_checker_extra_thinking = voice_v.excerpt.value();
  }

  // all non-clean findings go to harness; only confirmed violations go to verifier
  std::vector<Verdict> all_findings;
  std::vector<Verdict> raw_auditor_findings;
  for (auto *finding :
       {&gap_v, &constraint_v, &anti_v, &voice_v, &quality_v, &identity_v}) {
    if (finding->status != "clean") {
      all_findings.push_back(*finding);
    }
    if (finding->status == "violation" || finding->status == "drifted") {
      raw_auditor_findings.push_back(*finding);
    }
  }

  bool definitive_violation = false;

  // pass dirty issues over to final validation gate
  if (!raw_auditor_findings.empty()) {
    std::string verifier_payload = nlohmann::json(raw_auditor_findings).dump();
    Verdict verification_gate =
        sync_fetch_verdict("verifier", verifier_payload);

    if (verification_gate.status == "violation") {
      definitive_violation = true;
      spdlog::error("[CRITICAL DRIFT]: Verifier confirmed risk profile.");
    }
  }

  // send all findings to harness — status field tells it how to log each one
  nlohmann::json database_transaction = {
      {"payload", base_payload},
      {"findings", all_findings}};
  async_fire_and_forget("13-harness-logger", database_transaction.dump());

  ingestion_group.wait(); // wrap up any dangling logging threads before closing out
  spdlog::info("Coordinator turn completed successfully for ID: {}",
               tracking_id);
}

int main() {
  spdlog::set_pattern("%^[%T.%e] [THREAD %t] [%L] %v%$");

  // production entry point — receives human_msg and thinking_chain, fires pipeline
  drogon::app().registerHandler(
      "/coordinate",
      [](const drogon::HttpRequestPtr &req,
         std::function<void(const drogon::HttpResponsePtr &)> &&callback) {
        auto body =
            nlohmann::json::parse(req->getBody(), nullptr, false);

        if (body.is_discarded() || !body.contains("human_msg") ||
            !body.contains("thinking_chain")) {
          auto resp = drogon::HttpResponse::newHttpResponse();
          resp->setStatusCode(drogon::k400BadRequest);
          resp->setBody(R"({"error":"missing human_msg or thinking_chain"})");
          callback(resp);
          return;
        }

        std::string tracking_id = generate_uuid();
        std::string human_msg = body["human_msg"].get<std::string>();
        std::string thinking_chain = body["thinking_chain"].get<std::string>();

        std::thread([tracking_id, human_msg, thinking_chain]() {
          execute_drift_coordinator(tracking_id, human_msg, thinking_chain);
        }).detach();

        auto resp = drogon::HttpResponse::newHttpResponse();
        resp->setStatusCode(drogon::k202Accepted);
        resp->setContentTypeCode(drogon::CT_APPLICATION_JSON);
        resp->setBody(nlohmann::json{{"tracking_id", tracking_id}}.dump());
        callback(resp);
      },
      {drogon::Post});

  // test worker — generates a fresh UUID each run
  std::thread test_worker([]() {
    std::this_thread::sleep_for(std::chrono::milliseconds(1500));
    spdlog::info("Worker thread triggering pipeline turn execution...");
    execute_drift_coordinator(generate_uuid(), "Hello",
                              "<thinking>None</thinking>");
  });

  test_worker.detach();

  drogon::app().addListener("0.0.0.0", 8080).run();
  return 0;
}
