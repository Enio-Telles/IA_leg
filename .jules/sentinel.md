
## 2025-03-05 - Insecure HTML Parsing Fallback
**Vulnerability:** The HTML to text fallback parsing mechanism used a simplistic regular expression `re.sub(r'<[^>]+>', '\n', html_content)` to strip HTML tags when BeautifulSoup was not available. This approach was insecure because it could be easily bypassed with malformed tags or specific attributes, leading to potential Cross-Site Scripting (XSS) if the extracted text was re-rendered.
**Learning:** Regular expressions should not be used to parse or strip HTML due to HTML's complex syntax and edge cases. Built-in parsers like `html.parser.HTMLParser` provide a more robust and secure way to extract data without external dependencies.
**Prevention:** Use standard library tools like `html.parser.HTMLParser` or well-tested external libraries like `BeautifulSoup` for HTML parsing, and strictly avoid relying on regex for HTML tag stripping.
## 2026-03-24 - Fix SSRF in Answer Engines
**Vulnerability:** Server-Side Request Forgery (SSRF) via unvalidated URLs from environment variables `OLLAMA_URL` and `OPENAI_URL` inside `requests.post()` in `answer_engine.py` and `answer_engine_safe.py`.
**Learning:** Even though environment variables are generally trusted by administrators, they represent an attack surface where an insecure value could result in arbitrary requests made from the application server, potentially exposing internal networks.
**Prevention:** Always validate and sanitize URLs, ensuring they strictly follow `http` or `https` schemes and have a valid network location, prior to performing external requests, utilizing standard library modules like `urllib.parse`.
