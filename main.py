import streamlit as st
import pandas as pd
import sqlite3
import calendar
from datetime import datetime, date, time
import os
import plotly.express as px
import plotly.graph_objects as go

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Portal da Ala", page_icon="⛪", layout="wide")

# --- CAMINHOS ABSOLUTOS ---
# Garante que o banco e as pastas sejam criados no local correto do servidor
BASE_DIR = os.getcwd()
DB_PATH = os.path.join(BASE_DIR, 'igreja.db')
POSTS_DIR = os.path.join(BASE_DIR, 'posts')

if not os.path.exists(POSTS_DIR):
    os.makedirs(POSTS_DIR)

# --- CSS CUSTOMIZADO ---
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #FFFFFF !important; font-weight: 800 !important; font-size: 1.8rem !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    [data-testid="stMetricLabel"] { color: #F0F2F6 !important; font-weight: bold !important; text-transform: uppercase; }
    div[data-testid="stMetric"] { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
    .comunicado-card { padding: 20px; border-radius: 15px; border-left: 8px solid #1976d2; background-color: #f8f9fa; margin-bottom: 25px; }
    
    .cal-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; max-width: 450px; margin: auto; text-align: center; }
    .cal-header { font-weight: bold; color: #1976d2; margin-bottom: 10px; text-transform: uppercase; font-size: 1.2rem; }
    .cal-weekday { font-size: 0.8rem; color: #666; font-weight: bold; padding: 5px; }
    .cal-day { padding: 10px; border-radius: 5px; background-color: #ffffff; border: 1px solid #e0e0e0; min-height: 40px; display: flex; align-items: center; justify-content: center; }
    .cal-active { background-color: #1976d2 !important; color: white !important; font-weight: bold; }
    .cal-today { border: 2px solid #ff4b4b; color: #ff4b4b; font-weight: bold; }
    .cal-empty { background-color: transparent; border: none; }

    .cal-giant-container { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; width: 100%; text-align: center; }
    .cal-giant-header { font-weight: bold; color: #1976d2; margin-bottom: 15px; text-transform: uppercase; font-size: 1.8rem; text-align: center; }
    .cal-giant-day { min-height: 110px; padding: 10px; border-radius: 10px; background: white; border: 1px solid #ddd; display: flex; flex-direction: column; align-items: center; }
    .cal-giant-active { background-color: #e3f2fd !important; border: 2px solid #1976d2 !important; }
    .event-dot { width: 10px; height: 10px; background-color: #1976d2; border-radius: 50%; margin-top: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- BACKEND ---
def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS comunicados (id INTEGER PRIMARY KEY AUTOINCREMENT, data_postagem TEXT, titulo TEXT, mensagem TEXT, autor TEXT, link TEXT, imagem TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS agenda (id INTEGER PRIMARY KEY AUTOINCREMENT, data_evento TEXT, titulo TEXT, descricao TEXT, local TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tarefas_bispado (id INTEGER PRIMARY KEY AUTOINCREMENT, data_criacao TEXT, tarefa TEXT, status TEXT, prioridade TEXT, responsavel TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS agenda_bispado (id INTEGER PRIMARY KEY AUTOINCREMENT, data_agenda TEXT, horario TEXT, nome_compromisso TEXT, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS planejamento_lideranca (id INTEGER PRIMARY KEY AUTOINCREMENT, organizacao TEXT, atividade TEXT, data_planejada TEXT, horario_inicio TEXT, horario_fim TEXT)')
    conn.commit()
    conn.close()

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

def excluir_registro(tabela, id_item, imagem_path=None):
    conn = get_connection(); c = conn.cursor()
    if imagem_path and os.path.exists(str(imagem_path)):
        try: os.remove(imagem_path)
        except: pass
    c.execute(f'DELETE FROM {tabela} WHERE id = ?', (id_item,))
    conn.commit(); conn.close()

def ler_dados(tabela, ordem="id DESC"):
    conn = get_connection()
    df = pd.read_sql_query(f"SELECT * FROM {tabela} ORDER BY {ordem}", conn)
    conn.close(); return df

init_db()

# --- FUNÇÕES CALENDÁRIO ---
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

def exibir_indicadores_profeticos():
    st.header("📊 Prioridades Proféticas - Brasil")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("FREQUÊNCIA SACRAMENTAL", "109", "-1 p/ Meta")
    col2.metric("MEMBROS PARTICIPANTES", "102", "-13 p/ Meta")
    col3.metric("BATISMOS", "4", "-16 p/ Meta")
    col4.metric("MISSIONÁRIOS", "1", "-1 p/ Meta")
    st.markdown("<br>", unsafe_allow_html=True)
    col5, col6, col7, col8 = st.columns(4)
    col5.metric("JEJUM", "20", "-14 p/ Meta")
    col6.metric("MEMBROS RETORNANDO", "0", "-10 p/ Meta")
    col7.metric("MEMBROS COM INVESTIDURA", "49", "-1 p/ Meta")
    col8.metric("MEMBROS SEM INVESTIDURA", "26", "-4 p/ Meta")
    st.divider()
    
    meta_data_grafico = {"Indicador": ["Frequência", "Templo", "Retorno", "Jejum", "Batismos", "Missionários"], "Atual": [109, 102, 0, 20, 4, 1], "Meta": [110, 115, 10, 34, 20, 2]}
    st.plotly_chart(go.Figure(data=[go.Bar(name='Atual', x=meta_data_grafico['Indicador'], y=meta_data_grafico['Atual'], marker_color='#1e3a8a'), go.Bar(name='Meta', x=meta_data_grafico['Indicador'], y=meta_data_grafico['Meta'], marker_color='#93c5fd')]), use_container_width=True)
    
    st.subheader("📋 Tabela Detalhada")
    df_pdf = pd.DataFrame({
        "Categoria": ["VIVER", "VIVER", "CUIDAR NECESSITADOS", "CUIDAR NECESSITADOS", "CONVIDAR TODOS", "CONVIDAR TODOS", "UNIR FAMÍLIAS", "UNIR FAMÍLIAS"],
        "Indicador": ["Frequência Sacramental", "Membros Participantes", "Membros Retornando", "Membros Jejuando", "Batismos de Conversos", "Missionários Servindo no Brasil", "Membros com Investidura", "Membros sem Investidura"],
        "Atual": [109, 102, 0, 20, 4, 1, 49, 26],
        "Meta": [110, 115, 10, 34, 20, 2, 50, 30]
    })
    st.table(df_pdf)

def exibir_orcamento():
    st.subheader("💰 Gestão Orçamentária")
    if os.path.exists("orcamento.xlsx"):
        try:
            df_fin = pd.read_excel("orcamento.xlsx", engine="openpyxl")
            total = df_fin[df_fin['Categoria'] == 'TOTAL']
            if not total.empty:
                c1, c2, c3 = st.columns(3)
                c1.metric("Orçamento Total", f"R$ {total['Orçamento Inicial (R$)'].values[0]:,.2f}")
                c2.metric("Valor Gasto", f"R$ {total['Valor Gasto (R$)'].values[0]:,.2f}", delta_color="inverse")
                c3.metric("Saldo", f"R$ {total['Saldo Atual (R$)'].values[0]:,.2f}")
            st.plotly_chart(px.bar(df_fin[df_fin['Categoria'] != 'TOTAL'], x='Categoria', y='Orçamento Inicial (R$)', color='Categoria'), use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao ler orçamento: {e}")
    else:
        st.info("Arquivo 'orcamento.xlsx' não encontrado.")

# --- INTERFACE SIDEBAR ---
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=100)

menu = st.sidebar.radio("Navegar", ["📢 Mural de Avisos", "📅 Calendário da Ala", "🔒 Líderes e Secretários", "🏢 Painel do Bispado"])

def verificar_acesso(tipo):
    senha = st.sidebar.text_input(f"Senha {tipo.capitalize()}", type="password", key=f"pwd_{tipo}")
    return senha == ("admin123" if tipo == "lideranca" else "bispo2026")

# --- MURAL ---
if menu == "📢 Mural de Avisos":
    st.title("📢 Mural de Avisos")
    df = ler_dados("comunicados")
    for _, r in df.iterrows():
        st.markdown(f"<div class='comunicado-card'><h3>📌 {r['titulo']}</h3><p>{r['data_postagem']}</p></div>", unsafe_allow_html=True)
        if r.get('imagem') and os.path.exists(str(r['imagem'])): st.image(r['imagem'], use_container_width=True)
        st.write(r['mensagem']); st.divider()

# --- CALENDÁRIO ALA ---
elif menu == "📅 Calendário da Ala":
    st.title("📅 Calendário da Ala")
    df_p = ler_dados("planejamento_lideranca", "data_planejada ASC")
    mes_ref = st.selectbox("Mês", range(1, 13), index=datetime.now().month-1)
    st.markdown(gerar_calendario_gigante(2026, mes_ref, df_p), unsafe_allow_html=True)

# --- LÍDERES E SECRETÁRIOS ---
elif menu == "🔒 Líderes e Secretários":
    if verificar_acesso("lideranca"):
        t1, t2, t3, t4 = st.tabs(["📝 Postar", "🗑️ Gerenciar", "📅 Planejamento", "📊 Indicadores Proféticos"])
        
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
            for _, r in df_m.iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"📌 {r['titulo']}")
                if col2.button("Remover", key=f"rm_{r['id']}"): 
                    excluir_registro('comunicados', r['id'], r.get('imagem'))
                    st.rerun()

        with t3:
            with st.form("f_plan_fixed", clear_on_submit=True):
                c1, c2, c3 = st.columns(3)
                org = c1.selectbox("Org", ["Quórum de Elderes", "Sociedade de Socorro", "Moças", "Rapazes", "Primária", "Obra Missionária"])
                atv = c2.text_input("Atividade"); dt = c3.date_input("Data", date.today())
                ch1, ch2 = st.columns(2)
                h_inicio = ch1.time_input("Início", value=time(19, 0))
                h_fim = ch2.time_input("Término", value=time(20, 30))
                if st.form_submit_button("Salvar Atividade"):
                    if atv: 
                        adicionar_planejamento_lideranca(org, atv, dt.strftime("%Y-%m-%d"), h_inicio.strftime("%H:%M"), h_fim.strftime("%H:%M"))
                        st.rerun()
            st.divider()
            df_p = ler_dados("planejamento_lideranca", "data_planejada ASC")
            col_visual, col_lista = st.columns([0.5, 0.5])
            with col_visual:
                m_s = st.selectbox("Mês para Visualizar", range(1, 13), index=date.today().month-1, key="plan_month")
                st.markdown(gerar_calendario_html(2026, m_s, df_p['data_planejada'].tolist()), unsafe_allow_html=True)
            with col_lista:
                st.write(f"### Atividades de {m_s}/2026")
                df_f = df_p[df_p['data_planejada'].str.contains(f"2026-{m_s:02d}")]
                for _, r in df_f.iterrows():
                    ci, cb = st.columns([0.8, 0.2])
                    ci.write(f"**{r['data_planejada']}** - {r['organizacao']}")
                    if cb.button("🗑️", key=f"del_plan_{r['id']}"):
                        excluir_registro('planejamento_lideranca', r['id'])
                        st.rerun()
        
        with t4:
            exibir_indicadores_profeticos()

elif menu == "🏢 Painel do Bispado":
    if verificar_acesso("bispado"):
        tab_tarefas, tab_agenda, tab_orc, tab_ind = st.tabs(["🎯 Tarefas", "📅 Agenda", "💰 Orçamento", "📊 Indicadores Proféticos"])
        
        with tab_tarefas:
            with st.form("f_meta", clear_on_submit=True):
                mt = st.text_input("Tarefa")
                c_inp = st.columns(3)
                pr = c_inp[0].selectbox("Prioridade", ["Alta","Média","Baixa"])
                rs = c_inp[1].text_input("Responsável")
                stt = c_inp[2].selectbox("Status", ["Pendente", "Concluido"])
                if st.form_submit_button("Salvar Tarefa"): 
                    if mt and rs:
                        adicionar_tarefa_bispado(mt, pr, rs, stt)
                        st.rerun()
            st.divider()
            df_t = ler_dados("tarefas_bispado")
            if not df_t.empty:
                st.dataframe(df_t[['tarefa', 'prioridade', 'responsavel', 'status']], use_container_width=True, hide_index=True)
                with st.expander("⚙️ Gerenciar Tarefas"):
                    for _, r in df_t.iterrows():
                        c_task, c_btn_status, c_btn_del = st.columns([0.6, 0.2, 0.2])
                        c_task.write(f"**{r['tarefa']}**")
                        if r['status'] == "Pendente":
                            if c_btn_status.button("✅", key=f"done_{r['id']}"):
                                atualizar_status_tarefa(r['id'], "Concluido"); st.rerun()
                        if c_btn_del.button("🗑️", key=f"t_del_{r['id']}"):
                            excluir_registro('tarefas_bispado', r['id']); st.rerun()
        
        with tab_agenda:
            with st.form("f_bis"):
                d = st.date_input("Data"); h = st.time_input("Hora"); n = st.text_input("Assunto")
                if st.form_submit_button("Agendar"): 
                    adicionar_agenda_bispado(d, h.strftime("%H:%M"), n, "Agendado"); st.rerun()
            df_a = ler_dados("agenda_bispado", "data_agenda ASC")
            for _, r in df_a.iterrows():
                col1, col2 = st.columns([0.8, 0.2])
                col1.write(f"🗓️ **{r['data_agenda']}** - {r['nome_compromisso']}")
                if col2.button("❌", key=f"a_{r['id']}"): 
                    excluir_registro('agenda_bispado', r['id']); st.rerun()

        with tab_orc: exibir_orcamento()
        with tab_ind: exibir_indicadores_profeticos()
    else: st.warning("Acesso restrito.")
