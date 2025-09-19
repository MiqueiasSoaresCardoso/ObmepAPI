import requests # Para fazer a chamada à API
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# --- 1. Obter os Dados da sua API ---
url_api = 'http://192.168.1.5:5000/api/analise-completa-escolas-p98-obmep' # Use a URL correta do seu endpoint
print(f"Buscando dados da API em: {url_api}")

try:
    response = requests.get(url_api)
    response.raise_for_status() # Lança um erro se a requisição falhou (ex: 404, 500)
    data = response.json()
    print("Dados da API obtidos com sucesso.")
except requests.exceptions.RequestException as e:
    print(f"Erro ao conectar ou obter dados da API: {e}")
    exit()
except ValueError:
    print("Erro: A resposta da API não é um JSON válido.")
    exit()

# Extrair as partes relevantes do JSON
try:
    justificativa = data['justificativa_selecao']
    dados_histograma = justificativa['dados_para_plot_histograma']
    frequencias = dados_histograma['frequencias']
    intervalos_bins = dados_histograma['intervalos_bins']

    # Valores para anotação
    p98_corte = justificativa['p98_valor_corte']
    n_escolas_selecionadas = justificativa['n_escolas_selecionadas_p98']
    total_escolas = justificativa['total_escolas_publicas_premiadas_periodo']
    estatisticas = justificativa['estatisticas_descritivas_distribuicao_geral']

except KeyError as e:
    print(f"Erro: A chave {e} não foi encontrada na resposta da API. Verifique a estrutura do JSON.")
    exit()

# --- 2. Preparar os Dados para o Gráfico ---
# O Matplotlib/Seaborn podem plotar histogramas a partir de frequências e bins,
# mas uma forma mais direta é usar o tipo 'bar'.
# Vamos calcular o centro de cada bin para usar como rótulo no eixo X.
# A largura da barra será a largura do bin.
bin_centers = []
bin_widths = []
for i in range(len(intervalos_bins) - 1):
    largura = intervalos_bins[i+1] - intervalos_bins[i]
    centro = intervalos_bins[i] + (largura / 2)
    bin_centers.append(centro)
    bin_widths.append(largura)

# --- 3. Gerar o Gráfico com Eixo X Regular ---
sns.set_theme(style="whitegrid")
fig, ax = plt.subplots(figsize=(14, 8))

# Criar o gráfico de barras para simular o histograma
ax.bar(bin_centers, frequencias, width=bin_widths, color="skyblue", edgecolor='black', alpha=0.7, align='center')

# Focar o eixo X para melhor visualização
ax.set_xlim(-5, 400)

# Adicionar a linha vertical para o corte do P98
ax.axvline(x=p98_corte, color='red', linestyle='--', linewidth=2.5,
           label=f'Corte P98 = {p98_corte:.0f} Pontos\n(N = {n_escolas_selecionadas} escolas selecionadas)')

# Melhorar rótulos e título
ax.set_title('Distribuição da Pontuação Ponderada de Escolas na OBMEP (2010-2023)', fontsize=18, pad=20)
ax.set_xlabel('Pontuação Ponderada Acumulada', fontsize=14)
ax.set_ylabel('Número de Escolas (Frequência)', fontsize=14)

# --- AJUSTE DOS TICKS DO EIXO X (USANDO UMA GRADE REGULAR) ---
# Usar uma grade de 50 em 50 é uma boa opção para este intervalo.
# Isso torna a localização do 37 um exercício visual para o leitor.
ax.set_xticks(np.arange(0, 401, 50)) # Marcas em 0, 50, 100, 150, 200, 250, 300, 350, 400
# Alternativa mais densa, se preferir:
# ax.set_xticks(np.arange(0, 401, 25))
# --- FIM DO AJUSTE ---

# Melhorar a legenda
ax.legend(fontsize=12, loc='upper right')

# Adicionar a caixa de texto com as estatísticas
texto_anotacao = (
    f'Universo Analisado:\n{total_escolas} escolas públicas premiadas\n\n'
    f"Média: {estatisticas.get('mean', 'N/A'):.2f}\n"
    f"Mediana (P50): {estatisticas.get('50%', 'N/A'):.1f}\n"
    f"Desv. Padrão: {estatisticas.get('std', 'N/A'):.2f}"
)
ax.text(0.95, 0.95, texto_anotacao, transform=ax.transAxes, fontsize=12,
        verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.8))


ax.tick_params(axis='x', labelsize=12)
ax.tick_params(axis='y', labelsize=12)
plt.tight_layout()

# Salvar o gráfico em alta resolução
plt.savefig('grafico_selecao_amostra_p98_eixo_regular.png', dpi=300)
print("Gráfico 'grafico_selecao_amostra_p98_eixo_regular.png' salvo com sucesso.")

plt.show()