🎯 **What:**
Fixed a vulnerability where missing OpenAI API keys resulted in silent failures. Previously, the system logged a message and returned `(None, 0.0)` which could mask misconfigurations or lead to unexpected and potentially insecure behavior in upstream components that consume the LLM output.

⚠️ **Risk:**
If left unfixed, the lack of an explicit failure could lead to unpredictable downstream behavior or silent application degradation if API credentials were unintentionally removed, compromised and rotated, or misconfigured. This obfuscates root causes and violates the fail-fast principle.

🛡️ **Solution:**
Modified `chamar_openai` in `ia_leg/rag/answer_engine.py` and `_chamar_openai` in `ia_leg/rag/answer_engine_safe.py` to raise a `ValueError` explicitly when `OPENAI_URL` or `OPENAI_KEY` are not set. This guarantees the system fails fast and loudly on missing required credentials.
