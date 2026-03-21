## 2024-05-18 - Added ARIA Labels to Chat Interface
**Learning:** Found that the main chat input and send button in the `ConsultaIA` component lacked explicit `aria-label` attributes, which are crucial for screen reader accessibility, especially when the button is icon-only.
**Action:** Always ensure that icon-only buttons have an `aria-label` and `title` (for tooltip), and that primary inputs have an associated label or `aria-label`.
