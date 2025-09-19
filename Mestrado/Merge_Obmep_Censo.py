import pandas as pd
# import numpy as np # Removido pois np.histogram não é mais usado aqui diretamente
# import io # Removido pois não estamos gerando CSV em memória aqui

caminho_arquivo_planilha_obmep = r'C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\ESCOLAS_COM_INEP_OF.csv'

# Carregar sua planilha principal da OBMEP
try:
    df_obmep_original_com_historico = pd.read_csv(caminho_arquivo_planilha_obmep)
    print("Planilha OBMEP com histórico carregada com sucesso.")
    print(f"Colunas carregadas da planilha OBMEP: {df_obmep_original_com_historico.columns.tolist()}")

    # Padronizar nomes de colunas chave
    df_obmep_original_com_historico.rename(columns={'co_inep': 'CO_ENTIDADE', 'edicao': 'ANO'}, inplace=True)

    # Verificar se as colunas chave existem
    if 'CO_ENTIDADE' not in df_obmep_original_com_historico.columns:
        print("ERRO CRÍTICO: Coluna 'CO_ENTIDADE' (renomeada de 'co_inep') não encontrada. Verifique o CSV.")
        exit()
    if 'ANO' not in df_obmep_original_com_historico.columns:
        print("ERRO CRÍTICO: Coluna 'ANO' (renomeada de 'edicao') não encontrada. Verifique o CSV.")
        exit()

    # Garantir tipos corretos para as chaves de merge
    df_obmep_original_com_historico['CO_ENTIDADE'] = df_obmep_original_com_historico['CO_ENTIDADE'].astype(str)
    df_obmep_original_com_historico['ANO'] = df_obmep_original_com_historico['ANO'].astype(int)

    print(f"Shape da planilha OBMEP original com histórico: {df_obmep_original_com_historico.shape}")

except FileNotFoundError:
    print(f"Erro: Arquivo '{caminho_arquivo_planilha_obmep}' não encontrado.")
    exit()
except Exception as e:
    print(f"Erro ao carregar ou processar a planilha OBMEP: {e}")
    exit()

# --- Passo Adicional: Criar o esqueleto longitudinal para as escolas P98 ---
# 1. Obter a lista única de INEPs P98 e suas informações fixas
#    (nome, uf, municipio, pontuacao_total_periodo, total_medalhas_simples_periodo)
#    As colunas 'pontuacao_ponderada_total_2010_2023' e 'total_medalhas_simples_2010_2023'
#    são as mesmas para todas as linhas de uma mesma escola na sua planilha original.
colunas_info_fixa_escola = ['CO_ENTIDADE', 'escola', 'uf', 'municipio',
                            'pontuacao_ponderada_total_2010_2023',
                            'total_medalhas_simples_2010_2023']
df_info_escolas_p98_unicas = df_obmep_original_com_historico[colunas_info_fixa_escola].drop_duplicates(subset=['CO_ENTIDADE']).copy()
ineps_p98_unicos = df_info_escolas_p98_unicas['CO_ENTIDADE'].unique()
print(f"Número de escolas P98 únicas identificadas: {len(ineps_p98_unicos)}") # Deve ser 350

# 2. Criar o DataFrame esqueleto com todas as combinações (CO_ENTIDADE, ANO)
anos_periodo_completo = range(2010, 2024) # 2010 a 2023
df_esqueleto_longitudinal = pd.MultiIndex.from_product(
    [ineps_p98_unicos, anos_periodo_completo],
    names=['CO_ENTIDADE', 'ANO']
).to_frame(index=False)
print(f"DataFrame esqueleto criado com shape: {df_esqueleto_longitudinal.shape}")

# 3. Merge do esqueleto com os dados detalhados anuais da OBMEP
# Selecionar apenas as colunas relevantes do histórico da OBMEP para o merge
colunas_historico_obmep = ['CO_ENTIDADE', 'ANO', 'total_medalhas_na_edicao',
                           'medalhas_nivel_1', 'medalhas_nivel_2', 'medalhas_nivel_3']
# Adicione outras colunas de medalhas se houver (ex: pontuação ponderada anual da OBMEP, se calculada)

# Filtrar df_obmep_original_com_historico para ter apenas as colunas de histórico necessárias para o merge
# e garantir que não haja duplicatas de (CO_ENTIDADE, ANO) se uma escola por acaso tiver mais de uma linha por ano
# (o que não deveria acontecer com os dados de medalhas agregados por ano)
df_obmep_historico_para_merge = df_obmep_original_com_historico[colunas_historico_obmep].drop_duplicates(subset=['CO_ENTIDADE', 'ANO'])


