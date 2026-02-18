import streamlit as st
import pandas as pd
import sqlite3
import calendar
from datetime import datetime, date, time
import os
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from fpdf import FPDF

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Portal da Ala", page_icon="⛪", layout="wide")

# --- CAMINHOS ABSOLUTOS ---
BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, 'igreja.db')
POSTS_DIR = os.path.join(BASE_DIR, 'posts')

if not os.path.exists(POSTS_DIR):
    os.makedirs(POSTS_DIR)

# --- CSS CUSTOMIZADO (VISUAL) ---
st.markdown("""
    <style>
    /* Estilos Gerais */
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 800 !important; font-size: 1.8rem !important; }
    [data-testid="stMetricLabel"] { color: #F0F2F6 !important; font-weight: bold !important; }
    
    /* Cartões Gradiente */
    div[data-testid="stMetric"], .ind-card, .citation-box { 
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); 
        color: white;
    }
    
    .comunicado-card { padding: 20px; border-radius: 15px; border-left: 8px solid #1976d2; background-color: #f8f9fa; margin-bottom: 25px; color: #000; }
    
    /* Calendário e Outros Elementos */
    .cal-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; max-width: 450px; margin: auto; text-align: center; }
    .cal-header { font-weight: bold; color: #1976d2; margin-bottom: 10px; text-transform: uppercase; font-size: 1.2rem; }
    .cal-weekday { font-size: 0.8rem; color: #666; font-weight: bold; padding: 5px; }
    .cal-day { padding: 10px; border-radius: 5px; background-color: #ffffff; border: 1px solid #e0e0e0; min-height: 40px; display: flex; align-items: center; justify-content: center; color: #000; }
    .cal-active { background-color: #1976d2 !important; color: white !important; font-weight: bold; }
    .cal-today { border: 2px solid #ff4b4b; color: #ff4b4b; font-weight: bold; }
    .cal-empty { background-color: transparent; border: none; }

    .cal-giant-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; width: 100%; text-align: center; }
    .cal-giant-header { font-weight: bold; color: #1976d2; margin-bottom: 15px; text-transform: uppercase; font-size: 1.8rem; text-align: center; }
    .cal-giant-day { min-height: 110px; padding: 10px; border-radius: 10px; background: white; border: 1px solid #ddd; display: flex; flex-direction: column; align-items: center; color: #333; }
    .cal-giant-active { background-color: #e3f2fd !important; border: 2px solid #1976d2 !important; }
    .event-dot { width: 10px; height: 10px; background-color: #1976d2; border-radius: 50%; margin-top: 8px; }
    
    /* Indicadores */
    .ind-card { text-align: center; margin-bottom: 10px; height: 100%; display: flex; flex-direction: column; justify-content: center; }
    .ind-title { font-size: 0.9rem; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; opacity: 0.9; }
    .ind-value { font-size: 2.2rem; font-weight: 800; margin: 5px 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5); }
    .ind-meta { font-size: 0.8rem; opacity: 0.8; font-weight: 500; }
    .txt-green { color: #69f0ae !important; }
    .txt-yellow { color: #ffeb3b !important; }
    .txt-red { color: #ff8a80 !important; }

    /* Legenda */
    .legenda-container { display: flex; gap: 15px; margin-bottom: 20px; justify-content: flex-end; font-size: 0.8rem; color: #555; font-weight: bold; }
    .dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 5px; }
    
    .citation-box { text-align: center; font-style: italic; margin-top: 30px; font-size: 1.1rem; }
    .editor-box { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-top: 20px; margin-bottom: 20px; }
    
    [data-testid="stForm"] { border: none; padding: 0; }
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND SQLITE ---
def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Tabelas Core
    c.execute('CREATE TABLE IF NOT EXISTS comunicados (id INTEGER PRIMARY KEY AUTOINCREMENT, data_postagem TEXT, titulo TEXT, mensagem TEXT, autor TEXT, link TEXT, imagem TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS agenda (id INTEGER PRIMARY KEY AUTOINCREMENT, data_evento TEXT, titulo TEXT, descricao TEXT, local TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tarefas_bispado (id INTEGER PRIMARY KEY AUTOINCREMENT, data_criacao TEXT, tarefa TEXT, status TEXT, prioridade TEXT, responsavel TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS agenda_bispado (id INTEGER PRIMARY KEY AUTOINCREMENT, data_agenda TEXT, horario TEXT, nome_compromisso TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS planejamento_lideranca (id INTEGER PRIMARY KEY AUTOINCREMENT, organizacao TEXT, atividade TEXT, data_planejada TEXT, horario_inicio TEXT, horario_fim TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS indicadores (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, indicador TEXT, atual INTEGER, meta INTEGER)')
    # Tabelas Financeiras
    c.execute('CREATE TABLE IF NOT EXISTS financeiro_caravanas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome_irmao TEXT, mes_caravana TEXT, valor_pago REAL, valor_total REAL, quitado INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS orcamentos_iniciais (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT UNIQUE, valor_inicial REAL)')
    c.execute('CREATE TABLE IF NOT EXISTS despesas (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, descricao TEXT, valor REAL, data_despesa TEXT, responsavel TEXT)')

    # Seeding Inicial
    c.execute('SELECT count(*) FROM indicadores')
    if c.fetchone()[0] == 0:
        dados_iniciais = [("VIVER", "Frequência Sacramental", 109, 110), ("VIVER", "Membros Participantes", 102, 115), ("CUIDAR NECESSITADOS", "Membros Retornando", 0, 10), ("CUIDAR NECESSITADOS", "Membros Jejuando", 20, 34), ("CONVIDAR TODOS", "Batismos", 4, 20), ("CONVIDAR TODOS", "Missionários", 1, 2), ("UNIR FAMÍLIAS", "Membros com Investidura", 49, 50), ("UNIR FAMÍLIAS", "Membros sem Investidura", 26, 30)]
        c.executemany('INSERT INTO indicadores (categoria, indicador, atual, meta) VALUES (?,?,?,?)', dados_iniciais)
    
    c.execute('SELECT count(*) FROM orcamentos_iniciais')
    if c.fetchone()[0] == 0:
        orc_iniciais = [("Administração", 1000.0), ("Primária", 600.0), ("Moças", 500.0), ("Rapazes", 500.0), ("Soc. Socorro", 350.0), ("Seminário", 300.0), ("Obra Missionária", 300.0), ("JAS", 250.0), ("Quórum", 200.0)]
        c.executemany('INSERT OR IGNORE INTO orcamentos_iniciais (categoria, valor_inicial) VALUES (?,?)', orc_iniciais)

    conn.commit(); conn.close()

# --- FUNÇÕES GERAIS ---
def adicionar_comunicado(t, m, a, l, img):
    conn = get_connection(); c = conn.cursor()
    c.execute('INSERT INTO comunicados (data_postagem, titulo, mensagem, autor, link, imagem) VALUES (?,?,?,?,?,?)', (datetime.now().strftime("%Y-%m-%d"), t, m, a, l, img))
    conn.commit(); conn.close()

def adicionar_planejamento_lideranca(org, atv, data_p, h_ini, h_fim):
    conn = get_connection(); c = conn.cursor()
    c.execute('INSERT INTO planejamento_lideranca (organizacao, atividade, data_planejada, horario_inicio, horario_fim) VALUES (?,?,?,?,?)', (org, atv, data_p, h_ini, h_fim))
    conn.commit(); conn.close()

def adicionar_tarefa_bispado(tarefa, prioridade, responsavel, status):
    conn = get_connection(); c = conn.cursor()
    c.execute('INSERT INTO tarefas_bispado (data_criacao, tarefa, status, prioridade, responsavel) VALUES (?, ?, ?, ?, ?)', (datetime.now().strftime("%Y-%m-%d"), tarefa, status, prioridade, responsavel))
    conn.commit(); conn.close()

def atualizar_status_tarefa(id_item, novo_status):
    conn = get_connection(); c = conn.cursor()
    c.execute('UPDATE tarefas_bispado SET status = ? WHERE id = ?', (novo_status, id_item))
    conn.commit(); conn.close()

def adicionar_agenda_bispado(data, horario, nome, status):
    conn = get_connection(); c = conn.cursor()
    c.execute('INSERT INTO agenda_bispado (data_agenda, horario, nome_compromisso, status) VALUES (?, ?, ?, ?)', (data, horario, nome, status))
    conn.commit(); conn.close()

def atualizar_indicador(id_item, novo_atual, nova_meta):
    conn = get_connection(); c = conn.cursor()
    c.execute('UPDATE indicadores SET atual = ?, meta = ? WHERE id = ?', (novo_atual, nova_meta, id_item))
    conn.commit(); conn.close()

def excluir_registro(tabela, id_item, imagem_path=None):
    conn = get_connection(); c = conn.cursor()
    if imagem_path and os.path.exists(str(imagem_path)):
        try: os.remove(imagem_path)
        except: pass
    c.execute(f'DELETE FROM {tabela} WHERE id = ?', (id_item,))
    conn.commit(); conn.close()

def ler_dados(tabela, ordem="id DESC"):
    conn = get_connection()
    try: df = pd.read_sql_query(f"SELECT * FROM {tabela} ORDER BY {ordem}", conn)
    except: df = pd.DataFrame()
    conn.close(); return df

# --- CARAVANA ---
def adicionar_caravana_simples(nome, mes, total, pago):
    quitado = 1 if pago >= total else 0
    conn = get_connection(); c = conn.cursor()
    c.execute('INSERT INTO financeiro_caravanas (nome_irmao, mes_caravana, valor_pago, valor_total, quitado) VALUES (?, ?, ?, ?, ?)', (nome, mes, pago, total, quitado))
    conn.commit(); conn.close()

def atualizar_lote_caravana(df_edited):
    conn = get_connection(); c = conn.cursor()
    for index, row in df_edited.iterrows():
        c.execute('UPDATE financeiro_caravanas SET valor_pago = ?, valor_total = ?, quitado = ? WHERE id = ?', 
                  (row['valor_pago'], row['valor_total'], 1 if row['quitado'] else 0, row['id']))
    conn.commit(); conn.close()

# --- ORÇAMENTO ---
def adicionar_despesa(categoria, descricao, valor, data, responsavel):
    conn = get_connection(); c = conn.cursor()
    c.execute('INSERT INTO despesas (categoria, descricao, valor, data_despesa, responsavel) VALUES (?, ?, ?, ?, ?)', (categoria, descricao, valor, data, responsavel))
    conn.commit(); conn.close()

def get_resumo_orcamento():
    conn = get_connection()
    df_ini = pd.read_sql_query("SELECT * FROM orcamentos_iniciais", conn)
    df_desp = pd.read_sql_query("SELECT * FROM despesas", conn)
    conn.close()
    
    resumo = []
    total_orcado = df_ini['valor_inicial'].sum() if not df_ini.empty else 0
    total_gasto = df_desp['valor'].sum() if not df_desp.empty else 0
    
    for _, row in df_ini.iterrows():
        cat = row['categoria']
        ini = row['valor_inicial']
        gasto = 0
        if not df_desp.empty:
            gasto = df_desp[df_desp['categoria'] == cat]['valor'].sum()
        saldo = ini - gasto
        pct = (gasto / ini * 100) if ini > 0 else 0
        resumo.append({'Categoria': cat, 'Orçamento': ini, 'Gasto': gasto, 'Saldo': saldo, '% Uso': pct})
        
    return pd.DataFrame(resumo), total_orcado, total_gasto

# --- HELPER VISUAL ---
def render_indicador_card(titulo, atual, meta):
    if meta == 0: pct = 100 
    else: pct = (atual / meta) * 100
    text_class = "txt-red"
    if atual >= meta: text_class = "txt-green"
    elif pct >= 70: text_class = "txt-yellow"
    return f"<div class='ind-card'><div class='ind-title'>{titulo}</div><div class='ind-value {text_class}'>{atual}</div><div class='ind-meta'>Meta: {meta}</div></div>"

# --- EXPORTAÇÃO EXCEL E PDF SIMPLES ---
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer: df.to_excel(writer, index=False)
    return output.getvalue()

def to_pdf(df, titulo="Relatório"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=titulo, ln=True, align='C'); pdf.ln(10)
    pdf.set_font("Arial", size=10)
    col_width = 190 / len(df.columns)
    pdf.set_font("Arial", 'B', 10)
    for col in df.columns: pdf.cell(col_width, 10, str(col)[:15], 1, 0, 'C')
    pdf.ln()
    pdf.set_font("Arial", '', 10)
    for _, row in df.iterrows():
        for col in df.columns: pdf.cell(col_width, 10, str(row[col])[:15], 1, 0, 'C')
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')

# --- NOVAS FUNÇÕES PDF (CALENDÁRIO E ORÇAMENTO COMPLETO) ---

def gerar_pdf_calendario(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Calendario de Atividades da Ala", 0, 1, "C")
    pdf.ln(5)
    
    # Cabeçalho da Tabela
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 10, "Data", 1, 0, 'C', 1)
    pdf.cell(20, 10, "Hora", 1, 0, 'C', 1)
    pdf.cell(50, 10, "Organizacao", 1, 0, 'C', 1)
    pdf.cell(90, 10, "Atividade", 1, 0, 'C', 1)
    pdf.ln()
    
    # Corpo da Tabela
    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        # Tratamento simples de encoding para remover acentos que o FPDF padrão não aceita
        org_clean = str(row['organizacao']).encode('latin-1', 'replace').decode('latin-1')
        atv_clean = str(row['atividade']).encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(30, 10, str(row['data_planejada']), 1)
        pdf.cell(20, 10, str(row['horario_inicio']), 1)
        pdf.cell(50, 10, org_clean[:25], 1) # Corta texto longo
        pdf.cell(90, 10, atv_clean[:45], 1)
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

def gerar_pdf_orcamento_completo(df_resumo, df_extrato):
    pdf = FPDF()
    pdf.add_page()
    
    # Título Principal
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Relatorio Orcamentario", 0, 1, "C")
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 5, f"Gerado em: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, "C")
    pdf.ln(10)

    # 1. Tabela de Resumo (Saldos)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. Resumo por Organizacao", 0, 1)
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(60, 10, "Categoria", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Orcamento", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Gasto", 1, 0, 'C', 1)
    pdf.cell(40, 10, "Saldo", 1, 0, 'C', 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    for _, row in df_resumo.iterrows():
        cat_clean = str(row['Categoria']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(60, 10, cat_clean, 1)
        pdf.cell(40, 10, f"R$ {row['Orçamento']:.2f}", 1, 0, 'R')
        pdf.cell(40, 10, f"R$ {row['Gasto']:.2f}", 1, 0, 'R')
        pdf.cell(40, 10, f"R$ {row['Saldo']:.2f}", 1, 0, 'R')
        pdf.ln()

    pdf.ln(10)

    # 2. Tabela de Extrato (Despesas)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. Historico de Despesas", 0, 1)
    
    if not df_extrato.empty:
        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(25, 8, "Data", 1, 0, 'C', 1)
        pdf.cell(40, 8, "Categoria", 1, 0, 'C', 1)
        pdf.cell(85, 8, "Descricao", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Valor", 1, 0, 'C', 1)
        pdf.ln()
        
        pdf.set_font("Arial", "", 9)
        for _, row in df_extrato.iterrows():
            cat_clean = str(row['categoria']).encode('latin-1', 'replace').decode('latin-1')
            desc_clean = str(row['descricao']).encode('latin-1', 'replace').decode('latin-1')
            
            pdf.cell(25, 8, str(row['data_despesa']), 1)
            pdf.cell(40, 8, cat_clean[:20], 1)
            pdf.cell(85, 8, desc_clean[:45], 1)
            pdf.cell(30, 8, f"R$ {row['valor']:.2f}", 1, 0, 'R')
            pdf.ln()
    else:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, "Nenhuma despesa registrada no periodo.", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- COMPONENTES UI (INCLUINDO TODAS AS FUNÇÕES) ---

def gerar_calendario_html(ano, mes, datas_ativas):
    dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    meses_pt = {1:"Janeiro", 2:"Fevereiro", 3:"Março", 4:"Abril", 5:"Maio", 6:"Junho", 7:"Julho", 8:"Agosto", 9:"Setembro", 10:"Outubro", 11:"Novembro", 12:"Dezembro"}
    cal = calendar.Calendar(firstweekday=0)
    mes_matriz = cal.monthdayscalendar(ano, mes)
    html = f"<div class='cal-header'>{meses_pt[mes]} {ano}</div><div class='cal-container'>"
    for ds in dias_semana: html += f"<div class='cal-weekday'>{ds}</div>"
    for semana in mes_matriz:
        for dia in semana:
            if dia == 0: html += "<div class='cal-day cal-empty'></div>"
            else:
                data_str = f"{ano}-{mes:02d}-{dia:02d}"
                classe = "cal-day"
                if data_str in datas_ativas: classe += " cal-active"
                if date.today().strftime("%Y-%m-%d") == data_str: classe += " cal-today"
                html += f"<div class='{classe}'>{dia}</div>"
    return html + "</div>"

def gerar_calendario_gigante(ano, mes, df_atividades):
    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    cal = calendar.Calendar(firstweekday=0)
    mes_matriz = cal.monthdayscalendar(ano, mes)
    html = f"<div class='cal-giant-container'>"
    for ds in dias_semana: html += f"<div style='font-weight:bold;'>{ds}</div>"
    for semana in mes_matriz:
        for dia in semana:
            if dia == 0: html += "<div></div>"
            else:
                data_str = f"{ano}-{mes:02d}-{dia:02d}"
                atv = pd.DataFrame()
                if not df_atividades.empty and 'data_planejada' in df_atividades.columns:
                    atv = df_atividades[df_atividades['data_planejada'] == data_str]
                classe = "cal-giant-day"
                tooltip = f"Dia {dia}"
                if not atv.empty: 
                    classe += " cal-giant-active"
                    info = " | ".join([f"{r['organizacao']}: {r['atividade']}" for _, r in atv.iterrows()])
                    tooltip = f"Atividades: {info}"
                html += f"<div class='{classe}' title='{tooltip}'><div>{dia}</div>"
                if not atv.empty: html += "<div class='event-dot'></div>"
                html += "</div>"
    return html + "</div>"

def exibir_indicadores_profeticos(permitir_edicao=False):
    st.header("📊 Prioridades Proféticas - Brasil")
    st.markdown("""<div class='legenda-container'><div><span class='dot' style='background-color:#69f0ae;'></span>Meta Atingida</div><div><span class='dot' style='background-color:#ffeb3b;'></span>Próximo (>70%)</div><div><span class='dot' style='background-color:#ff8a80;'></span>Atenção (<70%)</div></div>""", unsafe_allow_html=True)
    df_ind = ler_dados("indicadores", "id ASC")
    if df_ind.empty: st.warning("Nenhum indicador encontrado."); return
    for i in range(0, len(df_ind), 4):
        cols = st.columns(4)
        batch = df_ind.iloc[i:i+4]
        for idx, (_, row) in enumerate(batch.iterrows()):
            card_html = render_indicador_card(row['indicador'], row['atual'], row['meta'])
            cols[idx].markdown(card_html, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
    st.divider()
    fig = go.Figure(data=[go.Bar(name='Atual', x=df_ind['indicador'], y=df_ind['atual'], marker_color='#1e3a8a'), go.Bar(name='Meta', x=df_ind['indicador'], y=df_ind['meta'], marker_color='#93c5fd')])
    st.plotly_chart(fig, width="stretch")
    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_ind[['categoria', 'indicador', 'atual', 'meta']], width="stretch", hide_index=True)
    if permitir_edicao:
        st.markdown("### 📝 Atualizar Metas e Resultados")
        st.markdown("<div class='editor-box'>", unsafe_allow_html=True)
        col_sel, col_val, col_meta, col_btn = st.columns([3, 2, 2, 2])
        with col_sel:
            lista_indicadores = df_ind['indicador'].unique()
            indicador_selecionado = st.selectbox("Selecione o Indicador:", lista_indicadores)
        dados_atuais = df_ind[df_ind['indicador'] == indicador_selecionado].iloc[0]
        id_atual = dados_atuais['id']
        with st.form(key=f"form_edicao_{id_atual}"):
            c1, c2, c3 = st.columns([1, 1, 1])
            with c1: novo_atual = st.number_input("Valor Atual", value=int(dados_atuais['atual']), step=1, key=f"input_atual_{id_atual}")
            with c2: nova_meta = st.number_input("Meta", value=int(dados_atuais['meta']), step=1, key=f"input_meta_{id_atual}")
            with c3:
                st.write(""); st.write("") 
                submit = st.form_submit_button("💾 Salvar Alteração", type="primary")
            if submit:
                atualizar_indicador(int(id_atual), novo_atual, nova_meta)
                st.success(f"'{indicador_selecionado}' atualizado!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("""<div class='citation-box'>"Pois eis que esta é minha obra e minha glória: Levar a efeito a imortalidade e a vida eterna do homem."<br><br><strong>(Moisés 1:39)</strong></div>""", unsafe_allow_html=True)

def exibir_orcamento():
    st.subheader("💰 Gestão Orçamentária da Ala")
    df_resumo, total_orcado, total_gasto = get_resumo_orcamento()
    saldo_total = total_orcado - total_gasto
    
    # Botão de Exportação PDF no Topo
    try:
        df_extrato = ler_dados("despesas")
        pdf_bytes = gerar_pdf_orcamento_completo(df_resumo, df_extrato)
        st.download_button("📄 Baixar Relatório Financeiro (PDF)", data=pdf_bytes, file_name=f"Orcamento_Ala_{datetime.now().strftime('%Y-%m-%d')}.pdf", mime="application/pdf", type="primary")
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")

    c1, c2, c3 = st.columns(3)
    c1.metric("Orçamento Total", f"R$ {total_orcado:,.2f}")
    c2.metric("Valor Gasto", f"R$ {total_gasto:,.2f}", delta_color="inverse")
    c3.metric("Saldo Disponível", f"R$ {saldo_total:,.2f}")
    st.divider()
    st.markdown("### 📝 Lançar Nova Despesa")
    with st.form("form_despesa", clear_on_submit=True):
        col_cat, col_desc, col_val, col_resp = st.columns([2, 3, 2, 2])
        categorias = df_resumo['Categoria'].tolist() if not df_resumo.empty else []
        cat_sel = col_cat.selectbox("Organização", categorias)
        desc = col_desc.text_input("Descrição")
        valor = col_val.number_input("Valor (R$)", min_value=0.01, step=10.0)
        resp = col_resp.text_input("Responsável")
        if st.form_submit_button("💾 Registrar Despesa", type="primary"):
            if desc and valor > 0:
                adicionar_despesa(cat_sel, desc, valor, datetime.now().strftime("%Y-%m-%d"), resp)
                st.success("Registrado!"); st.rerun()
            else: st.warning("Preencha os campos.")
    st.divider()
    st.markdown("### 📊 Saldo por Organização")
    if not df_resumo.empty:
        fig = go.Figure(data=[go.Bar(name='Orçamento', x=df_resumo['Categoria'], y=df_resumo['Orçamento'], marker_color='#1e3a8a'), go.Bar(name='Gasto', x=df_resumo['Categoria'], y=df_resumo['Gasto'], marker_color='#ef5350')])
        fig.update_layout(barmode='group', height=400); st.plotly_chart(fig, width="stretch")
        st.dataframe(df_resumo.style.format({"Orçamento": "R$ {:.2f}", "Gasto": "R$ {:.2f}", "Saldo": "R$ {:.2f}", "% Uso": "{:.1f}%"}).bar(subset=["% Uso"], color='#90caf9', vmin=0, vmax=100), width="stretch", hide_index=True)
    st.markdown("### 📜 Histórico")
    if not df_extrato.empty:
        st.dataframe(df_extrato[['data_despesa', 'categoria', 'descricao', 'valor', 'responsavel']], width="stretch", hide_index=True)
        with st.expander("🗑️ Excluir Lançamento"):
            for _, r in df_extrato.iterrows():
                if st.button(f"Excluir: {r['descricao']} (R$ {r['valor']})", key=f"del_desp_{r['id']}"): excluir_registro('despesas', r['id']); st.rerun()
    else: st.info("Sem lançamentos.")

init_db()

# --- SIDEBAR E LOGIN ---
if os.path.exists("logo.png"): st.sidebar.image("logo.png", width=100)
menu = st.sidebar.radio("Navegar", ["📢 Mural de Avisos", "📅 Calendário da Ala", "🔒 Líderes e Secretários", "🏢 Painel do Bispado"])

def verificar_acesso(tipo):
    senha = st.sidebar.text_input(f"Senha {tipo.capitalize()}", type="password", key=f"pwd_{tipo}")
    senha_correta = "admin123" if tipo == "lideranca" else "bispo2026"
    if senha.strip() == senha_correta: return True
    elif senha: st.sidebar.error("Senha Incorreta")
    return False

if menu == "📢 Mural de Avisos":
    st.title("📢 Mural de Avisos")
    df = ler_dados("comunicados")
    for _, r in df.iterrows():
        st.markdown(f"<div class='comunicado-card'><h3>📌 {r['titulo']}</h3><p>{r['data_postagem']}</p></div>", unsafe_allow_html=True)
        if r.get('imagem') and os.path.exists(str(r['imagem'])): st.image(r['imagem'], width="stretch")
        st.write(r['mensagem']); st.divider()

elif menu == "📅 Calendário da Ala":
    st.title("📅 Calendário da Ala")
    df_p = ler_dados("planejamento_lideranca", "data_planejada ASC")
    mes_ref = st.selectbox("Mês", range(1, 13), index=datetime.now().month-1)
    st.markdown(gerar_calendario_gigante(2026, mes_ref, df_p), unsafe_allow_html=True)

elif menu == "🔒 Líderes e Secretários":
    if verificar_acesso("lideranca"):
        if os.path.exists("lideres.png"): st.image("lideres.png", width="stretch")
        t1, t2, t3, t4 = st.tabs(["📝 Postar", "🗑️ Gerenciar", "📅 Planejamento", "📊 Indicadores"])
        with t1:
            with st.form("post"):
                t = st.text_input("Título"); m = st.text_area("Mensagem"); a = st.text_input("Autor")
                l = st.text_input("Link"); img = st.file_uploader("Imagem", type=['jpg','png'])
                if st.form_submit_button("Publicar"):
                    img_path = None
                    if img:
                        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{img.name}"
                        img_path = os.path.join(POSTS_DIR, filename)
                        with open(img_path, "wb") as f: f.write(img.getbuffer())
                    adicionar_comunicado(t, m, a, l, img_path); st.rerun()
        with t2:
            df_m = ler_dados("comunicados")
            if not df_m.empty:
                for _, r in df_m.iterrows():
                    col1, col2 = st.columns([0.8, 0.2])
                    col1.write(f"📌 {r['titulo']}")
                    if col2.button("Remover", key=f"rm_{r['id']}"): excluir_registro('comunicados', r['id'], r.get('imagem')); st.rerun()
            else: st.info("Sem comunicados.")
        with t3:
            with st.form("f_plan_fixed", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                org = c1.selectbox("Org", ["Quórum de Elderes", "Sociedade de Socorro", "Moças", "Rapazes", "Primária", "Obra Missionária"])
                atv = c2.text_input("Atividade"); dt = c3.date_input("Data", date.today())
                ch1, ch2 = st.columns(2)
                h_inicio = ch1.time_input("Início", value=time(19, 0)); h_fim = ch2.time_input("Término", value=time(20, 30))
                if st.form_submit_button("Salvar"): adicionar_planejamento_lideranca(org, atv, dt.strftime("%Y-%m-%d"), h_inicio.strftime("%H:%M"), h_fim.strftime("%H:%M")); st.rerun()
            st.divider()
            df_p = ler_dados("planejamento_lideranca", "data_planejada ASC")
            
            # --- CORREÇÃO: BOTÃO MOVIDO PARA CÁ (TOPO) ---
            if not df_p.empty:
                col_btn, _ = st.columns([1, 4])
                with col_btn:
                    try:
                        pdf_cal = gerar_pdf_calendario(df_p)
                        st.download_button("📄 Baixar Calendário (PDF)", data=pdf_cal, file_name=f"Calendario_Ala_2026.pdf", mime="application/pdf")
                    except Exception as e: st.error(f"Erro PDF: {e}")
            # ---------------------------------------------

            col_visual, col_lista = st.columns([0.5, 0.5])
            with col_visual:
                m_s = st.selectbox("Mês", range(1, 13), index=date.today().month-1, key="plan_month")
                datas = df_p['data_planejada'].tolist() if not df_p.empty else []
                st.markdown(gerar_calendario_html(2026, m_s, datas), unsafe_allow_html=True)
            with col_lista:
                st.write(f"### {m_s}/2026")
                if not df_p.empty:
                    df_f = df_p[df_p['data_planejada'].str.contains(f"2026-{m_s:02d}", na=False)]
                    for _, r in df_f.iterrows():
                        ci, cb = st.columns([0.8, 0.2])
                        ci.write(f"**{r['data_planejada']}** - {r['organizacao']}")
                        if cb.button("🗑️", key=f"del_plan_{r['id']}"): excluir_registro('planejamento_lideranca', r['id']); st.rerun()
        with t4: exibir_indicadores_profeticos(permitir_edicao=False)

elif menu == "🏢 Painel do Bispado":
    if verificar_acesso("bispado"):
        if os.path.exists("bispado.png"): st.image("bispado.png", width="stretch")
        tab_tarefas, tab_agenda, tab_caravana, tab_orc, tab_ind = st.tabs(["🎯 Tarefas", "📅 Agenda", "🚌 Caravanas", "💰 Orçamento", "📊 Indicadores"])
        
        with tab_tarefas:
            with st.form("f_meta", clear_on_submit=True):
                mt = st.text_input("Tarefa"); c_inp = st.columns(3)
                pr = c_inp[0].selectbox("Prioridade", ["Alta","Média","Baixa"]); rs = c_inp[1].text_input("Responsável"); stt = c_inp[2].selectbox("Status", ["Pendente", "Concluido"])
                if st.form_submit_button("Salvar"): 
                    if mt and rs: adicionar_tarefa_bispado(mt, pr, rs, stt); st.rerun()
            st.divider()
            df_t = ler_dados("tarefas_bispado")
            if not df_t.empty:
                st.dataframe(df_t[['tarefa', 'prioridade', 'responsavel', 'status']], width="stretch", hide_index=True)
                with st.expander("⚙️ Gerenciar"):
                    for _, r in df_t.iterrows():
                        c_task, c_btn_status, c_btn_del = st.columns([0.6, 0.2, 0.2])
                        c_task.write(f"**{r['tarefa']}**")
                        if r['status'] == "Pendente":
                            if c_btn_status.button("✅", key=f"done_{r['id']}"): atualizar_status_tarefa(r['id'], "Concluido"); st.rerun()
                        if c_btn_del.button("🗑️", key=f"t_del_{r['id']}"): excluir_registro('tarefas_bispado', r['id']); st.rerun()
        with tab_agenda:
            with st.form("f_bis"):
                d = st.date_input("Data"); h = st.time_input("Hora"); n = st.text_input("Assunto")
                if st.form_submit_button("Agendar"): adicionar_agenda_bispado(d, h.strftime("%H:%M"), n, "Agendado"); st.rerun()
            df_a = ler_dados("agenda_bispado", "data_agenda ASC")
            for _, r in df_a.iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"🗓️ **{r['data_agenda']}** - {r['nome_compromisso']}")
                if col2.button("❌", key=f"a_{r['id']}"): excluir_registro('agenda_bispado', r['id']); st.rerun()
        
        with tab_caravana:
            st.subheader("🚌 Gestão Financeira das Caravanas")
            with st.container():
                col_conf1, col_conf2 = st.columns([0.7, 0.3])
                with col_conf1: mes_sel = st.selectbox("Selecione o Mês da Caravana", ["Janeiro", "Abril", "Julho", "Outubro"])
                with col_conf2: padrao_caravana = st.number_input("Valor Padrão da Caravana (R$)", min_value=0.0, value=200.0, step=10.0, help="Valor que virá preenchido automaticamente ao adicionar novo irmão")
            
            df_dashboard = ler_dados("financeiro_caravanas")
            val_total_geral = 0.0; val_pago_geral = 0.0; val_falta_geral = 0.0
            if not df_dashboard.empty:
                df_dash_mes = df_dashboard[df_dashboard['mes_caravana'] == mes_sel]
                if not df_dash_mes.empty:
                    val_total_geral = df_dash_mes['valor_total'].sum()
                    val_pago_geral = df_dash_mes['valor_pago'].sum()
                    val_falta_geral = val_total_geral - val_pago_geral
            
            cd1, cd2, cd3 = st.columns(3)
            cd1.metric("💰 VALOR TOTAL ESPERADO", f"R$ {val_total_geral:,.2f}")
            cd2.metric("✅ TOTAL JÁ PAGO", f"R$ {val_pago_geral:,.2f}")
            cd3.metric("📉 FALTA ARRECADAR", f"R$ {val_falta_geral:,.2f}")
            st.divider()

            with st.form("f_caravana", clear_on_submit=True):
                st.write("Adicionar Novo Irmão(ã)")
                c1, c2 = st.columns([4, 2])
                nome_irm = c1.text_input("Nome")
                v_pago = c2.number_input("Valor Pago Inicial (R$)", min_value=0.0, value=0.0, step=10.0)
                if st.form_submit_button("Adicionar"):
                    if nome_irm:
                        adicionar_caravana_simples(nome_irm, mes_sel, padrao_caravana, v_pago)
                        st.success("Adicionado!"); st.rerun()
            st.divider()
            
            df_c = ler_dados("financeiro_caravanas")
            if not df_c.empty:
                df_filtrado = df_c[df_c['mes_caravana'] == mes_sel].copy()
                if not df_filtrado.empty:
                    df_filtrado['quitado'] = df_filtrado['quitado'].apply(lambda x: True if x == 1 else False)
                    df_editor = df_filtrado[['id', 'nome_irmao', 'valor_total', 'valor_pago', 'quitado']].reset_index(drop=True)
                    st.write("📝 **Edite diretamente na tabela abaixo:** (Pressione ENTER para atualizar)")
                    edited_df = st.data_editor(df_editor, column_config={"id": None, "nome_irmao": "Nome", "valor_total": st.column_config.NumberColumn("Total (R$)", format="R$ %.2f"), "valor_pago": st.column_config.NumberColumn("Pago (R$)", format="R$ %.2f"), "quitado": st.column_config.CheckboxColumn("Quitado?", help="Marque se estiver pago")}, disabled=["nome_irmao", "valor_total"], hide_index=True, width="stretch", key="editor_caravana")
                    
                    try:
                        diff_pago = (df_editor['valor_pago'] - edited_df['valor_pago']).abs().sum()
                        diff_quitado = (df_editor['quitado'] != edited_df['quitado']).sum()
                        if diff_pago > 0.001 or diff_quitado > 0: atualizar_lote_caravana(edited_df); st.rerun()
                    except: pass

                    edited_df['valor_a_pagar'] = edited_df['valor_total'] - edited_df['valor_pago']
                    st.caption("Visualização de Status (Vermelho = Pendente | Verde = Quitado)")
                    def color_status(val): return 'color: #ff5252; font-weight: bold' if val > 0.01 else 'color: #69f0ae; font-weight: bold'
                    st.dataframe(edited_df[['nome_irmao', 'valor_a_pagar']].style.format({"valor_a_pagar": "R$ {:.2f}"}).map(color_status, subset=['valor_a_pagar']), width="stretch", hide_index=True)
                    
                    c_exp1, c_exp2, c_del = st.columns([1, 1, 2])
                    with c_exp1: st.download_button("📥 Excel", to_excel(edited_df), file_name=f"Caravana_{mes_sel}.xlsx")
                    with c_exp2: 
                        try: st.download_button("📄 PDF", to_pdf(edited_df, mes_sel), file_name=f"Caravana_{mes_sel}.pdf", mime="application/pdf")
                        except: st.error("Erro PDF")
                    with c_del:
                        with st.expander("🗑️ Excluir"):
                             for _, r in df_filtrado.iterrows():
                                if st.button(f"Excluir {r['nome_irmao']}", key=f"del_c_{r['id']}"): excluir_registro('financeiro_caravanas', r['id']); st.rerun()
                else: st.info(f"Nenhum registro para {mes_sel}.")
            else: st.info("Nenhum registro encontrado.")

        with tab_orc: exibir_orcamento()
        with tab_ind: exibir_indicadores_profeticos(permitir_edicao=True)
    else: st.warning("Acesso restrito.")