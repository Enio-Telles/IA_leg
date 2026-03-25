"""
Módulo responsável pelo crawling de normas da SEFIN-RO.
Realiza coleta via API e controle por banco de dados SQLite para evitar duplicidades.
"""

import requests
import json
import sqlite3
from pathlib import Path

# Caminhos absolutos/relativos importados ou definidos localmente
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "metadata.db"
PDF_DIR = BASE_DIR / "documentos" / "pdf"

BASE_URL = "https://legislacao.sefin.ro.gov.br"

def conectar_banco():
    """Retorna a conexão com o banco SQLite."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def norma_existe(conn, id_lei_api: str) -> bool:
    """Verifica se o ID da lei (que chamaremos de hash/ref_origem opcionalmente) já existe para evitar reprocessamento."""
    # Neste caso vamos procurar na tabela `normas` ou usar uma tabela de controle de crawler.
    # Para o escopo básico, vamos armazenar o origin_id num novo campo da tabela normas se necessário,
    # Mas dado que a tabela normas tem "tipo, numero, ano" UNIQUE, podemos inspecionar esses dados.
    # Como a API retorna o ID, o mais seguro é olhar no banco o hash/id ou extrair tipo/ano do título.
    # Faremos uma tabela simples de log temporário caso não exista campo de ID de origem.
    
    # Vamos verificar se o PDF daquele ID já foi salvo.
    pdf_path = PDF_DIR / f"{id_lei_api}.pdf"
    if pdf_path.exists():
        return True
    
    # Ou se temos o conteudo salvo:
    json_path = PDF_DIR.parent / "texto" / f"{id_lei_api}.json"
    if json_path.exists():
        return True
    
    return False

def salvar_norma(id_lei: str, dados_detalhes: dict):
    """
    Salva os detalhes da norma em JSON. Se houver anexos (pdf), baixa-os.
    O processamento para alimentar o DB oficial ocorrerá no Pipeline ETL.
    """
    # Garante estrutura de pastas
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    TEXT_DIR = PDF_DIR.parent / "texto"
    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    json_path = TEXT_DIR / f"{id_lei}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(dados_detalhes, f, indent=4, ensure_ascii=False)
        
    print(f"Salvo JSON para Lei ID: {id_lei}")

def baixar_pdf(session, id_lei: str):
    """Obtém links de arquivos dessa norma e baixa o primeiro PDF que existir."""
    url_links = f"{BASE_URL}/link_arquivo/{id_lei}"
    try:
        resp = session.get(url_links, timeout=10)
        dados_json = resp.json()
        
        # A API retorna um dict com a chave 'anexos' contendo a lista
        arquivos = dados_json.get("anexos", [])
        
        for arq in arquivos:
            if not isinstance(arq, dict):
                 continue
            nome_original = arq.get("nome", "").lower()
            arquivo_ref = arq.get("arquivo")
            if ".pdf" in nome_original:
                # Vamos baixar
                url_download = f"{BASE_URL}/Download"
                resp_pdf = session.get(url_download, params={"arquivo": arquivo_ref, "nome": arq.get("nome")})
                if resp_pdf.status_code == 200:
                    pdf_path = PDF_DIR / f"{id_lei}.pdf"
                    with open(pdf_path, "wb") as f:
                        f.write(resp_pdf.content)
                    print(f"PDF baixado para a lei {id_lei}")
                    return True # Baixamos 1 pdf
    except Exception as e:
        import traceback
        print(f"Erro ao baixar PDF para {id_lei}: {e}")
        traceback.print_exc()
    
    return False

def executar_crawler(termos_busca=None):
    """
    Executa rotina principal de coleta consumindo a API da SEFIN.
    """
    if termos_busca is None:
        termos_busca = ["", "RICMS", "Anexo"]


    session = requests.Session()
    headers = {
        "User-Agent": "Crawler Institucional SEFIN/RO (Automated Process)",
        "Accept": "application/json"
    }
    session.headers.update(headers)

    print("Iniciando crawling da Sefin API...")

    conn = conectar_banco()
    try:
        for termo in termos_busca:
            print(f"\\n--- Iniciando coleta para o termo de busca: '{termo}' ---")
            pagina_atual = 1
            total_paginas = 1
            
            while pagina_atual <= total_paginas:
                print(f"-- Processando página {pagina_atual} de {total_paginas} (termo: '{termo}') --")
                url_pesquisa = f"{BASE_URL}/pesquisar_lei"
                params = {
                    "page": pagina_atual,
                    "por_pagina": 50,
                    "q": termo
                }
                
                resp = session.get(url_pesquisa, params=params)
                if resp.status_code != 200:
                    print(f"Falha ao pesquisar. Código {resp.status_code}")
                    break
                    
                dados = resp.json()
                
                if pagina_atual == 1:
                    pagina_info = dados.get("pagina_info", {})
                    # A API as vezes não devolve info total pages corretamente, se vier 0 mantemos limite safe.
                    fetched_total = pagina_info.get("total_pages", 1)
                    total_paginas = fetched_total if fetched_total is not None and fetched_total > 0 else 1
                    
                resultados = dados.get("resultados", [])
                
                if not resultados:
                    print("Não há mais resultados.")
                    break
                    
                for doc in resultados:
                    id_lei = str(doc.get("lei"))
                    titulo = doc.get("titulo", "")
                    
                    # Check duplication
                    if norma_existe(conn, id_lei):
                        continue
                    
                    print(f"Nova norma encontrada: {titulo[:50]}... ID: {id_lei}")
                    
                    # Obtem detalhes
                    url_detalhe = f"{BASE_URL}/pesquisar_detalhe_lei/{id_lei}"
                    resp_detalhe = session.get(url_detalhe)
                    if resp_detalhe.status_code == 200:
                        detalhes = resp_detalhe.json()
                        salvar_norma(id_lei, detalhes)
                        baixar_pdf(session, id_lei)
                    else:
                        print(f"Falha ao obter detalhe para id {id_lei}")

                pagina_atual += 1
                
                # Se for busca geral ('') e páginas > 20, ou para evitar sobrecarga no teste local,
                # vamos colocar um break manual após certas páginas se preferir.
                # Aqui vamos confiar no 'norma_existe' para não processar nada repetido.
                
    except Exception as e:
        import traceback
        print(f"Erro no loop do crawler: {e}")
        traceback.print_exc()
    finally:
        conn.close()
        print("Crawler finalizado.")

if __name__ == "__main__":
    executar_crawler()