df_obmep_painel_parcial = pd.merge(
    df_esqueleto_longitudinal,
    df_obmep_historico_para_merge, # Sua planilha OBMEP com histórico anual de medalhas
    on=['CO_ENTIDADE', 'ANO'],
    how='left'
)

# 4. Preencher NaN nas colunas de medalhas com 0
colunas_medalhas_a_zerar = ['total_medalhas_na_edicao', 'medalhas_nivel_1', 'medalhas_nivel_2', 'medalhas_nivel_3']
for col in colunas_medalhas_a_zerar:
    if col in df_obmep_painel_parcial.columns:
        df_obmep_painel_parcial[col].fillna(0, inplace=True)
    else:
        # Se a coluna não existir, cria com zeros.
        # Isso pode acontecer se nenhuma escola tiver medalha daquele tipo/nível em nenhum ano.
        df_obmep_painel_parcial[col] = 0


# 5. Adicionar as informações fixas da escola de volta ao painel
df_obmep_painel_completo = pd.merge(
    df_obmep_painel_parcial,
    df_info_escolas_p98_unicas,
    on='CO_ENTIDADE',
    how='left' # 'left' é apropriado aqui, pois todas as CO_ENTIDADE no painel parcial vieram de df_info_escolas_p98_unicas
)

print(f"Shape do df_obmep_painel_completo (com todos os anos para escolas P98): {df_obmep_painel_completo.shape}")
print("Verificando algumas linhas do painel OBMEP completo:")
print(df_obmep_painel_completo.head(20))
# Verifique se escolas que não tiveram medalhas em certos anos agora têm 0 nessas colunas.

# --- Agora df_obmep_painel_completo é o seu "lado esquerdo" para o merge com o Censo ---

# --- Definição das Colunas do Censo (como antes) ---
colunas_censo_interesse_obrigatorias = ['CO_ENTIDADE', 'NU_ANO_CENSO']
colunas_censo_perfil_sugeridas = [
    'TP_DEPENDENCIA', 'TP_LOCALIZACAO', 'SG_UF', 'NO_MUNICIPIO', 'CO_MUNICIPIO',
    'TP_SITUACAO_FUNCIONAMENTO', 'QT_MAT_BAS', 'QT_MAT_FUND_AF', 'QT_MAT_MED',
    'QT_TUR_BAS', 'QT_TUR_FUND_AF', 'QT_TUR_MED', 'IN_BIBLIOTECA', 'IN_SALA_LEITURA',
    'IN_LABORATORIO_INFORMATICA', 'IN_LABORATORIO_CIENCIAS', 'IN_QUADRA_ESPORTES_COBERTA',
    'IN_INTERNET', 'IN_BANDA_LARGA', 'QT_COMP_ALUNO', 'IN_AGUA_POTAVEL',
    'IN_ENERGIA_REDE_PUBLICA', 'IN_ESGOTO_REDE_PUBLICA', 'IN_ACESSIBILIDADE_RAMPAS',
    'IN_BANHEIRO_PNE', 'QT_DOC_BAS', 'QT_DOC_FUND_AF', 'QT_DOC_MED',
    'IN_EXAME_SELECAO', 'IN_ORGAO_CONSELHO_ESCOLAR', 'IN_ORGAO_GREMIO_ESTUDANTIL',
    'IN_ALIMENTACAO', 'IN_VINCULO_SEGURANCA_PUBLICA',
    'IN_VINCULO_SECRETARIA_EDUCACAO', 'IN_VINCULO_SECRETARIA_SAUDE',
    'IN_VINCULO_OUTRO_ORGAO'
]
colunas_censo_interesse = list(set([col.upper() for col in colunas_censo_interesse_obrigatorias] + \
                                   [col.upper() for col in colunas_censo_perfil_sugeridas]))
print(f"\nColunas de interesse selecionadas do Censo (Total: {len(colunas_censo_interesse)}):")

# --- Loop Anual e Merge com Censo (como antes) ---
df_censo_longitudinal_completo = pd.DataFrame()
anos_censo = range(2010, 2024)

