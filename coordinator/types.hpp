#pragma once
#include <nlohmann/json.hpp>
#include <optional>
#include <string>

namespace nlohmann {
template <typename T> struct adl_serializer<std::optional<T>> {
  static void to_json(json &j, const std::optional<T> &opt) {
    if (opt.has_value()) {
      j = *opt;
    } else {
      j = nullptr;
    }
  }

  static void from_json(const json &j, std::optional<T> &opt) {
    if (j.is_null()) {
      opt = std::nullopt;
    } else {
      opt = j.get<T>();
    }
  }
};
} // namespace nlohmann

// basic data blobs that match what the python script sends

// what we get at the start
struct BasePayload {
  std::string input_id;
  std::string human_input;
  std::string engine_response;
};

// results from the profiler agents
struct Profile {
  std::string agent;
  std::string status;
  std::optional<std::string> id;
  std::optional<std::string> input_id;
  std::string role;
  std::string scope;
  std::optional<std::string> error_code;
};

// generic verdict for almost everyone else
struct Verdict {
  std::string agent;
  std::string status;
  std::string certainty;
  std::optional<std::string> rule;
  std::optional<std::string> excerpt;
  std::optional<std::string> severity;
  std::optional<std::string> reason;
  std::optional<std::string> error_code;
};

// nlohmann macros so we dont have to write manual parsers

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(BasePayload, input_id, human_input,
                                   engine_response)

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Profile, agent, status, id, input_id, role,
                                   scope, error_code)

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Verdict, agent, status, certainty, rule,
                                   excerpt, severity, reason, error_code)
