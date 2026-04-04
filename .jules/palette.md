
## 2024-03-25 - Semantic Forms for Search and Chat Inputs
**Learning:** Interactive search and chat components lacking semantic `<form>` tags prevent native keyboard submission ('Enter' key) and mobile 'Go' actions, severely degrading the experience.
**Action:** Always wrap search and chat inputs with `<form>` and ensure submit buttons use `type="submit"`.

## 2024-03-26 - Keyboard Navigation and Context in Dynamic Lists
**Learning:** Interactive elements like buttons within lists/cards (e.g., "Ler Texto", "Detalhes") and custom input elements (like `<input type="range">`) often lack visible focus states (e.g., `focus:outline-none focus-visible:ring-2`) and specific `aria-label`s, creating a frustrating experience for keyboard-only and screen-reader users, as they cannot tell which item they are focused on or what the action will affect.
**Action:** Always ensure custom interactive elements have accessible focus states (`focus-visible:ring-2`) and provide dynamic `aria-label`s that incorporate context (e.g., `aria-label={\`Ler texto da versão de ${version.date} de ${result.type} ${result.number}\`}`) to buttons whose visible text is generic.

## 2024-05-20 - Adding Visual Feedback to Asynchronous Form Submissions
**Learning:** Users lack confidence when interacting with AI chat interfaces if there is no immediate visual feedback that their input is being processed. It's critical to disable inputs to prevent duplicate submissions and show a clear loading indicator (like a spinner) in the submit button. In addition, interactive elements using Tailwind CSS inside forms need explicit `focus-visible` styles to ensure proper keyboard accessibility.
**Action:** Always provide explicit visual feedback (loading spinners, disabled states) during asynchronous form submissions and ensure `focus-visible` rings are configured on interactive buttons, especially when relying on `focus:outline-none`.

## 2026-03-15 - Missing Feedback on Global Action Buttons
**Learning:** Global action buttons (like "Atualizar Base") often lack immediate visual feedback and disabled states, leading to duplicate submissions and poor screen reader experience during async operations.
**Action:** Always pair async button actions with a disabled state, a visual loading indicator (`animate-spin`), `aria-live="polite"` for screen readers, and clear focus states (`focus-visible`). Simulated async loading states are effective for demonstrating these UI patterns when backend APIs are pending.

## 2024-05-24 - Avoid overriding visible text with aria-label
**Learning:** Adding an `aria-label` to an interactive element (like a button) that already contains sufficient visible descriptive text is an accessibility anti-pattern. It completely overrides the visible text for screen readers and breaks automatic translation tools because they skip attributes.
**Action:** Use visually hidden text nodes (e.g., `<span className="sr-only">`) appended to the visible text instead of `aria-label` to provide extra context without overriding the visible text.
