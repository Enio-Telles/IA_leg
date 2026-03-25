
## 2024-03-25 - Semantic Forms for Search and Chat Inputs
**Learning:** Interactive search and chat components lacking semantic `<form>` tags prevent native keyboard submission ('Enter' key) and mobile 'Go' actions, severely degrading the experience.
**Action:** Always wrap search and chat inputs with `<form>` and ensure submit buttons use `type="submit"`.
