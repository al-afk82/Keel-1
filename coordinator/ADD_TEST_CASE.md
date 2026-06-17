/*
# Blueprint: Adding a New Test Case to the Drift Suite

This integration testing suite is fully decoupled using cross-process distributed tracing parameters (**Tracking IDs**). To add a new testing scenario to the system, follow this three-step blueprint.

---

## Step 1: Append the Target Scenario in `main.cpp`
Scroll down to the `test_suite` initialization array inside the `main()` function of `main.cpp`. Add a structural configuration object assigned to a brand new tracking suffix signature (e.g., `0005`).

```cpp
// Locate inside main.cpp -> main() -> test_suite vector initialization:
std::vector<TestCase> test_suite = {
    // ... Existing test cases (1 through 4)
    {
        "CASE 5: Custom Specialist Target Failure Scenario",
        "00000000-0000-0000-0000-000000000005", // The Unique Tracking ID
        false, // mock_misalignment: Passes 05-classifier early checks
        false, // mock_uncertainty: Let 13-verifier execute dynamically 
        "Your custom testing instruction context text payload."
    }
};
```

---

## Step 2: Update Scenario Routing in `mock_server.cpp`
Because `mock_agent_server` runs in an isolated process space, it reads the incoming JSON payloads to identify the current case by parsing the trailing sequence of the UUID. 

1. Near the top of the `handle_agent_request` function, declare your conditional scope flag:
```cpp
bool is_case_5 = (tracking_id.find("0005") != std::string::npos);
```

2. Implement your customized agent behavior conditions inside the evaluation tree. For example, if you want Case 5 to simulate a failure *only* inside the `08-constraints-checker` agent while others remain clean:
```cpp
else {
    // Default clean configuration parameters
    std::string test_certainty = "clean";
    std::string test_status = "success";

    // Custom isolated behavioral override for Case 5
    if (is_case_5 && agent_name == "08-constraints-checker") {
        test_certainty = "violation";
        test_status = "violation";
    }
    // Preserving baseline fallback assertions for Case 3 and Case 4
    else if (!is_case_1 && !is_case_2 && !is_case_5) {
        test_certainty = "violation";
        test_status = "violation";
    }

    response_body = {
        {"agent", agent_name}, 
        {"status", test_status}, 
        {"certainty", test_certainty}, 
        {"rule", "MOCK_AUDIT_MATCH"}, 
        {"excerpt", "```"},
        {"severity", "medium"}, 
        {"reason", "```"}, 
        {"error_code", nlohmann::json()}
    };
}
```

---

## Step 3: Recompile & Execute the Suite
Execute a build tree generation update to let the compiler build both independent targets:

```bash
# Run inside your build target environment
make

# Execute binaries sequentially or use your orchestration launcher script
# The new test case will evaluate automatically in order.
```
*/
