
## 2024-03-25 - Semantic Forms for Search and Chat Inputs
**Learning:** Interactive search and chat components lacking semantic `<form>` tags prevent native keyboard submission ('Enter' key) and mobile 'Go' actions, severely degrading the experience.
**Action:** Always wrap search and chat inputs with `<form>` and ensure submit buttons use `type="submit"`.

## 2024-03-26 - Keyboard Navigation and Context in Dynamic Lists
**Learning:** Interactive elements like buttons within lists/cards (e.g., "Ler Texto", "Detalhes") and custom input elements (like `<input type="range">`) often lack visible focus states (e.g., `focus:outline-none focus-visible:ring-2`) and specific `aria-label`s, creating a frustrating experience for keyboard-only and screen-reader users, as they cannot tell which item they are focused on or what the action will affect.
**Action:** Always ensure custom interactive elements have accessible focus states (`focus-visible:ring-2`) and provide dynamic `aria-label`s that incorporate context (e.g., `aria-label={\`Ler texto da versão de ${version.date} de ${result.type} ${result.number}\`}`) to buttons whose visible text is generic.
