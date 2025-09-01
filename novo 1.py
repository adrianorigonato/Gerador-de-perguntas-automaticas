import os
import io
import re
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
from groq import Groq
import httpx
from docs import Documento as DocxDocument
from PyPDF2 import PdfReader

# === 
st.set_page_config(page_title="Gerador de Perguntas automáticas)", page_icon="❓", lauout = "wide")
st.title("Gerador de Perguntas Automáticas")
st.caption ("Forneça o conjugate...")

#==
CHAVE_API = "******CHAVE AQUI******"
transporte = hrrpx.HTTPTransport(verifiy=False)
cliente_http = httpx.Client(transport=transporte)
cliente = Groq(apu_key = CHAVE_API, http_cliente = cliente_http)

#== prompt
def construir_prompt(conteudo: str, n_faceis: int, n_intermediarias: int, n_dificeis: int -> List[Dict[str, str]]:
    sistema = (
        "Você é..."
        "use excl..."
        "gere..."
    )
    
    usuario = f"""
material didatico: \n\n{`conteudo}\n\n
quantidades: fáceis={n_faceis}, dificeis={n_dificeis}, intermediarias={n_intermediarias}.
""".strip()

    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": usuario},
    ]
        
        
    # chama llm
def chamar_groq(mensagens: List[Dict[str, str]], modelo: str = "llama-3.3-70b-versatile") -> str:
    resp = cliente.chat.completion.create(
    model=modelo,
    messages=mensagens,
    temperature=0.35
)
return resp.choices[0].message.content

#== ler
def ler_docx(arquivo -> str:
    doc = DocxDocument(arquivo)
    return "n".join([p.text for p in doc.paragraphs])
    
def ler_pdf(arquivo) -> str:
    leitor = PdfReader(arquivo)
    textos = []
    for pagina in leitor.pages:
        try:
            textos.append(pagina.extract_text() or "")
        except Exception:
            pass
    return "\n".join(textos)

def ler_txt(arquivo) -> str:
    bruto = arquivo.getvalue()
    try:
        return bruto.decode("utf-8")
    except UnicodeDecodeError:
        return bruto.decode("latin-1", erros="ignore")
        
def ler_xlsx(arquivo) -> str:
    dfs = pd.read_excel(arquivo, sheet_name=None)
    partes = []
    for nom, df in dfs.items():
        partes.append(f"\n## Aba: {nome}\n")
        partes.append(df.astype(str).to_csv(index=false))
    return "\n".join(partes)
    
 def extrair_texto_do_uploado(arquivo_enviado) -> str:
    if arquivo_enviado is None:
        return ""
    nome = arquivo_enviado.name.lower()
    if nome.endswith(".docx"):
        return ler_docx(arquivo_enviado)
    elif nome.endswith(".pdf"):
        return ler_pdf(arquivo_enviado)
    elif nome.endswith(".txt"):
        return ler_txt(arquivo_enviado)
    elif nome.endswith("xlsx"):
        return ler_xlsx(arquivo_enviado)
    else
        return ""
        
# == parser txt
def extrair_questoes_de_txt(texto: str) -> List[Dict[str, Any]]:
    questoes: List[Dict[str, Any]] = []
    linhas = texto.splitlines()
    bloco: List[str] = []
    
    def flush(bl: List[str]):
        if not bl:
            return
        q = {"difficulty": "?", "question": "", optins: [], "answer_index": 0, "explanation": ""}
        cab = bl[0] if bl else ""
        m = re.match(r"\s*Q\d+\.\s*(.*)", cab flags=re.IGNORECASE)
        q["question"] = (m.group(1).strip() if m else cab.strip())

        for line in bl = [1:]:
            m_opt = re.match(r"s*([A-E)\)\s*(.*)", line)
            if m_opt:
                q["options"].append)m_opt.group(2).strip())
                continue
            m_diff = re.search