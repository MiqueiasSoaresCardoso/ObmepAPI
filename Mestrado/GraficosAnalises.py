import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. Carregar o Resultado do Cruzamento ---

caminho_resultado_final = r"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\CRUZAMENTO OBMEP CENSO OFICIAL - RESULTADO_CRUZAMENTO_OBMEP_CENSO_LONGITUDINAL_V10 (1).csv"
try:
    df_final = pd.read_csv(caminho_resultado_final, sep=',', encoding='ISO-8859-1')
    print("Arquivo de dados cruzados carregado com sucesso!\n")
    print(df_final.columns.tolist())
except FileNotFoundError:
    print(f"Erro: Arquivo '{caminho_resultado_final}' não encontrado.")
    exit()

# Definir o ano mais recente para análise de perfil
ano_recente = df_final['ANO'].max()

# Carregar o Censo do ano mais recente
caminho_censo_recente = rf"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\CENSO ESCOLAR\microdados_ed_basica_{int(ano_recente)}.csv"
try:
    colunas_a_carregar_do_censo_total = ['TP_DEPENDENCIA', 'TP_LOCALIZACAO']
    df_censo_total_recente = pd.read_csv(
        caminho_censo_recente,
        sep=';',
        encoding='latin1',
        usecols=colunas_a_carregar_do_censo_total
    )
    print(f"Arquivo do Censo de {int(ano_recente)} carregado com sucesso.\n")
except FileNotFoundError:
    print(f"Erro: Arquivo do Censo de {int(ano_recente)} não encontrado.")
    exit()

# --- 2. Preparação do DataFrame de Análise para o Ano Recente ---
print(f"============================================================")
print(f"  ANÁLISE DE PERFIL (ANO MAIS RECENTE: {ano_recente})")
print(f"============================================================")
df_recente = df_final[df_final['ANO'] == ano_recente].drop_duplicates(subset=['CO_ENTIDADE']).copy()
print(f"Número de escolas P98 em {ano_recente}: {len(df_recente)}\n")

# --- 3. GERAÇÃO DOS GRÁFICOS E IMPRESSÃO DOS DADOS ---

# --- a) Perfil por Dependência Administrativa (GRÁFICO DE BARRAS NORMALIZADO) ---
print("\n--- a) Análise Corrigida por Dependência Administrativa ---")
# Contar total de escolas públicas no Brasil
df_censo_publicas = df_censo_total_recente[df_censo_total_recente['TP_DEPENDENCIA'].isin([1, 2, 3])]
total_escolas_por_rede = df_censo_publicas['TP_DEPENDENCIA'].value_counts()
mapa_dependencia = {1: 'Federal', 2: 'Estadual', 3: 'Municipal'}
total_escolas_por_rede.index = total_escolas_por_rede.index.map(mapa_dependencia)
print(f"\nTotal de Escolas Públicas no Brasil ({ano_recente}):\n{total_escolas_por_rede}")

# Contar escolas P98 por rede
df_recente['DESC_DEPENDENCIA'] = df_recente['TP_DEPENDENCIA'].map(mapa_dependencia)
contagem_p98_por_rede = df_recente['DESC_DEPENDENCIA'].value_counts()
print(f"\nComposição Absoluta do Grupo P98:\n{contagem_p98_por_rede}")

# Calcular taxa de sucesso
taxa_sucesso_por_rede = (contagem_p98_por_rede / total_escolas_por_rede.reindex(contagem_p98_por_rede.index)) * 100
print(f"\nTaxa de Sucesso (%) de Cada Rede:\n{taxa_sucesso_por_rede.round(2)}")

