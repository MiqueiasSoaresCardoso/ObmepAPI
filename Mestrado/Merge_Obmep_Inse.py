import pandas as pd

# --- 1. Definir Caminhos dos Arquivos ---
caminho_base_principal = r"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\CRUZAMENTO OBMEP CENSO OFICIAL - RESULTADO_CRUZAMENTO_OBMEP_CENSO_LONGITUDINAL_V10 (1).csv" # SEU ARQUIVO ATUAL"
# Ajuste os caminhos para onde você salvou seus microdados de INSE
# NOVO: Caminho para o arquivo que contém 2011 e 2013 juntos
caminho_inse_2011_2013_junto = r"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\INSE\INSE_2011_2013.csv" # ATENÇÃO: VERIFIQUE O NOME CORRETO DO SEU ARQUIVO
caminho_inse_2015 = r"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\INSE\INSE_2015.csv"
caminho_inse_2019 = r"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\INSE\INSE_2019.csv"
caminho_inse_2021 = r"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\INSE\INSE_2021.csv" # Confirme o nome do arquivo 2021

# --- 2. Carregar a Base Principal (OBMEP + Censo) ---
try:
    df_painel_final = pd.read_csv(caminho_base_principal, sep=',', encoding='utf-8-sig') # Ajuste sep e encoding se necessário
    print(f"Base principal carregada. Shape: {df_painel_final.shape}")
    print(f"Colunas da base principal: {df_painel_final.columns.tolist()}\n")

    # Garante que as chaves de merge estão nos formatos corretos
    df_painel_final['CO_ENTIDADE'] = df_painel_final['CO_ENTIDADE'].astype(str)
    df_painel_final['ANO'] = df_painel_final['ANO'].astype(int)

except FileNotFoundError:
    print(f"Erro: Base principal '{caminho_base_principal}' não encontrada.")
    exit()
except Exception as e:
    print(f"Erro ao carregar a base principal: {e}")
    exit()

# Lista de INEPs das 315 escolas para filtrar as bases secundárias
ineps_p98 = df_painel_final['CO_ENTIDADE'].unique()
print(f"INSEs únicos das escolas P98 na base principal: {len(ineps_p98)}\n")

# --- 3. Função Auxiliar para Carregar e Preparar Dados Secundários (SEM RENOMEAÇÃO) ---
def carregar_e_preparar_dados_secundarios(caminho_arquivo, colunas_interesse_csv, sep=',', encoding='latin1', filtrar_inep=True):
    try:
        # Adicionar 'NU_ANO_CENSO' à usecols caso a base tenha essa coluna de ano
        cols_to_load = list(set(colunas_interesse_csv + ['NU_ANO_CENSO'])) # Adiciona NU_ANO_CENSO para carregar se existir

        df = pd.read_csv(caminho_arquivo, sep=sep, encoding=encoding, usecols=cols_to_load, header=0)
        df.columns = [col.upper() for col in df.columns] # Padroniza para MAIÚSCULAS para consistência interna

        # NOVO: Priorizar a coluna de ano do próprio arquivo, se existir (como NU_ANO_CENSO)
        if 'NU_ANO_CENSO' in df.columns:
            df.rename(columns={'NU_ANO_CENSO': 'ANO'}, inplace=True)
        elif 'ANO' not in df.columns: # Se não tiver nenhuma coluna de ano no arquivo, é um problema para INSE combinado
            # Isso pode indicar que o arquivo é de um ano único e a coluna 'ANO' não existe.
            # Neste caso, a função `carregar_e_preparar_dados_secundarios` não deve ser usada para um `ano_fixo`.
            # Ou o arquivo combinado não tem coluna de ano e isso é um erro.
            raise ValueError(f"Arquivo INSE '{caminho_arquivo.split('/')[-1]}' não contém coluna de ano ('NU_ANO_CENSO' ou 'ANO').")

        # Garantir tipos corretos para as chaves de merge
        if 'CO_ENTIDADE' in df.columns:
            df['CO_ENTIDADE'] = df['CO_ENTIDADE'].astype(str)
        if 'CO_MUNICIPIO' in df.columns: # Para IDHM
            df['CO_MUNICIPIO'] = df['CO_MUNICIPIO'].astype(str)
        if 'ANO' in df.columns:
            df['ANO'] = df['ANO'].astype(int)

        # Filtrar apenas as escolas do seu grupo P98, se aplicável
        if filtrar_inep and 'CO_ENTIDADE' in df.columns:
            df = df[df['CO_ENTIDADE'].isin(ineps_p98)].copy()

        # CORREÇÃO DO ERRO DA F-STRING:
        nome_arquivo_curto = caminho_arquivo.split('\\')[-1] # Obtém o nome do arquivo aqui
        print(f"  - Carregado {nome_arquivo_curto}. Shape: {df.shape}")
        return df
    except FileNotFoundError:
        nome_arquivo_curto = caminho_arquivo.split('\\')[-1] # Obtém o nome do arquivo aqui
        print(f"  - AVISO: Arquivo '{nome_arquivo_curto}' não encontrado. Pulando.")
        return pd.DataFrame()
    except Exception as e:
        nome_arquivo_curto = caminho_arquivo.split('\\')[-1] # Obtém o nome do arquivo aqui
        print(f"  - ERRO ao carregar {nome_arquivo_curto}: {e}. Retornando DataFrame vazio.")
        return pd.DataFrame()



