# Pattern Threshold

A pattern qualifies for a new rule proposal when:

1. The same rule ID has fired 3 or more times
2. All 3 instances have user_response set to "accepted"
3. The excerpts share a recognisable common pattern

If user_response is "overridden" on any instance — the rule fired incorrectly. Do not propose. Flag the existing rule for review instead.

If user_response is null — the user did not respond. Do not count toward the threshold.