for ano in anos_censo:
    try:
        caminho_arquivo_censo = rf"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\CENSO ESCOLAR\microdados_ed_basica_{ano}.csv"
        print(f"Processando Censo Escolar do ano: {ano} de {caminho_arquivo_censo}...")
        df_censo_anual_raw = pd.read_csv(caminho_arquivo_censo, sep=';', encoding='latin1', low_memory=False)
        df_censo_anual_raw.columns = [col.upper() for col in df_censo_anual_raw.columns]

        cols_necessarias_censo = colunas_censo_interesse.copy()
        if 'NU_ANO_CENSO' not in cols_necessarias_censo: cols_necessarias_censo.append('NU_ANO_CENSO')
        if 'CO_ENTIDADE' not in cols_necessarias_censo: cols_necessarias_censo.append('CO_ENTIDADE')

        colunas_existentes_no_df_censo = [col for col in cols_necessarias_censo if col in df_censo_anual_raw.columns]
        df_censo_anual = df_censo_anual_raw[colunas_existentes_no_df_censo].copy()

        if 'NU_ANO_CENSO' in df_censo_anual.columns:
            df_censo_anual.rename(columns={'NU_ANO_CENSO': 'ANO'}, inplace=True)
        elif 'ANO' not in df_censo_anual.columns:
            df_censo_anual['ANO'] = int(ano)
        else:
            df_censo_anual['ANO'] = df_censo_anual['ANO'].astype(int)

        if 'CO_ENTIDADE' not in df_censo_anual.columns:
            print(f"AVISO: Coluna 'CO_ENTIDADE' não encontrada no Censo de {ano}.")
            continue
        df_censo_anual['CO_ENTIDADE'] = df_censo_anual['CO_ENTIDADE'].astype(str)
        df_censo_anual['ANO'] = df_censo_anual['ANO'].astype(int)

        df_censo_longitudinal_completo = pd.concat([df_censo_longitudinal_completo, df_censo_anual], ignore_index=True)
        print(f"Dados do Censo {ano} adicionados. Shape atual: {df_censo_longitudinal_completo.shape}")
    except FileNotFoundError:
        print(f"AVISO: Arquivo do Censo para o ano {ano} não encontrado. Pulando.")
    except Exception as e:
        print(f"Erro ao processar Censo {ano}: {e}")

# Merge Final
if not df_censo_longitudinal_completo.empty and not df_obmep_painel_completo.empty :
    print("\nIniciando cruzamento final com dados da OBMEP (painel completo)...")
    df_final_cruzado = pd.merge(
        df_obmep_painel_completo, # <<-- USA O PAINEL COMPLETO DA OBMEP
        df_censo_longitudinal_completo,
        on=['CO_ENTIDADE', 'ANO'],
        how='left'
    )
    print(f"Shape do DataFrame OBMEP Painel Completo: {df_obmep_painel_completo.shape}")
    print(f"Shape do DataFrame Censo Agregado: {df_censo_longitudinal_completo.shape}")
    print(f"Shape do DataFrame Final Cruzado: {df_final_cruzado.shape}")

    if 'TP_DEPENDENCIA' in df_final_cruzado.columns:
        print(f"Registros com match em TP_DEPENDENCIA: {df_final_cruzado['TP_DEPENDENCIA'].notna().sum()}")
        print(f"Registros sem match em TP_DEPENDENCIA (NaN): {df_final_cruzado['TP_DEPENDENCIA'].isna().sum()}")
    else:
        print("Coluna TP_DEPENDENCIA não encontrada no resultado do merge para verificação.")

    df_final_cruzado.to_csv('RESULTADO_CRUZAMENTO_OBMEP_CENSO_LONGITUDINAL_V12.csv', index=False, sep=';', encoding='utf-8-sig')
    print("Arquivo RESULTADO_CRUZAMENTO_OBMEP_CENSO_LONGITUDINAL_V12.csv salvo!")
else:
    if df_censo_longitudinal_completo.empty:
        print("Nenhum dado do Censo foi carregado. O cruzamento não pode ser realizado.")
    if df_obmep_painel_completo.empty:
        print("Painel OBMEP completo está vazio. Verifique os passos anteriores.")

        # Verifica quais escolas da OBMEP não conseguiram se cruzar com o Censo
escolas_obmep = df_obmep_painel_completo['CO_ENTIDADE'].drop_duplicates()
escolas_cruzadas = df_final_cruzado[df_final_cruzado['TP_DEPENDENCIA'].notna()]['CO_ENTIDADE'].drop_duplicates()

# Diferença entre elas
escolas_sem_censo = escolas_obmep[~escolas_obmep.isin(escolas_cruzadas)]

print(f"\nTotal de escolas na OBMEP: {len(escolas_obmep)}")
print(f"Total de escolas após cruzamento com o Censo: {len(escolas_cruzadas)}")
print(f"Escolas sem dados do Censo: {len(escolas_sem_censo)}")

# Mostrar ou salvar as escolas ausentes
escolas_faltando_info = df_obmep_painel_completo[df_obmep_painel_completo['CO_ENTIDADE'].isin(escolas_sem_censo)]
escolas_faltando_info[['CO_ENTIDADE', 'escola', 'uf', 'municipio']].drop_duplicates().to_csv('escolas_sem_dados_censo.csv', index=False, encoding='utf-8-sig')
