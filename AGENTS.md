# APOS development requirements

The user requires German compliance to be considered in every future feature iteration.

For each feature, assess effects on fiscal records, receipts, consumer ordering, alcohol/food service and personal data. Update docs/COMPLIANCE.md when coverage, limitations or configuration obligations change. Verify changing legal requirements using current official sources. Add meaningful regression tests for relevant safeguards.

Do not describe APOS as legally compliant or TSE-certified without verified implementation and applicable operational review. Labels such as “tab-only” do not establish an exemption. Preserve original transactional records; use traceable cancellations rather than destructive deletion. Guest expiry revokes access and must not erase retained financial records. Never invent an association's legal identity, tax status, privacy legal basis or retention schedule.
