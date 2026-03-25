
## 2025-03-05 - Insecure HTML Parsing Fallback
**Vulnerability:** The HTML to text fallback parsing mechanism used a simplistic regular expression `re.sub(r'<[^>]+>', '\n', html_content)` to strip HTML tags when BeautifulSoup was not available. This approach was insecure because it could be easily bypassed with malformed tags or specific attributes, leading to potential Cross-Site Scripting (XSS) if the extracted text was re-rendered.
**Learning:** Regular expressions should not be used to parse or strip HTML due to HTML's complex syntax and edge cases. Built-in parsers like `html.parser.HTMLParser` provide a more robust and secure way to extract data without external dependencies.
**Prevention:** Use standard library tools like `html.parser.HTMLParser` or well-tested external libraries like `BeautifulSoup` for HTML parsing, and strictly avoid relying on regex for HTML tag stripping.
