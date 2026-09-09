---
name: model-armor-diagnostics
description: >-
  Diagnoses, tests, and validates Google Cloud Model Armor templates, filter
  configurations, and safety thresholds for LLM sanitization.
---

# Google Cloud Model Armor Diagnostics Skill

Use this skill to verify connection to Model Armor endpoints, test sanitization templates, and benchmark response latency.

## Diagnostic Procedures

### 1. Test Prompt Sanitization
```bash
python3 skills/model-armor-diagnostics/scripts/test_template.py --prompt "Test prompt here"
```

### 2. Run Adversarial Benchmark Suite
```bash
python3 skills/model-armor-diagnostics/scripts/test_template.py --benchmark
```
