import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

from config import BASE_DIR
from etl.pdf_to_text import extrair_texto_pdf
from etl.versionamento_pipeline import conectar, calcular_hash_texto, quebrar_pdf_em_chunks

import os

# Mapeamento estático baseado nos nomes de arquivos do projeto
MAPA_METADADOS_PDF = {
    "Difal_STF_Lei_Kandir.pdf": {"tipo": "Jurisprudencia_STF", "tema": "DIFAL", "numero": "STF/Kandir", "ano": 2023},
    "Guia Prático EFD - Versão 3.1.9.pdf": {"tipo": "Guia_Pratico_EFD", "tema": "Obrigacao_Acessoria", "numero": "3.1.9", "ano": 2024},
    "MOC_CTe_VisaoGeral_v4.00.pdf": {"tipo": "Manual_MOC", "tema": "Obrigacao_Acessoria", "numero": "4.0.0", "ano": 2023},
    "PARECER 443-2020 CIMENTO ASFALTICO 1 (1).pdf": {"tipo": "Parecer", "tema": "ICMS_ST", "numero": "443", "ano": 2020},
    "Enunciado_TATE_007_Responsavel_Solidario.pdf": {"tipo": "Jurisprudencia_TATE", "tema": "Responsabilidade_Solidaria", "numero": "007", "ano": 2022},
    "despachos fisconforme.pdf": {"tipo": "Despacho", "tema": "Fisconforme", "numero": "S/N", "ano": 2024},
    "Metodo_estoque.pdf": {"tipo": "Metodologia", "tema": "ICMS_ST", "numero": "S/N", "ano": 2024},
    "moc7-anexo-i-leiaute-e-rv (2).pdf": {"tipo": "Manual_MOC", "tema": "Obrigacao_Acessoria", "numero": "7.0", "ano": 2024},
    "Ressarcimento_ST_orientacao Fisconforme.pdf": {"tipo": "Orientacao", "tema": "Ressarcimento_ICMS_ST", "numero": "S/N", "ano": 2024}
}

def extrair_metadados_automaticos(arq_path: Path) -> dict:
    """Tenta extrair metadados automaticamente baseado no diretório e nome do arquivo."""
    nome = arq_path.name
    parent_folder = arq_path.parent.name.lower()
    
    # Se estiver na pasta enunciado_tate
    if parent_folder == "enunciado_tate":
        # Padrão: Enunciado-TATE-002 decadencia.pdf ou Enunciado_TATE_001_DIFAL.pdf
        base = nome.rsplit('.', 1)[0]
        match_num = re.search(r'(?:Enunciado|TATE)[-_]?(\d+)', base, re.IGNORECASE)
        numero = match_num.group(1) if match_num else "S/N"
        
        tema = "Jurisprudencia_TATE"
        partes = re.split(r'[-_ ]+', base)
        if len(partes) > 3:
            tema = "_".join(partes[3:])
            
        return {
            "tipo": "Jurisprudencia_TATE",
            "tema": tema,
            "numero": numero,
            "ano": 2024
        }
    
    # Se estiver na pasta sumulas_tate
    if parent_folder == "sumulas_tate":
        # Padrão: Sumula_01_TATE_RO.pdf
        match_num = re.search(r'Sumula_(\d+)', nome, re.IGNORECASE)
        numero = match_num.group(1) if match_num else "S/N"
        return {
            "tipo": "Sumula_TATE",
            "tema": "Sumula_Administrativa",
            "numero": numero,
            "ano": 2024
        }
    
    # Se estiver dentro de camara_plena_tate (qualquer nível)
    parts_lower = [p.lower() for p in arq_path.parts]
    if "camara_plena_tate" in parts_lower:
        # Numero do PAT do nome do arquivo
        match_pat = re.search(r'PAT_(\d+)', nome)
        numero_pat = match_pat.group(1) if match_pat else nome.rsplit('.', 1)[0]
        
        # Ano: buscar na pasta Decisoes_MM_YYYY ou na pasta de ano
        str_path = str(arq_path)
        match_ano = re.search(r'Decisoes_\d{2}_(\d{4})', str_path)
        if not match_ano:
            match_ano = re.search(r'[/\\](20\d{2})[/\\]', str_path)
        ano = int(match_ano.group(1)) if match_ano else 2024
        
        return {
            "tipo": "Jurisprudencia_TATE_Camara_Plena",
            "tema": "Decisao_Camara_Plena",
            "numero": numero_pat,
            "ano": ano
        }
    
    # Mapeamento estático (original)
    return MAPA_METADADOS_PDF.get(nome)

