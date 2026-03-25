🎯 **What:** The `calcular_hash_texto` function in `etl/versionamento_pipeline.py` previously lacked unit tests. Testing it is crucial as it's a foundational utility for ensuring document versioning consistency across the application.
📊 **Coverage:** A new suite of deterministic unit tests has been implemented covering:
  * Standard text strings
  * Empty strings
  * Strings containing Unicode/special characters
  * Strings with formatting elements like tabs and newlines
  * Validation against a pre-calculated, known static SHA256 hash
✨ **Result:** Test coverage for this utility module is now established. The new deterministic tests guarantee that changes to the system's runtime or Python environment won't silently alter encoding mechanisms, maintaining the integrity of the database's versioning hash keys.
