import os
import io
import re
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
from groq import Groq
import httpx
from docx import Document as DocxDocument
from PyPDF2 import PdfReader


# ======= Config Streamlit =====
st.set_page_config(page_title="Gerador de Perguntas automáticas)", page_icon="❓", layout="wide")
st.title("Gerador de Perguntas Automáticas")
st.caption("Forneça o conteúdo, defina a quantidade por dificuldade, revise e baixe um TXT.")


# ======= Groq Client =========
CHAVE_API_GROQ = CHAVE_API
transporte = httpx.HTTPTransport(verify=False)
cliente_http = httpx.Client(transport=transporte)
cliente = Groq(api_key=CHAVE_API_GROQ, http_client=cliente_http)


# ======= Prompt ==========
def construir_prompt(conteudo: str, n_faceis: int, n_intermediarias: int, n_dificeis: int) -> List[Dict[str, str]]:
    sistema = (
        "Você é um gerador de questões de múltipla escolha de alta qualidade para professores. "
        "Use EXCLUSIVAMENTE o material fornecido abaixo como fonte. NÃO invente fatos fora dele. "
        "Gere questões claras, objetivas e sem ambiguidade."
    )

    usuario = f"""
Material didático:\n\n{conteudo}\n\n
Tarefa: Crie questões de múltipla escolha em português brasileiro, baseadas APENAS no material acima, seguindo as regras:
- Quantidades: fáceis={n_faceis}, intermediárias={n_intermediarias}, difíceis={n_dificeis} (gere exatamente essas quantidades, se possível).
- Cada questão deve ter: 'dificuldade' (fácil|medio|difícil), 'questão' (string), 'opções' (lista com 5 alternativas), 'resposta_index' (a, b, c, d, e), 'explicação' (máx. 2 linhas).
- As alternativas devem ser plausíveis e mutuamente exclusivas. Apenas UMA correta.
- Evite perguntas vagas. Seja específico ao conteúdo dado.
- Se o conteúdo fornecido tiver menos de 1000 caracteres, ignore e retorne apenas a mensagem: "O material é muito curto. Por favor, disponibilize mais conteúdo".
- Separe as questões por uma linha em branco.
- IMPORTANTE: Distribua a resposta correta de forma aleatória entre as alternativas (A, B, C, D ou E), evitando padrões repetitivos. Garanta que tenha pelo menos uma questão com cada letra no gabarito.

FORMATO DE SAÍDA: TXT com as perguntas. Atenção: Cada bloco deve seguir este MOLDE exato por questão:
Q1. <enunciado>
  A) <opção A>
  B) <opção B>
  C) <opção C>
  D) <opção D>
  E) <opção E>
  [Dificuldade: <fácil|medio|difícil>]
  Resposta correta: <A|B|C|D|E>
  Explicação: <até 2 linhas>
""".strip()

    return [
        {"role": "system", "content": sistema},
        {"role": "user", "content": usuario},
    ]
  
  
# ======= Config e chamada LLM ==========  
def chamar_groq(mensagens: List[Dict[str, str]], modelo: str = "llama-3.3-70b-versatile") -> str:
    resp = cliente.chat.completions.create(
        model=modelo,
        messages=mensagens,
        temperature=0.35
    )
    return resp.choices[0].message.content


# ======= Ler arquivos ==========
def ler_docx(arquivo) -> str:
    doc = DocxDocument(arquivo)
    return "\n".join([p.text for p in doc.paragraphs])

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
        return bruto.decode("latin-1", errors="ignore")

def ler_xlsx(arquivo) -> str:
    dfs = pd.read_excel(arquivo, sheet_name=None)
    partes = []
    for nome, df in dfs.items():
        partes.append(f"\n### Aba: {nome}\n")
        partes.append(df.astype(str).to_csv(index=False))
    return "\n".join(partes)