def ingerir_pdfs():
    pasta_pdfs = Path(BASE_DIR) / "documentos" / "pdf"
    # Busca recursiva para pegar subpastas como enunciado_tate
    arquivos = list(pasta_pdfs.rglob("*.pdf"))
    
    conn = conectar()
    cursor = conn.cursor()
    
    print(f"Iniciando integração de {len(arquivos)} PDFs ao banco de dados RAG...\n")
    
    for arq in arquivos:
        nome_arquivo = arq.name
        
        metadados = extrair_metadados_automaticos(arq)
        
        if not metadados:
            print(f"⚠️ Ignorando '{nome_arquivo}': não há mapeamento de metadados definido.")
            continue
            
        print(f"📄 Processando {nome_arquivo} (Tipo: {metadados['tipo']} | Tema: {metadados['tema']})")
        
        try:
            conn.execute("BEGIN TRANSACTION;")
            
            # 1. Extração do texto
            texto_sujo = extrair_texto_pdf(str(arq))
            if not texto_sujo:
                raise ValueError("Erro ao extrair o texto do PDF.")
            hash_texto = calcular_hash_texto(texto_sujo)
            
            # 2. Verificar ou Inserir Norma com TEMA
            cursor.execute(
                "SELECT id FROM normas WHERE tipo=? AND numero=? AND ano=?",
                (metadados["tipo"], metadados["numero"], metadados["ano"])
            )
            resultado = cursor.fetchone()
            
            if resultado:
                norma_id = resultado[0]
                cursor.execute("UPDATE normas SET tema=? WHERE id=?", (metadados["tema"], norma_id))
            else:
                cursor.execute(
                    "INSERT INTO normas (tipo, numero, ano, tema) VALUES (?, ?, ?, ?)",
                    (metadados["tipo"], metadados["numero"], metadados["ano"], metadados["tema"])
                )
                norma_id = cursor.lastrowid
                
            # 3. Verificar Versão
            cursor.execute(
                "SELECT id, hash_texto FROM versoes_norma WHERE norma_id=? AND vigencia_fim IS NULL",
                (norma_id,)
            )
            versao_atual = cursor.fetchone()
            
            if versao_atual and versao_atual[1] == hash_texto:
                print(f"  ✅ PDF já no banco de dados e sem alterações. Pulando.")
                conn.rollback()
                continue
                
            if versao_atual:
                cursor.execute("UPDATE versoes_norma SET vigencia_fim=CURRENT_DATE WHERE id=?", (versao_atual[0],))
                
            # 4. Inserir Nova Versão
            cursor.execute(
                "INSERT INTO versoes_norma (norma_id, texto_integral, hash_texto, vigencia_inicio) VALUES (?, ?, ?, CURRENT_DATE)",
                (norma_id, texto_sujo, hash_texto)
            )
            nova_versao_id = cursor.lastrowid
            
            # 5. Chunking & Dispositivos
            chunks = quebrar_pdf_em_chunks(texto_sujo)
            print(f"  ✂️ Dividido em {len(chunks)} trechos semânticos.")
            
            for identificador, conteudo in chunks:
                hash_disp = calcular_hash_texto(conteudo)
                cursor.execute(
                    "INSERT INTO dispositivos (versao_id, identificador, texto, hash_dispositivo) VALUES (?, ?, ?, ?)",
                    (nova_versao_id, identificador, conteudo, hash_disp)
                )
            
            conn.commit()
            print("  ✅ Inserido no SQLite com Sucesso!")
            
        except Exception as e:
            conn.rollback()
            print(f"  ❌ Erro ao ingerir {nome_arquivo}: {e}")
            
    conn.close()
    
    print("\n---------------------------------------------------------")
    print("Ingestão de texto concluída. Você deve rodar o script:")
    print("python rag/embeddings.py")
    print("para vetorizar esses novos dispositivos e torná-los pesquisáveis pela IA.")
    print("---------------------------------------------------------")

if __name__ == "__main__":
    ingerir_pdfs()
