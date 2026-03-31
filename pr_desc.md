🎯 What
Removed the unused `from __future__ import annotations` import from `ia_leg/etl/legal_parser.py`.

💡 Why
This improves the readability and code health of the file by removing dead code. Type hints in this file use standard types from the `typing` module (`List` and `Tuple`) and do not require forward referencing or stringized annotations.

✅ Verification
- Validated with `git diff` that only line 9 was removed.
- Ran formatting (`black`) and linting (`ruff check`) with no errors.
- Verified syntactical correctness via `python3 -m py_compile` and unit test success for `test_legal_parser.py`.

✨ Result
Cleaned up the parser file by removing a redundant import, ensuring the codebase strictly maintains only required dependencies and headers.