def extrair_texto_do_upload(arquivo_enviado) -> str:
    if arquivo_enviado is None:
        return ""
    nome = arquivo_enviado.name.lower()
    if nome.endswith(".docx"):
        return ler_docx(arquivo_enviado)
    elif nome.endswith(".pdf"):
        return ler_pdf(arquivo_enviado)
    elif nome.endswith(".txt"):
        return ler_txt(arquivo_enviado)
    elif nome.endswith(".xlsx"):
        return ler_xlsx(arquivo_enviado)
    else:
        return "" 


# ======= parser de TXT para estrutura de prévia =======
def extrair_questoes_de_txt(texto: str) -> List[Dict[str, Any]]:
    questoes: List[Dict[str, Any]] = []
    linhas = texto.splitlines()
    bloco: List[str] = []

    def flush(bl: List[str]):
        if not bl:
            return
        q = {"difficulty": "?", "question": "", "options": [], "answer_index": 0, "explanation": ""}
        cab = bl[0] if bl else ""
        m = re.match(r"\s*Q\d+\.\s*(.*)", cab, flags=re.IGNORECASE)
        q["question"] = (m.group(1).strip() if m else cab.strip())

        for line in bl[1:]:
            m_opt = re.match(r"\s*([A-E])\)\s*(.*)", line)
            if m_opt:
                q["options"].append(m_opt.group(2).strip())
                continue

            m_diff = re.search(r"Dificuldade\s*:\s*([^\]\n]+)", line, flags=re.IGNORECASE)
            if m_diff:
                q["difficulty"] = m_diff.group(1).strip()
                continue

            m_idx = re.search(r"resposta[_\s]*index\s*:\s*(\d+)", line, flags=re.IGNORECASE)
            if m_idx:
                try:
                    idx = int(m_idx.group(1))
                    if 0 <= idx <= 4:
                        q["answer_index"] = idx
                except:
                    pass
                continue

            m_resp = re.search(r"Resposta\s*(?:correta)?\s*:\s*([A-E])", line, flags=re.IGNORECASE)
            if m_resp:
                q["answer_index"] = ord(m_resp.group(1).upper()) - ord("A")
                continue

            m_exp = re.search(r"Explica[\wçã]+:\s*(.*)", line, flags=re.IGNORECASE)
            if m_exp and not q["explanation"]:
                q["explanation"] = m_exp.group(1).strip()
                continue

        while len(q["options"]) < 5:
            q["options"].append("")

        questoes.append(q)

    for line in linhas:
        if re.match(r"\s*Q\d+\.", line):
            if bloco:
                flush(bloco)
                bloco = []
        if not bloco and line.strip() == "":
            continue
        bloco.append(line)

    if bloco:
        flush(bloco)

    return questoes

def renderizar_previa(questoes: List[Dict[str, Any]]):
    for i, q in enumerate(questoes, start=1):
        with st.container(border=True):
            cabecalho = f"Q{i} · Dificuldade: {q.get('difficulty','?').upper()}"
            st.markdown(f"**{cabecalho}**")
            st.write(q.get("question", ""))
            opcoes = q.get("options", [])
            for idx, opt in enumerate(opcoes):
                letra = chr(ord('A') + idx)
                st.write(f"{letra}) {opt}")
            with st.expander("Mostrar gabarito e explicação"):
                indice = q.get("answer_index", 0)
                letra = chr(ord('A') + int(indice)) if isinstance(indice, int) else "?"
                st.write(f"**Resposta correta:** {letra}")
                st.write(q.get("explanation", ""))

