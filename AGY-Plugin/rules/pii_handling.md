---
trigger: model_decision
description: "Guidelines for handling, testing, and redacting Indian Personally Identifiable Information (PII)."
---

# Indian PII Handling & Redaction Guidelines

Use these guidelines when generating mock data, unit tests, sample logs, or data pipelines:

## 1. Synthetic / Mock Data Standards
* Never use real customer Aadhaar, PAN, Card, or Bank Account numbers in unit tests or code examples.
* Use recognized dummy ranges:
  - Mock PAN: `ABCDE1234F` (Invalid 4th character 'D' prevents collision with real individual PANs) or designated sandbox ranges.
  - Mock Aadhaar: Test with generated Verhoeff check digits from safe test prefixes.
  - Mock Cards: Use standard test card ranges (e.g. Visa `4111 1111 1111 1111`, RuPay `5081 2345 6789 0123`).

## 2. Redaction Patterns
* Always apply format-preserving masking when redacting data for LLM analysis:
  - Aadhaar: `XXXX-XXXX-{last4}`
  - PAN: `{first2}XXXXX{last3}`
  - Account: `XXXXXXXXXXXX{last4}`
  - Card: `{first4}-XXXX-XXXX-{last4}`
  - Phone: `+91-XXXXX-{last4}`
  - UPI: `{first2}***@{handle}`
