import pandas as pd

#Código para Inserção de Dados Faltantes após cruzamento de dados da OBMEP com o Censo

# Lista direta dos códigos INEP (CO_ENTIDADE) das escolas faltantes
ineps_faltantes = [
    '35990012',
    '15167216',
    '26138875',
    '41128249',
    '13103377',
    '43000231',
    '35456512',
    '31067873',
    '14006871',
    '23238933',
    '35046024',
    '23252235',
    '33130426',
    '31000576',
    '35462792'
]

print(f'Total de escolas faltantes: {len(ineps_faltantes)}')

# Ordem personalizada das colunas para o CSV final
ordem_colunas_final = [
    'IN_SALA_LEITURA', 'IN_VINCULO_OUTRO_ORGAO', 'TP_DEPENDENCIA', 'IN_BANHEIRO_PNE',
    'IN_BIBLIOTECA', 'IN_ORGAO_GREMIO_ESTUDANTIL', 'IN_VINCULO_SEGURANCA_PUBLICA', 'QT_MAT_FUND_AF',
    'IN_QUADRA_ESPORTES_COBERTA', 'IN_ENERGIA_REDE_PUBLICA', 'IN_ALIMENTACAO', 'QT_TUR_BAS',
    'IN_EXAME_SELECAO', 'IN_LABORATORIO_CIENCIAS', 'QT_DOC_FUND_AF', 'IN_AGUA_POTAVEL',
    'IN_BANDA_LARGA', 'NO_MUNICIPIO', 'QT_DOC_BAS', 'IN_LABORATORIO_INFORMATICA', 'IN_INTERNET',
    'IN_ORGAO_CONSELHO_ESCOLAR', 'TP_LOCALIZACAO', 'IN_VINCULO_SECRETARIA_EDUCACAO', 'QT_COMP_ALUNO',
    'TP_SITUACAO_FUNCIONAMENTO', 'QT_MAT_MED', 'IN_ESGOTO_REDE_PUBLICA', 'IN_VINCULO_SECRETARIA_SAUDE',
    'SG_UF', 'QT_MAT_BAS', 'QT_TUR_FUND_AF', 'QT_DOC_MED', 'CO_MUNICIPIO', 'IN_ACESSIBILIDADE_RAMPAS',
    'QT_TUR_MED'
]

# Adiciona colunas obrigatórias no início
colunas_padrao = ['CO_ENTIDADE', 'ANO'] + ordem_colunas_final

# Acumulador
df_censo_faltantes = pd.DataFrame()

for ano in range(2010, 2024):
    try:
        caminho_censo = fr"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_PESQUISA\CENSO ESCOLAR\microdados_ed_basica_{ano}.csv"
        print(f"🔄 Processando Censo {ano}...")

        df_raw = pd.read_csv(caminho_censo, sep=';', encoding='latin1', low_memory=False)
        df_raw.columns = [col.upper() for col in df_raw.columns]

        df_raw['CO_ENTIDADE'] = df_raw['CO_ENTIDADE'].astype(str)
        df_filtrado = df_raw[df_raw['CO_ENTIDADE'].isin(ineps_faltantes)]

        # Renomeia ano se necessário
        if 'NU_ANO_CENSO' in df_filtrado.columns:
            df_filtrado.rename(columns={'NU_ANO_CENSO': 'ANO'}, inplace=True)
        else:
            df_filtrado['ANO'] = ano

        # Seleciona apenas colunas existentes e da ordem correta
        colunas_presentes = [col for col in colunas_padrao if col in df_filtrado.columns]
        df_filtrado = df_filtrado[colunas_presentes].copy()

        # Garante ordem desejada (preenche colunas ausentes com NaN)
        for col in colunas_padrao:
            if col not in df_filtrado.columns:
                df_filtrado[col] = pd.NA
        df_filtrado = df_filtrado[colunas_padrao]

        df_censo_faltantes = pd.concat([df_censo_faltantes, df_filtrado], ignore_index=True)
        print(f"✅ {df_filtrado.shape[0]} registros adicionados de {ano}.")

    except FileNotFoundError:
        print(f"⚠️ Arquivo não encontrado para {ano}")
    except Exception as e:
        print(f"❌ Erro no ano {ano}: {e}")

# Salva o resultado com separador ; e encoding UTF-8 com BOM
df_censo_faltantes.to_csv('DADOS_CENSO_ESCOLAS_FALTANTES_V02.csv', sep=';', index=False, encoding='utf-8-sig')
print("\n✅ Arquivo 'DADOS_CENSO_ESCOLAS_FALTANTES.csv' salvo com colunas na ordem correta.")
