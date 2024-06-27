import pandas as pd
from pymongo import MongoClient

# Passo 1: Configurar a conexão com o MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['Obmep']
collection = db['Escola']

# Passo 3: Ler os dados do CSV para um DataFrame
csv_file_path = "C:\\Users\\mique\\Downloads\\obmep.csv"
try:
    df = pd.read_csv(csv_file_path, delimiter=';', encoding='latin1')  # Tente alterar o delimitador se necessário
except pd.errors.ParserError:
    df = pd.read_csv(csv_file_path, delimiter=',', encoding='latin1')

# Passo 4: Converter o DataFrame para uma lista de dicionários
data_dict = df.to_dict(orient="records")

# Passo 5: Inserir os dados na coleção do MongoDB
collection.insert_many(data_dict)

print("Dados inseridos com sucesso!")