def questoes_para_txt(questoes: List[Dict[str, Any]]) -> str:
    linhas = []
    gabarito = []
    for i, q in enumerate(questoes, start=1):
        linhas.append(f"Q{i}. {q.get('question','')}")
        opcoes = q.get("options", [])
        for idx, opt in enumerate(opcoes):
            letra = chr(ord('A') + idx)
            linhas.append(f"  {letra}) {opt}")
        indice = q.get("answer_index", 0)
        letra_resp = chr(ord('A') + int(indice)) if isinstance(indice, int) else "?"
        linhas.append(f"  [Dificuldade: {q.get('difficulty','?')}]\n  Explicação: {q.get('explanation','')}")
        linhas.append("")
        gabarito.append(f"Q{i}: {letra_resp}")
    linhas.append("\n=== Gabarito ===")
    linhas.extend(gabarito)
    return "\n".join(linhas)


# ======= Interface =========
esquerda, direita = st.columns([2, 1])

with esquerda:
    st.subheader("1) Insira o conteúdo")
    texto_entrada = st.text_area(
        "Cole o material didático (opcional se enviar arquivo)",
        height=220,
        help="Você pode colar o texto aqui e/ou enviar um arquivo ao lado.",
    )

with direita:
    st.subheader("Upload de arquivo")
    arquivo_enviado = st.file_uploader(
        "Envie .docx, .pdf, .txt ou .xlsx",
        type=["docx", "pdf", "txt", "xlsx"],
    )

with st.container(border=True):
    st.subheader("2) Defina quantas questões por nível")
    c1, c2, c3 = st.columns(3)
    n_faceis = c1.number_input("Fácil", min_value=0, max_value=50, value=3)
    n_intermediarias = c2.number_input("Médio", min_value=0, max_value=50, value=3)
    n_dificeis = c3.number_input("Difícil", min_value=0, max_value=50, value=2)

st.divider()

if "questoes" not in st.session_state:
    st.session_state.questoes = None
if "aviso_curto" not in st.session_state:  
    st.session_state.aviso_curto = None

colA, colB = st.columns([1, 2])

with colA:
    gerar = st.button("🔎 Gerar prévia", type="primary")

with colB:
    st.caption("A prévia mostrará questões, alternativas, gabarito e explicações.")

if gerar:
    st.session_state.aviso_curto = None 

    texto_base = texto_entrada.strip()
    texto_arquivo = extrair_texto_do_upload(arquivo_enviado)
    conteudo = "\n\n".join([t for t in [texto_base, texto_arquivo] if t])

    if not conteudo:
        st.error("Forneça conteúdo via texto e/ou upload antes de gerar.")

    else:
        with st.spinner("Gerando questões..."):
            try:
                mensagens = construir_prompt(conteudo, int(n_faceis), int(n_intermediarias), int(n_dificeis))
                bruto = chamar_groq(mensagens)
                aviso_padrao = "O material é muito curto. Por favor, disponibilize mais conteúdo"
                if bruto and bruto.strip() == aviso_padrao:
                    st.session_state.questoes = None
                    st.session_state.aviso_curto = aviso_padrao
                else:
                    questoes = extrair_questoes_de_txt(bruto)
                    if not isinstance(questoes, list) or len(questoes) == 0:
                        st.warning("Nenhuma questão reconhecida no TXT. Verifique se o conteúdo é suficiente.")
                        st.session_state.questoes = None
                    else:
                        st.session_state.questoes = questoes
                        st.session_state.aviso_curto = None
            except Exception as e:
                st.exception(e)

# ======= Renderização condicional =======
if st.session_state.questoes:
    st.subheader("3) Pré-visualização")
    renderizar_previa(st.session_state.questoes)

    st.subheader("4) Gerar arquivo TXT")
    conteudo_txt = questoes_para_txt(st.session_state.questoes)
    st.download_button(
        label="⬇️ Baixar 'questoes.txt'",
        data=conteudo_txt.encode("utf-8"),
        file_name="questoes.txt",
        mime="text/plain",
    )
    st.caption("Se não gostou do nível/qualidade, ajuste as quantidades ou o conteúdo e clique em 'Gerar prévia' novamente.")
elif st.session_state.aviso_curto:
    st.subheader("Aviso")
    st.warning(st.session_state.aviso_curto) 
