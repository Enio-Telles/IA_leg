🎯 **What:** The `consultar_norma_por_data` function in `etl/timeline.py` was an empty stub with no meaningful testing contract. This PR implements a comprehensive set of tests establishing a clear contract for the expected behavior of this function.

📊 **Coverage:** The test suite now covers:
*   Happy path (valid `id_norma` and `data`).
*   Edge cases with empty strings (`""`).
*   Invalid date formats (e.g., `01/01/2023`).
*   Handling of future dates (e.g., `2050-12-31`).
*   Handling of `None` inputs.
*   Type errors for missing arguments.
*   Handling of invalid types (e.g., integer inputs).

✨ **Result:** A solid testing contract is now established. The new tests verify that the stub behaves consistently (currently returning `None` safely or raising expected structural errors), providing a safety net for future development of the `consultar_norma_por_data` method.