# --- 4. Integração dos Dados do INSE ---
print("\n--- Integrando Dados do INSE ---")
dfs_inse = []

# COLUNAS DO INSE CONFORME VOCÊ FORNECEU (EXATAMENTE COMO ESTÃO NO SEU CSV)
# ADICIONADO 'NU_ANO_CENSO' à lista, pois ele PRECISA estar no arquivo combinado para identificar os anos
colunas_inse_interesse_csv_originais = [
    'CO_ENTIDADE',
    'INSE_CLASSIFICACAO'
]

# Lista de caminhos para os arquivos INSE
caminhos_inse_a_processar = [
    caminho_inse_2011_2013_junto, # Arquivo combinado
    caminho_inse_2015,
    caminho_inse_2019,
    caminho_inse_2021
]

for caminho_inse_arquivo in caminhos_inse_a_processar:
    df_inse_ano = carregar_e_preparar_dados_secundarios(
        caminho_inse_arquivo,
        colunas_inse_interesse_csv_originais,
        sep=',', # **CRÍTICO: VERIFIQUE SE O INSE É SEPARADO POR VÍRGULA (',') OU PONTO E VÍRGULA (';')**
        encoding='latin1'
    )
    if not df_inse_ano.empty:
        dfs_inse.append(df_inse_ano)

if dfs_inse:
    df_inse_longitudinal = pd.concat(dfs_inse, ignore_index=True)

    # Remove possíveis duplicatas de (CO_ENTIDADE, ANO) no INSE antes do merge final, se houver
    df_inse_longitudinal.drop_duplicates(subset=['CO_ENTIDADE', 'ANO'], inplace=True)

    # Colunas do INSE que queremos mesclar para df_painel_final
    # Usamos os nomes ORIGINAIS (em maiúsculas, pois a função já os padroniza)
    # Certifique-se de que os nomes abaixo são os que você quer no seu DF final
    # e que eles realmente existem no df_inse_longitudinal
    cols_para_merge_inse_final = [
        'CO_ENTIDADE', 'ANO', 'MEDIA_INSE', 'INSE_CLASSIFICACAO', 'QTD_ALUNOS_INSE',
        'PC_NIVEL_1', 'PC_NIVEL_2', 'PC_NIVEL_3', 'PC_NIVEL_4', 'PC_NIVEL_5',
        'PC_NIVEL_6', 'PC_NIVEL_7', 'PC_NIVEL_8'
        # NO_ESCOLA e TP_TIPO_REDE geralmente não são mescladas do INSE para evitar redundância/conflito com Censo
    ]
    cols_para_merge_inse_final = [col for col in cols_para_merge_inse_final if col in df_inse_longitudinal.columns]


    df_painel_final = pd.merge(
        df_painel_final,
        df_inse_longitudinal[cols_para_merge_inse_final],
        on=['CO_ENTIDADE', 'ANO'],
        how='left'
    )
    print(f"INSE integrado. Shape atual: {df_painel_final.shape}\n")
else:
    print("Nenhum dado de INSE integrado.\n")


# --- 5. Salvar o DataFrame Final Após Integração do INSE ---
output_caminho_final_inse = r"RESULTADO_CRUZAMENTO_OBMEP_CENSO_INSE.csv" # Nome do arquivo final após INSE
df_painel_final.to_csv(output_caminho_final_inse, index=False, sep=';', encoding='utf-8-sig')
print(f"\nDataset com OBMEP + Censo + INSE salvo em: '{output_caminho_final_inse}'")
print(f"Shape final do dataset: {df_painel_final.shape}")

print("\nVerificação de valores ausentes para colunas INSE (top 5):")
# Use os nomes das colunas como elas aparecerão no DataFrame final (em maiúsculas)
cols_inse_check = [
    'MEDIA_INSE', 'INSE_CLASSIFICACAO', 'QTD_ALUNOS_INSE', 'PC_NIVEL_1', 'PC_NIVEL_2'
    # Adicione outras colunas INSE que você espera para verificar NaNs
]
cols_inse_check_present = [col for col in cols_inse_check if col in df_painel_final.columns]

if cols_inse_check_present:
    print(df_painel_final[cols_inse_check_present].isnull().sum().sort_values(ascending=False).head(5))
else:
    print("Nenhuma das colunas INSE esperadas encontrada para verificação de NaNs.")

print("\nPrimeiras 10 linhas do dataset final com INSE (após merge):")
print(df_painel_final.head(10))