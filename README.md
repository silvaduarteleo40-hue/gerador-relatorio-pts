# Gerador de Relatório de Permissões de Trabalho (PTs)

Aplicativo em Python com interface gráfica (Tkinter) para leitura e extração automatizada de dados de Permissões de Trabalho em formato PDF (padrão Nestlé) e consolidação em planilhas Excel (.xlsx).

## 🚀 Funcionalidades

- **Interface Gráfica Simples**: Seleção de pastas intuitiva via janela do Windows.
- **Extração Automatizada de PDFs**:
  - Número da PTe
  - Local da atividade
  - Descrição da atividade
  - Datas de início e fim planejadas/efetivas
  - Contagem de executantes assinados
- **Cálculo de Jornada e Homem-Hora (H/H)**:
  - Cálculo de horas baseado na jornada padrão (9h de Segunda a Quinta, 8h na Sexta-feira).
  - Cálculo automático do total de Homem-Hora (`Duração × Executantes`).
- **Exportação para Excel**: Gera uma planilha consolidada com todos os dados processados.

## 🛠️ Tecnologias Utilizadas

- **Python 3**
- **Tkinter** (interface gráfica)
- **pdfplumber** (extração e parsing de texto dos PDFs)
- **pandas** e **openpyxl** (tratamento de dados e geração do relatório em Excel)

## 📦 Instalação e Execução

1. Clone o repositório:
   ```bash
   git clone https://github.com/silvaduarteleo40-hue/gerador-relatorio-pts.git
   cd gerador-relatorio-pts
   ```

2. Crie e ative um ambiente virtual:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Execute a aplicação:
   ```bash
   python pts_script.py
   ```
