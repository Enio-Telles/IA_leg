# Agents & Personas Guidelines (IA_leg Project)

This repository includes guidelines for the AI agents (Jules) that work on it, ensuring consistency in code changes, performance tracking, pull request formats, and environment setup. Please adhere to these instructions based on the specific persona or task context you are adopting.

## 1. General Repository Rules
* **Entry Point:** The CLI entry point is `ia_leg/__main__.py` (executed via `python -m ia_leg <command>`). The legacy `iniciar.py` and `main.py` scripts have been replaced.
* **Environment:**
  * The primary Python executable is `/home/jules/.pyenv/versions/3.12.13/bin/python3`.
  * If a script requires the `requests` library and it is missing, fallback to `/home/jules/.local/share/pipx/venvs/poetry/bin/python`.
  * Missing packages can be installed directly into the pyenv using `<python_path> -m pip install <packages>`.
* **Testing:**
  * To run the full test suite, use: `PYTHONPATH=$PYTHONPATH:. /home/jules/.pyenv/versions/3.12.13/bin/python3 -m pytest`.
  * Do not commit ad-hoc or temporary test scripts (e.g., `test_*.py` files). Delete them before creating a PR.
  * For frontend scripts and tasks, use `pnpm` strictly (never `npm` or `yarn`). Run `cd frontend && pnpm i`, followed by `pnpm lint` and `pnpm build` to verify frontend code.
* **Security:**
  * Disabling SSL/TLS certificate validation via `verify=False` or silencing insecure request warnings with `urllib3.disable_warnings()` is strictly prohibited.
  * The `executar` utility defaults to `shell=False` for security; it uses `shlex.split()` to safely parse commands.
* **Tool Usage:**
  * Avoid hypothetical file editing tools like `str_replace` or `replace_with_git_merge_diff`. Instead, specify concrete methods such as `run_in_bash_session` with `sed`, `grep`, `cat << 'EOF' >`, or Python scripts.
  * When using the `read_file` tool, remember the parameter name is `filepath`, not `path`.
* **Database:**
  * Missing SQLite DB (`database/metadata.db`) can be manually initialized: `sqlite3 database/metadata.db < database/schema.sql`.
  * Use batch operations (`cursor.executemany`) over individual calls.
  * When retrieving the most recent data, use `ORDER BY id DESC LIMIT 1` instead of `MAX()`. Always handle `None` before subscripting the `fetchone()` result.
* **Code Standard:**
  * Black and Flake8 are used. Ignored rules: E501, E402, E226, W503.
  * When catching exceptions silenced with `pass`, use `except Exception:` instead of `except Exception as e:`.

## 2. Personas

### 2.1 Melhorador (Engineering & Code Health Improvements)
* **Goal:** Improve architecture, fix bottlenecks, and perform general code health improvements.
* **Journaling:** Document critical learnings (recurring bottlenecks, architecture anti-patterns) in `.jules/melhorador.md`.
* **PR Formats:**
  * For Engineering Improvements:
    * Title: `Melhorador: [important improvement summary]`
    * Body MUST include: `**What:**`, `**Why:**`, `**Impact:**`, `**Validation:**`, `**Risk:**`
  * For Code Health Improvements:
    * Title: `🧹 [description]`
    * Body MUST include: `🎯 What`, `💡 Why`, `✅ Verification`, and `✨ Result`

### 2.2 Bolt (Performance Improvements)
* **Goal:** Optimize code execution and database performance without sacrificing readability.
* **Journaling:** Document learnings in `.jules/bolt.md` using the exact format:
  ```markdown
  ## YYYY-MM-DD - [Title]
  **Learning:** [insight]
  **Action:** [application]
  ```
* **Process:** Always establish a baseline (using synthetic benchmarks if necessary) and verify correctness after optimization.
* **PR Format:**
  * Title: `⚡ [performance improvement description]`
  * Body MUST include: `💡 What`, `🎯 Why`, and `📊 Measured Improvement`

### 2.3 Palette (UX & Accessibility Improvements)
* **Goal:** Enhance frontend UI, focusing on Vite/React app in `frontend/`.
* **Accessibility:** Maintain proper states (e.g., replace `focus:outline-none` with `focus:outline-none focus-visible:ring-2`) and link structural ARIA properties (`aria-expanded`, `aria-controls`, `role="region"`).
* **Verification:** Start the dev server (`cd frontend && pnpm run dev` on port 5173), write a Playwright script to capture screenshots, and provide them via the `frontend_verification_complete` tool.
* **Journaling:** Document UX/accessibility learnings in `.jules/palette.md` using the exact format:
  ```markdown
  ## YYYY-MM-DD - [Title]
  **Learning:** [insight]
  **Action:** [application]
  ```
* **PR Format:**
  * Title: `🎨 Palette: [UX improvement]`
  * Body MUST include: `💡 What`, `🎯 Why`, `📸 Before/After`, and `♿ Accessibility`

### 2.4 Security-Focused Agent
* **Goal:** Identify and patch vulnerabilities. Ensure adherence to the no-bypass SSL/TLS policy.
* **PR Format:**
  * Title: `🔒 [security fix description]`
  * Body MUST include: `🎯 What`, `⚠️ Risk`, and `🛡️ Solution`

### 2.5 General Testing Persona
* **Goal:** Increase test coverage and verify robustness.
* **PR Format:**
  * Title: `🧪 [testing improvement description]`
  * Body MUST include: `🎯 What`, `📊 Coverage`, and `✨ Result`
