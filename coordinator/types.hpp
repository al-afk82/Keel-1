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

// nlohmann macros / custom parsers

NLOHMANN_DEFINE_TYPE_NON_INTRUSIVE(BasePayload, input_id, human_input,
                                   engine_response)

// --- Profile: tolerant from_json that handles missing keys ---
inline void to_json(nlohmann::json &j, const Profile &p) {
  j = nlohmann::json{
      {"agent", p.agent},          {"status", p.status}, {"id", p.id},
      {"input_id", p.input_id},    {"role", p.role},     {"scope", p.scope},
      {"error_code", p.error_code}};
}

inline void from_json(const nlohmann::json &j, Profile &p) {
  p.agent = j.value("agent", "");
  p.status = j.value("status", "");
  p.role = j.value("role", "");
  p.scope = j.value("scope", "");
  p.id = (j.contains("id") && !j["id"].is_null())
             ? std::optional<std::string>(j["id"].get<std::string>())
             : std::nullopt;
  p.input_id =
      (j.contains("input_id") && !j["input_id"].is_null())
          ? std::optional<std::string>(j["input_id"].get<std::string>())
          : std::nullopt;
  p.error_code =
      (j.contains("error_code") && !j["error_code"].is_null())
          ? std::optional<std::string>(j["error_code"].get<std::string>())
          : std::nullopt;
}

// --- Verdict: tolerant from_json that handles missing keys ---
inline void to_json(nlohmann::json &j, const Verdict &v) {
  j = nlohmann::json{{"agent", v.agent},         {"status", v.status},
                     {"certainty", v.certainty}, {"rule", v.rule},
                     {"excerpt", v.excerpt},     {"severity", v.severity},
                     {"reason", v.reason},       {"error_code", v.error_code}};
}

inline void from_json(const nlohmann::json &j, Verdict &v) {
  v.agent = j.value("agent", "");
  v.status = j.value("status", "");
  v.certainty = j.value("certainty", "");
  v.rule = (j.contains("rule") && !j["rule"].is_null())
               ? std::optional<std::string>(j["rule"].get<std::string>())
               : std::nullopt;
  v.excerpt = (j.contains("excerpt") && !j["excerpt"].is_null())
                  ? std::optional<std::string>(j["excerpt"].get<std::string>())
                  : std::nullopt;
  v.severity =
      (j.contains("severity") && !j["severity"].is_null())
          ? std::optional<std::string>(j["severity"].get<std::string>())
          : std::nullopt;
  v.reason = (j.contains("reason") && !j["reason"].is_null())
                 ? std::optional<std::string>(j["reason"].get<std::string>())
                 : std::nullopt;
  v.error_code =
      (j.contains("error_code") && !j["error_code"].is_null())
          ? std::optional<std::string>(j["error_code"].get<std::string>())
          : std::nullopt;
}
