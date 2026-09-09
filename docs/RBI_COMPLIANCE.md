# Reserve Bank of India (RBI) Compliance Mapping

This document provides the formal regulatory compliance mapping between the **Nandi Plugin** and RBI mandates governing Indian Scheduled Commercial Banks, Small Finance Banks, Payments Banks, NBFCs, and Payment System Operators.

---

## 1. Master Direction on IT Governance, Risk, Controls and Assurance Practices (2023)

| RBI Mandate Section | Regulatory Requirement | Plugin Implementation | Verification Test |
| :--- | :--- | :--- | :--- |
| **Chapter III, Para 11 (Data Protection & Privacy)** | Regulated Entities (REs) must enforce strict boundary controls preventing unauthorized exposure or transmission of sensitive customer PII and financial records. | `PIIDetector` engine with Verhoeff checksums for Aadhaar, entity validation for PAN, and CBS account number pattern validation. Hard-blocks violating prompts in `PreInvocation` and `PreToolUse`. | `tests/test_pii_detector.py` |
| **Chapter III, Para 14 (Cyber Security Threat Defense)** | REs shall implement automated detection and defensive mechanisms against algorithmic manipulation, prompt injection, and malicious input vectors targeting automated decision systems. | `ModelArmorClient` connecting to Google Cloud Model Armor (`asia-south1`). Evaluates prompt injection, jailbreak, and adversarial indicators before model processing. | `tests/test_model_armor.py` |
| **Chapter V, Para 22 (Audit Trail & Logging)** | Detailed, time-synchronized, tamper-evident audit trails must be generated for all automated transactions, security exceptions, and policy blocks, and retained for at least 7 years. | `FSIAuditLogger` generating SHA-256 cryptographically chained JSON audit events with UTC and IST timestamps. | `tests/test_governance.py` |

---

## 2. Master Direction on Digital Payment Security Controls (2021)

| RBI Mandate Section | Regulatory Requirement | Plugin Implementation | Verification Test |
| :--- | :--- | :--- | :--- |
| **Section 4 (Cardholder Data Security)** | Entities shall not store raw Primary Account Numbers (PAN) or Card Verification Values (CVV) in unencrypted logs, prompts, or test parameters. | Detection of 13-16 digit payment card numbers (RuPay, Visa, Mastercard) via Luhn algorithm, plus CVV pattern scanner. Automated blocking in `PreToolUse`. | `tests/test_checksums.py` |
| **Section 5 (UPI & Real-Time Payment Guardrails)** | Protection of customer Virtual Payment Addresses (VPA) and payment identifiers from unauthorized automated exposure. | Context-aware regex matching for all NPCI PSP bank handles (`@okaxis`, `@okhdfcbank`, `@oksbi`, `@paytm`, `@ybl`, etc.). | `tests/test_checksums.py` |

---

## 3. Digital Personal Data Protection (DPDP) Act, 2023 Alignment

| DPDP Act Provision | Legal Requirement | Technical Safeguard |
| :--- | :--- | :--- |
| **Section 6 (Notice & Consent)** | Processing of digital personal data must be for lawful and explicit purposes. | Real-time advisory and audit event recording when PII entities are encountered. |
| **Section 8 (Data Principal Protection)** | Data Fiduciaries must implement reasonable security safeguards to prevent personal data breaches. | Automated fail-closed gate preventing PII from ever reaching external LLMs or third-party APIs. |
| **Section 9 (Processing of Sensitive Data)** | Specific protections for biometric, identity (Aadhaar), and financial records. | Verhoeff-validated Aadhaar detection and tokenized format-preserving redaction (`XXXX-XXXX-1234`). |
