import pandas as pd

caminho = r"C:\Users\mique\OneDrive\Área de Trabalho\DADOS_CENSO\INSE\INSE_2011_2013 - INSE_2011_2013.csv.csv"

escolas_inse = pd.read_csv(caminho, encoding='latin1', sep=';', header=9)
escolas_inse.columns = escolas_inse.columns.str.strip()

print(escolas_inse.columns.tolist())
for col in escolas_inse.columns:
    print(f"'{col}'")

# Encontra o nome exato da coluna parecida com 'COD_ESCOLA'
for col in escolas_inse.columns:
    if 'COD_ESCOLA' in col:
        print(f"Coluna encontrada: '{col}'")
        escolas_inse['CO_ENTIDADE'] = escolas_inse[col]
        break



print(escolas_inse.columns.tolist())


# Criando a coluna ANO_CENSO com base na coluna 'edicao'
escolas_inse['CO_ENTIDADE'] = escolas_inse['COD_ESCOLA']

# Conferindo rapidamente
print(escolas_inse[['CO_ENTIDADE', 'COD_ESCOLA', 'NOME_ESCOLA']].head())
