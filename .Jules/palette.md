## 2024-03-19 - [ARIA Labels on Icon Buttons]
**Learning:** Icon-only action buttons (like the send button in the AI chat) often lack accessible names, making them invisible to screen readers, and lack visual feedback when actions are unavailable.
**Action:** Always pair `aria-label` with `title` for icon-only buttons, and implement `disabled` states with visual feedback (like opacity/cursor changes) to prevent empty submissions and improve perceived affordance.