# Geração do Gráfico 1
fig1, ax1 = plt.subplots(figsize=(10, 6)) # Cria uma figura e eixos SÓ para este gráfico
sns.set_theme(style="whitegrid")
taxa_sucesso_por_rede.plot(kind='bar', ax=ax1, color=['#4c72b0', '#55a868', '#c44e52'])
ax1.set_title('Taxa de Sucesso por Dependência Administrativa (% de Escolas no Grupo P98)', fontsize=16, pad=20)
ax1.set_ylabel('Percentual de Escolas da Rede no Grupo P98 (%)', fontsize=12)
ax1.set_xlabel('Dependência Administrativa', fontsize=12)
ax1.tick_params(axis='x', rotation=0)
for p in ax1.patches:
    ax1.annotate(f"{p.get_height():.2f}%", (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=12)
fig1.tight_layout()
fig1.savefig('taxa_sucesso_dependencia.png', dpi=300)
plt.show() # Mostra e "fecha" o estado do gráfico
print("\nGráfico 'taxa_sucesso_dependencia.png' salvo.")


# --- b) Perfil por Localização (GRÁFICO DE BARRAS NORMALIZADO) ---
print("\n--- b) Análise Corrigida por Localização ---")
mapa_localizacao = {1: 'Urbana', 2: 'Rural'}
total_escolas_por_localizacao = df_censo_total_recente['TP_LOCALIZACAO'].map(mapa_localizacao).value_counts()
print(f"\nTotal de Escolas no Brasil ({ano_recente}) por Localização:\n{total_escolas_por_localizacao}")
df_recente['DESC_LOCALIZACAO'] = df_recente['TP_LOCALIZACAO'].map(mapa_localizacao)
contagem_p98_por_localizacao = df_recente['DESC_LOCALIZACAO'].value_counts()
print(f"\nComposição Absoluta do Grupo P98 por Localização:\n{contagem_p98_por_localizacao}")
taxa_sucesso_por_localizacao = (contagem_p98_por_localizacao / total_escolas_por_localizacao.reindex(contagem_p98_por_localizacao.index)) * 100
print(f"\nTaxa de Sucesso (%) de Cada Localização:\n{taxa_sucesso_por_localizacao.round(3)}")

# Geração do Gráfico 2
fig2, ax2 = plt.subplots(figsize=(8, 6)) # Nova figura e eixos
taxa_sucesso_por_localizacao.plot(kind='bar', ax=ax2, color=['#1f77b4', '#ff7f0e'])
ax2.set_title('Taxa de Sucesso por Localização (% de Escolas no Grupo P98)', fontsize=16, pad=20)
ax2.set_ylabel('Percentual de Escolas da Localização no Grupo P98 (%)', fontsize=12)
ax2.set_xlabel('Localização', fontsize=12)
ax2.tick_params(axis='x', rotation=0)
for p in ax2.patches:
    ax2.annotate(f"{p.get_height():.3f}%", (p.get_x() + p.get_width() / 2., p.get_height()), ha='center', va='center', xytext=(0, 9), textcoords='offset points', fontsize=12)
fig2.tight_layout()
fig2.savefig('taxa_sucesso_localizacao.png', dpi=300)
plt.show()
print("\nGráfico 'taxa_sucesso_localizacao.png' salvo.")


# --- c) Perfil por Porte da Escola (Boxplot) ---
print("\n--- c) Dados do Perfil por Porte da Escola (Matrículas na Ed. Básica) ---")
print(df_recente['QT_MAT_BAS'].describe().round(2))

# Geração do Gráfico 3
fig3, ax3 = plt.subplots(figsize=(10, 6)) # Nova figura e eixos
sns.boxplot(x=df_recente['QT_MAT_BAS'], color='lightgreen', ax=ax3)
ax3.set_title(f'Distribuição do Número de Alunos nas Escolas P98 ({ano_recente})', fontsize=16)
ax3.set_xlabel('Quantidade de Matrículas na Educação Básica', fontsize=12)
fig3.tight_layout()
fig3.savefig('perfil_porte_boxplot.png', dpi=300)
plt.show()
print("\nGráfico 'perfil_porte_boxplot.png' salvo.")

# --- d) Evolução da Infraestrutura (Gráfico de Linhas) ---
# ... (O código para esta parte e a próxima já é longitudinal e não deve ter o mesmo problema, mas vamos manter o padrão) ...
print("\n============================================================")
print(f"   INSIGHTS PARA O PERFIL LONGITUDINAL (2010-2023)")
print(f"============================================================")
print("\n--- d) Dados da Evolução da Infraestrutura (%) ---")

infra_vars = {'IN_BIBLIOTECA_SALA_LEITURA': 'Biblioteca/Sala de Leitura', 'IN_LABORATORIO_INFORMATICA': 'Lab. Informática', 'IN_LABORATORIO_CIENCIAS': 'Lab. Ciências', 'IN_BANDA_LARGA': 'Banda Larga', 'IN_QUADRA_ESPORTES_COBERTA': 'Quadra Coberta'}
lista_evolucao_infra = []
for ano in sorted(df_final['ANO'].unique()):
    df_ano = df_final[df_final['ANO'] == ano]
    for var_cod, var_desc in infra_vars.items():
        if var_cod in df_ano.columns:
            percentual_sim = df_ano[var_cod].value_counts(normalize=True).get(1, 0) * 100
            lista_evolucao_infra.append({'Ano': ano, 'Indicador': var_desc, 'Percentual': percentual_sim})
df_evolucao_infra = pd.DataFrame(lista_evolucao_infra)
df_evolucao_infra_print = df_evolucao_infra.pivot(index='Ano', columns='Indicador', values='Percentual').round(2)
print(df_evolucao_infra_print)

# Geração do Gráfico 4
fig4, ax4 = plt.subplots(figsize=(14, 8)) # Nova figura e eixos
sns.lineplot(data=df_evolucao_infra, x='Ano', y='Percentual', hue='Indicador', style='Indicador', markers=True, dashes=False, linewidth=2.5, ax=ax4)
ax4.set_title('Evolução da Infraestrutura nas Escolas P98 (2010-2023)', fontsize=18, pad=20)
ax4.set_xlabel('Ano', fontsize=14)
ax4.set_ylabel('Percentual de Escolas (%)', fontsize=14)
ax4.set_ylim(0, 101)
ax4.set_xticks(sorted(df_final['ANO'].unique()))
ax4.tick_params(axis='x', rotation=45, labelsize=12)
ax4.tick_params(axis='y', labelsize=12)
ax4.legend(title='Indicador de Infraestrutura', bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
fig4.tight_layout()
fig4.savefig('evolucao_infraestrutura_p98.png', dpi=300)
plt.show()
print("\nGráfico 'evolucao_infraestrutura_p98.png' salvo.")

# --- e) Gráfico de Tendência Longitudinal do Porte ---
print("\n--- e) Dados da Evolução do Número Médio de Alunos ---")
tendencia_alunos_por_ano = df_final.groupby('ANO')['QT_MAT_BAS'].mean().round(0)
print(tendencia_alunos_por_ano)

# Geração do Gráfico 5
fig5, ax5 = plt.subplots(figsize=(12, 6)) # Nova figura e eixos
tendencia_alunos_por_ano.plot(kind='line', marker='o', linestyle='-', ax=ax5)
ax5.set_title('Evolução do Número Médio de Alunos nas Escolas P98 (2010-2023)', fontsize=16)
ax5.set_xlabel('Ano', fontsize=12)
ax5.set_ylabel('Média de Alunos na Educação Básica', fontsize=12)
ax5.grid(True)
ax5.set_xticks(tendencia_alunos_por_ano.index.astype(int))
fig5.tight_layout()
fig5.savefig('tendencia_alunos_p98.png', dpi=300)
plt.show()
print("\nGráfico 'tendencia_alunos_p98.png' salvo/atualizado.")