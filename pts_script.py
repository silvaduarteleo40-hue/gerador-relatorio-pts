import sys
import os
import re
from datetime import datetime, timedelta
import pdfplumber
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


def obter_caminho_recurso(caminho_relativo):
    """Retorna o caminho correto para arquivos de recurso, seja via Python ou no executável do PyInstaller."""
    try:
        # O PyInstaller cria uma pasta temporária e armazena o caminho nessa variável _MEIPASS
        caminho_base = sys._MEIPASS
    except Exception:
        caminho_base = os.path.abspath(".")

    return os.path.join(caminho_base, caminho_relativo)


def calcular_horas_jornada(inicio_str, fim_str):
    """Calcula horas com base em 9h (Seg-Qui) e 8h (Sexta)."""
    padrao_data = r'(\d{2}/\d{2}/\d{4})'
    match_inicio = re.search(padrao_data, inicio_str)
    match_fim = re.search(padrao_data, fim_str) if fim_str else None

    if not match_inicio:
        return 0.0

    dt_inicio = datetime.strptime(match_inicio.group(1), "%d/%m/%Y").date()
    dt_fim = datetime.strptime(match_fim.group(1), "%d/%m/%Y").date() if match_fim else dt_inicio

    total_horas = 0.0
    dt_atual = dt_inicio

    while dt_atual <= dt_fim:
        dia_semana = dt_atual.weekday()
        if dia_semana in [0, 1, 2, 3]:   # Segunda a Quinta (9h)
            total_horas += 9.0
        elif dia_semana == 4:            # Sexta-feira (8h)
            total_horas += 8.0
        dt_atual += timedelta(days=1)

    return total_horas


def extrair_dados_pt_nestle(caminho_pdf):
    """Extrai dados específicos das PTs no padrão Nestlé."""
    texto_completo = ""
    linhas_texto = []

    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            t = pagina.extract_text()
            if t:
                texto_completo += t + "\n"
                linhas_texto.extend([l.strip() for l in t.split('\n') if l.strip()])

    # 1. ID PTe
    id_pte = re.search(r'ID da PTe\s*[:\n]?\s*(\d+)', texto_completo)
    id_pte_val = id_pte.group(1) if id_pte else "N/A"

    # 2. Local
    local_val = "N/A"
    for i, linha in enumerate(linhas_texto):
        if "Local da atividade" in linha and i + 1 < len(linhas_texto):
            local_val = linhas_texto[i + 1]
            break

    # 3. Descrição da Atividade
    atividade = re.search(
        r'Descrição detalhada da atividade\s*\n\s*(.*?)(?=\nID - Modelo|\nEmpresas|\nObservação)',
        texto_completo,
        re.DOTALL
    )
    atividade_val = atividade.group(1).replace('\n', ' ').strip() if atividade else "N/A"

    # 4. Datas/Horas
    inicio_plan_val, fim_plan_val, inicio_efet_val = "", "", ""

    for i, linha in enumerate(linhas_texto):
        if "Data/Hora planejada inicio" in linha and i + 1 < len(linhas_texto):
            inicio_plan_val = linhas_texto[i + 1]
        elif "Data/Hora planejada fim" in linha and i + 1 < len(linhas_texto):
            fim_plan_val = linhas_texto[i + 1]
        elif "Data/Hora efetiva inicio" in linha and i + 1 < len(linhas_texto):
            inicio_efet_val = linhas_texto[i + 1]

    data_inicio_raw = inicio_efet_val if (inicio_efet_val and inicio_efet_val != "--") else inicio_plan_val
    data_fim_raw = fim_plan_val

    m_ini = re.search(r'\d{2}/\d{2}/\d{4}', data_inicio_raw)
    m_fim = re.search(r'\d{2}/\d{2}/\d{4}', data_fim_raw)

    data_inicio_exibicao = m_ini.group(0) if m_ini else "N/A"
    data_fim_exibicao = m_fim.group(0) if m_fim else "N/A"

    # 5. Contagem de Executantes
    qte_executantes = 0
    em_bloco_executantes = False

    for linha in linhas_texto:
        if "Assinatura de abertura do(s) Executante(s)" in linha:
            em_bloco_executantes = True
            continue
        if em_bloco_executantes and ("Assinatura de abertura do(s) Auxiliar(es)" in linha or "PTe Trabalho" in linha):
            break
        if em_bloco_executantes and "Assinado em:" in linha:
            qte_executantes += 1

    # 6. Cálculos de Horas e H/H
    duracao_horas = calcular_horas_jornada(data_inicio_raw, data_fim_raw)
    homem_hora = duracao_horas * qte_executantes

    return {
        "Arquivo": os.path.basename(caminho_pdf),
        "ID PTe": id_pte_val,
        "Local": local_val,
        "Atividade": atividade_val,
        "Data Início": data_inicio_exibicao,
        "Data Fim": data_fim_exibicao,
        "Qtd. Executantes": qte_executantes,
        "Duração (Horas)": duracao_horas,
        "Homem-Hora (H/H)": homem_hora
    }


