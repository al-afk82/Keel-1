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

// what we pass to and get back from most safety checks
struct Verdict {
  std::string agent;
  std::string status;
  std::string certainty;
  std::optional<std::string> rule;
  std::optional<std::string> excerpt;
  std::optional<std::string> severity;
  std::optional<std::string> reason; // forgot this earlier, do not delete again
  std::optional<std::string> error_code;
};

// tracks permissions and user/engine scopes
struct Profile {
  std::string agent;
  std::string status;
  std::optional<std::string> id;
  std::optional<std::string>
      input_id; // nlohmann crashed when this was blank, made it optional
  std::string role;
  std::string scope;
  std::optional<std::string> error_code;
};

// just for the gate results
struct Alignment {
  std::string agent;
  std::string status;
  std::optional<std::string> reason;
  std::optional<std::string> error_code;
};

// Fixed names here to match main.cpp tracking vars so compilation stops failing
struct AuditPayload {
  std::string tracking_id;
  std::string human_msg;
  std::string thinking_chain;
  std::optional<std::string> voice_checker_extra_thinking;
};

struct VerifierVerdict {
  std::string agent;
  std::string status; // "violation" or "clean"
  std::optional<std::string> rule;
  std::optional<std::string> excerpt;
  std::optional<std::string> severity; // "high" or "medium"
};

// Reflect exactly 5 fields

// macros for serialization junk
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Profile, agent, status, id, input_id, role,
                                   scope, error_code)

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Verdict, agent, status, certainty, rule,
                                   excerpt, severity, reason, error_code)

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(Alignment, agent, status, reason, error_code)

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(AuditPayload, tracking_id, human_msg,
                                   thinking_chain, voice_checker_extra_thinking)
NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(VerifierVerdict, agent, status, rule,
                                   excerpt, severity)
