import pandas as pd
from pymongo import MongoClient
from unidecode import unidecode
#
# Passo 1: Configurar a conexão com o MongoDB
uri = "mongodb+srv://miqueiassoares:pMmAke6bpsOI8u6T@cluster0.sjuug1b.mongodb.net/Obmep"
client = MongoClient(uri, ssl=True)
db = client['Obmep']
#collection = db['Aluno']
collection = db['Aluno2']

# Passo 3: Ler os dados do CSV para um DataFrame
#csv_file_path = "C:\\Users\\mique\\Downloads\\obmep.csv"
csv_file_path = "C:\\Users\\mique\\IdeaProjects\\Obmep\\Mestrado\\obmep_v2.csv"
try:
    df = pd.read_csv(csv_file_path, delimiter=';', encoding='latin1')  # Tente alterar o delimitador se necessário
except pd.errors.ParserError:
    df = pd.read_csv(csv_file_path, delimiter=',', encoding='latin1')

#Passo 4: Remover acentos
if 'municipio' in df.columns:
    df['municipio'] = df['municipio'].apply(unidecode)

# Passo 4: Converter o DataFrame para uma lista de dicionários
data_dict = df.to_dict(orient="records")

# Passo 5: Inserir os dados na coleção do MongoDB
collection.insert_many(data_dict)

print("Dados inseridos com sucesso!")