class AplicativoPT:
    def __init__(self, root):
        self.root = root
        cor_fundo = "#315b2d"

        # Aplica o ícone da janela
        caminho_icone = obter_caminho_recurso("Security.ico")
        if os.path.exists(caminho_icone):
            try:
                self.root.iconbitmap(caminho_icone)
            except Exception as e:
                print(f"Erro ao carregar o ícone: {e}")

        self.root.title("Extrator de Homem-Hora de PTs")
        self.root.geometry("450x230")
        self.root.config(bg=cor_fundo)
        self.root.resizable(False, False)

        # Estilo ttk
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TFrame', background=cor_fundo)
        self.style.configure('TLabel', background=cor_fundo, foreground='white')

        # Variáveis
        self.caminho_pasta = tk.StringVar()

        # Layout
        frame = ttk.Frame(root, padding="20", style='TFrame')
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text="Selecione a pasta onde estão as PTs em PDF:",
            font=("Arial", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))

        e_frame = ttk.Frame(frame, style='TFrame')
        e_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Entry(e_frame, textvariable=self.caminho_pasta, width=45).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5)
        )
        ttk.Button(e_frame, text="Procurar...", command=self.selecionar_pasta).pack(side=tk.RIGHT)

        self.btn_processar = ttk.Button(frame, text="Gerar Relatório Excel", command=self.processar)
        self.btn_processar.pack(pady=10, fill=tk.X)

        self.lbl_status = ttk.Label(
            frame,
            text="Status: Aguardando seleção da pasta.",
            font=("Arial", 9, "italic")
        )
        self.lbl_status.pack(anchor=tk.W, pady=(10, 0))

    def selecionar_pasta(self):
        pasta = filedialog.askdirectory(title="Selecione a pasta com as PTs")
        if pasta:
            self.caminho_pasta.set(pasta)

    def processar(self):
        pasta = self.caminho_pasta.get()
        if not pasta or not os.path.exists(pasta):
            messagebox.showwarning("Aviso", "Por favor, selecione uma pasta válida!")
            return

        arquivos = [f for f in os.listdir(pasta) if f.lower().endswith('.pdf')]
        if not arquivos:
            messagebox.showinfo("Informação", "Nenhum arquivo PDF encontrado na pasta selecionada.")
            return

        arquivo_saida = filedialog.asksaveasfilename(
            title="Salvar relatório Excel como",
            defaultextension=".xlsx",
            filetypes=[("Arquivo Excel", "*.xlsx")],
            initialfile="relatorio_homem_hora.xlsx"
        )

        if not arquivo_saida:
            return

        self.lbl_status.config(text=f"Processando {len(arquivos)} arquivo(s)... Aguarde.")
        self.root.update()

        dados_processados = []
        for arq in arquivos:
            caminho = os.path.join(pasta, arq)
            try:
                res = extrair_dados_pt_nestle(caminho)
                dados_processados.append(res)
            except Exception as e:
                print(f"Erro no arquivo {arq}: {e}")

        if dados_processados:
            df = pd.DataFrame(dados_processados)

            # Cálculo dos Totalizadores
            total_horas = df["Duração (Horas)"].sum()
            total_hh = df["Homem-Hora (H/H)"].sum()
            total_executantes = df["Qtd. Executantes"].sum()
            dias_trabalhados_estimados = round(total_horas / 8.8, 1) if total_horas > 0 else 0

            # Linha de fechamento
            linha_total = {
                "Arquivo": "TOTAL GERAL",
                "ID PTe": "-",
                "Local": "-",
                "Atividade": f"Total de Dias Úteis Estimados: ~{dias_trabalhados_estimados} dias",
                "Data Início": "-",
                "Data Fim": "-",
                "Qtd. Executantes": total_executantes,
                "Duração (Horas)": total_horas,
                "Homem-Hora (H/H)": total_hh
            }

            df_final = pd.concat([df, pd.DataFrame([linha_total])], ignore_index=True)
            df_final.to_excel(arquivo_saida, index=False)

            mensagem_sucesso = (
                f"Relatório gerado com sucesso!\n\n"
                f"• Total de PTs: {len(dados_processados)}\n"
                f"• Total de Horas: {total_horas:.1f} hrs\n"
                f"• Dias Trabalhados (Estimados): ~{dias_trabalhados_estimados} dias\n"
                f"• Homem-Hora Acumulado (H/H): {total_hh:.1f}\n\n"
                f"Salvo em: {arquivo_saida}"
            )

            self.lbl_status.config(text="Processamento concluído com sucesso!")
            messagebox.showinfo("Resumo do Fechamento", mensagem_sucesso)
        else:
            self.lbl_status.config(text="Erro ao processar os arquivos.")
            messagebox.showerror("Erro", "Não foi possível extrair dados dos arquivos fornecidos.")


if __name__ == "__main__":
    root = tk.Tk()
    app = AplicativoPT(root)
    root.mainloop()