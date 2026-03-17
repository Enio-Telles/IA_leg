import requests
from bs4 import BeautifulSoup
import json

def explorar_site():
    url = "https://legislacao.sefin.ro.gov.br/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Encontrar os scripts na página para tentar descobrir rotas de API
        scripts = soup.find_all('script')
        print("Scritps encontrados na página inicial:")
        for script in scripts:
            if script.get('src'):
                print(f" - {script.get('src')}")
                
        print("\nTrechos de dados (estado inicial Vue/React) se houverem no HTML:")
        script_texts = [s.string for s in scripts if s.string and ('api' in s.string.lower() or 'url' in s.string.lower())]
        for t in script_texts:
            print(t[:500])

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    explorar_site()
