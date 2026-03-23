from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:5173/linha-do-tempo")
        page.screenshot(path="linha_do_tempo.png")
        page.goto("http://localhost:5173/consulta-ia")
        page.screenshot(path="consulta_ia.png")
        page.goto("http://localhost:5173/explorar-normas")
        page.screenshot(path="explorar_normas.png")
        browser.close()

if __name__ == "__main__":
    run()
