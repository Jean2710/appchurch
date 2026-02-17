import sqlite3
import pyperclip
import pyautogui
import time
import webbrowser
import schedule
from datetime import datetime

# --- CONFIGURAÇÕES ---
ID_GRUPO_IGREJA = "7Fi40y3GnJG5AIoMSU03v6"
CAMINHO_BANCO = 'igreja.db'

# IMPORTANTE: Mantenha os nomes em MAIÚSCULAS para bater com a lógica de busca
CONTATOS_LIDERANCA = {
    "WEIMER": "5565981170015",
    "PAZ": "5565992828453",
    "COUTINHO": "5565981090775"
}

# --- FUNÇÕES DE BUSCA (SQLITE) ---

def buscar_ultimo_comunicado():
    try:
        conn = sqlite3.connect(CAMINHO_BANCO)
        cursor = conn.cursor()
        cursor.execute("SELECT titulo, mensagem, link FROM comunicados ORDER BY id DESC LIMIT 1")
        resultado = cursor.fetchone()
        conn.close()
        return resultado
    except Exception as e:
        print(f"❌ Erro banco comunicados: {e}")
        return None

def buscar_tarefas_pendentes():
    try:
        conn = sqlite3.connect(CAMINHO_BANCO)
        cursor = conn.cursor()
        # Busca apenas o que você marcou como 'Pendente' no seu App Streamlit
        cursor.execute("SELECT tarefa, responsavel, prioridade FROM tarefas_bispado WHERE status = 'Pendente'")
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    except Exception as e:
        print(f"❌ Erro banco tarefas: {e}")
        return []

# --- FUNÇÕES DE DISPARO (AUTOMAÇÃO DE INTERFACE) ---

def disparar_comunicado_grupo():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Enviando comunicado ao grupo...")
    comunicado = buscar_ultimo_comunicado()
    if comunicado:
        titulo, mensagem, link = comunicado
        texto = f"⛪ *PORTAL DA ALA - COMUNICADO*\n\n📌 *{titulo.upper()}*\n\n{mensagem}\n"
        if link and str(link).lower() != "none": 
            texto += f"\n🔗 Saiba mais: {link}"
        
        pyperclip.copy(texto)
        webbrowser.open(f"https://web.whatsapp.com/accept?code={ID_GRUPO_IGREJA}")
        
        time.sleep(50) # Tempo de carga para o grupo
        
        # Foco e envio usando a tecla ESC para centralizar na caixa de texto
        pyautogui.click(10, 10) 
        pyautogui.press('esc')
        time.sleep(2)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(2)
        pyautogui.press('enter')
        print("✅ Grupo notificado!")
    else:
        print("⚠️ Sem comunicados recentes para o grupo.")

def disparar_tarefas_individuais():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📋 Iniciando lembretes individuais...")
    tarefas = buscar_tarefas_pendentes()
    
    if not tarefas:
        print("✅ Nenhuma tarefa pendente encontrada no banco.")
        return

    # Agrupa tarefas por responsável
    dados_envio = {}
    for tarefa, resp, prio in tarefas:
        resp_upper = str(resp).upper().strip() 
        if resp_upper not in dados_envio: 
            dados_envio[resp_upper] = []
        dados_envio[resp_upper].append(f"• *[{prio}]* {tarefa}")

    for responsavel, lista_tarefas in dados_envio.items():
        if responsavel in CONTATOS_LIDERANCA:
            numero = CONTATOS_LIDERANCA[responsavel]
            
            msg = f"Olá *{responsavel}*, você tem as seguintes tarefas pendentes no *Portal da Ala*:\n\n"
            msg += "\n".join(lista_tarefas)
            msg += "\n\n📌 _Por favor, verifique o painel do Bispado no App._"
            
            pyperclip.copy(msg)
            webbrowser.open(f"https://web.whatsapp.com/send?phone={numero}")
            
            print(f"⏳ Carregando conversa de {responsavel} (Aguarde 50s)...")
            time.sleep(50) 
            
            # --- ESTRATÉGIA DE FOCO ROBUSTA ---
            # 1. Clica no canto superior para focar na janela do navegador
            pyautogui.click(10, 10) 
            time.sleep(1)
            
            # 2. Usa ESC para forçar o foco na caixa de entrada de texto
            pyautogui.press('esc')
            time.sleep(2)
            
            print(f"⌨️ Colando mensagem para {responsavel}...")
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(2)
            pyautogui.press('enter')
            
            # 3. Espera o envio e fecha a aba
            time.sleep(3)
            pyautogui.hotkey('ctrl', 'w') 
            print(f"✅ Notificação enviada para {responsavel}")
            time.sleep(5) 
        else:
            print(f"⚠️ O responsável '{responsavel}' não cadastrado no dicionário.")

# --- AGENDADOR E TESTE ---
if __name__ == "__main__":
    # PARA TESTAR AGORA: Descomente a linha abaixo e comente o bloco "while True"
    # disparar_tarefas_individuais()

    print("⛪ Central de Automação da Ala Iniciada!")
    print("📅 Configurado: Grupo às 13:00 | Liderança às 13:05")

    # Agendamento das tarefas
    schedule.every().day.at("13:00").do(disparar_comunicado_grupo)
    schedule.every().day.at("13:01").do(disparar_tarefas_individuais)

    # Loop principal de execução
    while True:
        schedule.run_pending()
        time.sleep(30)