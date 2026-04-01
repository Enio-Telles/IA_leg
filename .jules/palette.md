
## 2024-03-25 - Semantic Forms for Search and Chat Inputs
**Learning:** Interactive search and chat components lacking semantic `<form>` tags prevent native keyboard submission ('Enter' key) and mobile 'Go' actions, severely degrading the experience.
**Action:** Always wrap search and chat inputs with `<form>` and ensure submit buttons use `type="submit"`.

## 2024-03-26 - Keyboard Navigation and Context in Dynamic Lists
**Learning:** Interactive elements like buttons within lists/cards (e.g., "Ler Texto", "Detalhes") and custom input elements (like `<input type="range">`) often lack visible focus states (e.g., `focus:outline-none focus-visible:ring-2`) and specific `aria-label`s, creating a frustrating experience for keyboard-only and screen-reader users, as they cannot tell which item they are focused on or what the action will affect.
**Action:** Always ensure custom interactive elements have accessible focus states (`focus-visible:ring-2`) and provide dynamic `aria-label`s that incorporate context (e.g., `aria-label={\`Ler texto da versão de ${version.date} de ${result.type} ${result.number}\`}`) to buttons whose visible text is generic.

## 2024-05-20 - Adding Visual Feedback to Asynchronous Form Submissions
**Learning:** Users lack confidence when interacting with AI chat interfaces if there is no immediate visual feedback that their input is being processed. It's critical to disable inputs to prevent duplicate submissions and show a clear loading indicator (like a spinner) in the submit button. In addition, interactive elements using Tailwind CSS inside forms need explicit `focus-visible` styles to ensure proper keyboard accessibility.
**Action:** Always provide explicit visual feedback (loading spinners, disabled states) during asynchronous form submissions and ensure `focus-visible` rings are configured on interactive buttons, especially when relying on `focus:outline-none`.
## 2024-05-14 - Loading state UI improvements
**Learning:** Adding `disabled={isLoading}` state to the text input in forms with loading state prevents unexpected behavior where the user types while the form is processing.
**Action:** Always add `disabled={isLoading}` to the main `<input>` or form elements associated with a submit button that has a loading state.
## 2024-05-15 - Focus Visibility in Sidebar NavLinks
**Learning:** Global layout components like sidebars often neglect keyboard focus visibility, leaving keyboard users unable to navigate the primary menu.
**Action:** Always add explicit focus-visible classes (e.g. focus-visible:ring-2 focus-visible:ring-offset-2) to all interactive elements in Layout components.
