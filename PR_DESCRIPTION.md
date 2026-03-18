# 🧪 [Testing] Add edge case and fallback tests for extrair_texto_html

## Description
This PR addresses a testing gap in the HTML to plaintext extraction logic found in `etl/html_to_text.py`. The `extrair_texto_html` function handles parsing of HTML into plaintext and implements a Regex-based fallback when the `bs4` (BeautifulSoup) module is unavailable.

### 🎯 What:
- Added comprehensive unit tests for `extrair_texto_html` in `tests/test_html_to_text.py`.
- Tested the fallback regex parsing behavior using `unittest.mock.patch` to simulate `NameError` triggered by a missing `BeautifulSoup`.
- Added tests for edge cases to ensure proper error handling and predictable string output.

### 📊 Coverage:
The following scenarios are now covered by the test suite:
1. **Happy path:** Accurate extraction of plain text from HTML, ignoring structural tags and retaining essential text.
2. **Edge cases:** Proper handling of `None` values and empty strings `""`, returning an empty string.
3. **Fallback path:** Ensuring `BeautifulSoup` errors correctly switch over to the Regex fallback parsing logic (`<[^>]+>`) to strip tags and format lines cleanly.
4. **Empty tags:** Verifying that HTML strings containing purely structural tags with no textual content return an empty string.
5. **Whitespace handling:** Checking for the elimination of excessive tabs, newlines, and spaces in favor of a clean, standardized format.

### ✨ Result:
- Increased test coverage for `etl/html_to_text.py`.
- Confidence that HTML string handling will correctly strip structural tags regardless of environment constraints (e.g. absent `bs4` library).
