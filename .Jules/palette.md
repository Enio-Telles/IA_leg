## 2024-03-24 - Accessible Custom Accordions and Focus Visibility
**Learning:** Custom accordions often fail accessibility checks because they lack `aria-expanded`, `aria-controls`, `role="region"` and visible focus states (`focus-visible:ring`). Focus visibility is critical for keyboard users and shouldn't be overridden globally with `focus:outline-none` without providing a `focus-visible` alternative.
**Action:** Always ensure custom toggle components maintain structural linkage between the header and the content panel to support screen readers, and provide distinct keyboard focus indicators (`focus-visible:ring-2` etc) when utilizing `focus:outline-none`.

## 2024-04-09 - Accessible SR-only text vs aria-label
**Learning:** For robust accessibility and internationalization, prefer using visually hidden text nodes (e.g., `<span className="sr-only">`) or explicit `<label>` elements over `aria-label` attributes. Automated translation tools often translate inner DOM text but skip attributes, leaving non-native screen reader users with un-translated accessible names.
**Action:** Always prefer `<span className="sr-only">` inside icon-only buttons or visually hidden explicit `<label>` elements for inputs instead of relying on `aria-label`.
## 2024-04-11 - Adicionando Atalhos de Teclado
**Learning:** Os usuários de sistemas com dados massivos se beneficiam muito da navegação via teclado. A inclusão do atalho `/` para focar diretamente na busca e o uso da tag `<kbd>` para explicitar o atalho ajudam na produtividade e acessibilidade.
**Action:** Sempre que houver um campo de busca central no sistema, incluir atalho (como `/`) e a tag semântica `<kbd>` para dica visual.
