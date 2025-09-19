import pandas as pd
import os

# --- Configurações ---
diretorio_censo_csv = r"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_CENSO"
# Exemplo de lista das CO_ENTIDADE das suas top 10 escolas
lista_co_entidade_top10 = [53001354,33124361,23210710,43105009,41131215,26139618,31291030,29182395,50005499,31294471] # SUBSTITUA PELOS SEUS CÓDIGOS INEP

# Lista de variáveis que você quer coletar (NOMES EXATOS das colunas como nos CSVs)
# Como você confirmou que são os mesmos, não precisamos de mapeamento aqui.
variaveis_desejadas_censo = [
    'NU_ANO_CENSO', 'CO_ENTIDADE', 'NO_ENTIDADE', 'TP_DEPENDENCIA',
    'TP_LOCALIZACAO', 'SG_UF', 'NO_MUNICIPIO',
    'IN_EXAME_SELECAO', # Lembre-se que esta pode não estar em anos mais antigos
    'IN_BIBLIOTECA_SALA_LEITURA', # Ou 'IN_BIBLIOTECA' se for sempre este o nome
    'IN_LABORATORIO_CIENCIAS', 'IN_LABORATORIO_INFORMATICA',
    'IN_INTERNET', 'IN_BANDA_LARGA',
    'QT_MAT_BAS', 'QT_DOC_BAS',
    # Adicione TODAS as outras variáveis que você quer,
    # usando o nome exato que elas têm nos seus CSVs.
]

# Lista para armazenar todos os dados coletados
dados_escolas_top10_todos_anos = []

arquivos_csv_censo = [f for f in os.listdir(diretorio_censo_csv) if f.upper().endswith('.CSV') or f.lower().endswith('.csv')]
print(f"Arquivos CSV encontrados: {arquivos_csv_censo}")

for nome_arquivo in arquivos_csv_censo:
    caminho_completo_arquivo = os.path.join(diretorio_censo_csv, nome_arquivo)
    ano_censo_extraido = None # Usaremos NU_ANO_CENSO do próprio arquivo se disponível

    print(f"\nProcessando arquivo: {nome_arquivo}")

    try:
        df_censo_ano = pd.read_csv(caminho_completo_arquivo, sep=';', encoding='latin1', low_memory=False)
        print(f"  Arquivo lido. Total de linhas: {len(df_censo_ano)}, Colunas: {len(df_censo_ano.columns)}")

        # Verificar se as colunas essenciais existem
        if 'CO_ENTIDADE' not in df_censo_ano.columns:
            print(f"  AVISO: Coluna 'CO_ENTIDADE' não encontrada em {nome_arquivo}. Pulando arquivo.")
            continue
        if 'NU_ANO_CENSO' not in df_censo_ano.columns:
            print(f"  AVISO: Coluna 'NU_ANO_CENSO' não encontrada em {nome_arquivo} para usar como ano. Pulando arquivo.")
            continue # Ou tente extrair do nome do arquivo como fallback

        # Filtrar pelas escolas de interesse
        df_escolas_ano_filtrado = df_censo_ano[df_censo_ano['CO_ENTIDADE'].isin(lista_co_entidade_top10)].copy()

        if df_escolas_ano_filtrado.empty:
            print(f"  Nenhuma das escolas top 10 encontrada no arquivo {nome_arquivo}.")
            continue
        print(f"  Escolas top 10 encontradas neste arquivo: {len(df_escolas_ano_filtrado)}")

        # Selecionar apenas as colunas desejadas
        # Criar uma lista de colunas que realmente existem neste DataFrame específico
        # para evitar erros se alguma variável desejada não estiver presente em um ano específico
        colunas_presentes_neste_ano = [col for col in variaveis_desejadas_censo if col in df_escolas_ano_filtrado.columns]

        # Garantir que colunas essenciais como CO_ENTIDADE e NU_ANO_CENSO estejam na lista se não estiverem já
        if 'CO_ENTIDADE' not in colunas_presentes_neste_ano and 'CO_ENTIDADE' in df_escolas_ano_filtrado.columns:
            colunas_presentes_neste_ano.insert(0, 'CO_ENTIDADE') # Adiciona no início
        if 'NU_ANO_CENSO' not in colunas_presentes_neste_ano and 'NU_ANO_CENSO' in df_escolas_ano_filtrado.columns:
            colunas_presentes_neste_ano.insert(0, 'NU_ANO_CENSO')


        df_selecionado = df_escolas_ano_filtrado[list(set(colunas_presentes_neste_ano))].copy() # Usar set para remover duplicatas caso CO_ENTIDADE/NU_ANO_CENSO já estivessem em variaveis_desejadas_censo

        # Adicionar colunas faltantes (de variaveis_desejadas_censo) com NaN
        for col_desejada in variaveis_desejadas_censo:
            if col_desejada not in df_selecionado.columns:
                print(f"  AVISO: Variável '{col_desejada}' não encontrada em {nome_arquivo} para as escolas filtradas. Será preenchida com NaN.")
                df_selecionado[col_desejada] = pd.NA

        # Reordenar colunas para consistência (opcional, mas bom para visualização)
        # Garante que 'NU_ANO_CENSO' e 'CO_ENTIDADE' venham primeiro, se existirem.
        ordem_final_colunas = []
        if 'NU_ANO_CENSO' in df_selecionado.columns:
            ordem_final_colunas.append('NU_ANO_CENSO')
        if 'CO_ENTIDADE' in df_selecionado.columns:
            ordem_final_colunas.append('CO_ENTIDADE')

        for col in variaveis_desejadas_censo:
            if col not in ordem_final_colunas and col in df_selecionado.columns:
                ordem_final_colunas.append(col)

        # Adiciona quaisquer outras colunas que possam ter sido selecionadas (improvável com a lógica atual, mas seguro)
        for col in df_selecionado.columns:
            if col not in ordem_final_colunas:
                ordem_final_colunas.append(col)

        df_selecionado = df_selecionado[ordem_final_colunas]


        dados_escolas_top10_todos_anos.append(df_selecionado)

    except Exception as e:
        print(f"Erro ao processar o arquivo {nome_arquivo}: {e}")

if dados_escolas_top10_todos_anos:
    df_consolidado_top10 = pd.concat(dados_escolas_top10_todos_anos, ignore_index=True)
    print("\n--- Dados Consolidados (Primeiras Linhas) ---")
    print(df_consolidado_top10.head())
    df_consolidado_top10.to_csv("perfil_top10_escolas_censo_simplificado.csv", index=False, sep=';', encoding='utf-8-sig')
    print("\nDados consolidados salvos em 'perfil_top10_escolas_censo_simplificado.csv'")
else:
    print("\nNenhum dado foi coletado. Verifique os logs.")