🎨 Palette: [UX improvement] Adding loading states and accessible focus for chat input

💡 **What:** Added a `Loader2` spinner to the form submit button in `ConsultaIA.tsx`. Disabled the button and text input during the loading state. Also added explicit `focus-visible` ring styling to the submit button.
🎯 **Why:** Users need visual feedback when waiting for an async AI response to prevent duplicate submissions and frustration. Keyboard-only and screen reader users also need to see clearly when the button is focused, since it was previously stripped of focus rings via `focus:outline-none`.
📸 **Before/After:** See `verification/focused.png` and `verification/loading.png`.
♿️ **Accessibility:** Improved keyboard accessibility with `focus-visible:ring-2 focus-visible:ring-blue-500` and `disabled` states to inform assistive technologies when the form is processing.
