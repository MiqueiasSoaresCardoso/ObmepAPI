import ssl

from flask import Flask, jsonify, request
from pymongo import MongoClient
import os

# Configuração da conexão com MongoDB Atlas
uri = "mongodb+srv://miqueiassoares:pMmAke6bpsOI8u6T@cluster0.sjuug1b.mongodb.net/Obmep"

client = MongoClient(uri, ssl=True)
db = client['Obmep']
collection = db['Escola']

app = Flask(__name__)


# ENDPOINT - 02
# Dentro de um determinado estado, selecionando o nível e a edição da olimpíada, conseguir visualizar qual instituição mais se destacou nas premiações
@app.route('/api/buscarinstituicaoestado', methods=['GET'])
def buscarinstituicao():
    estado = request.args.get('estado', default='PB', type=str)
    nivel = request.args.get('nivel', default=3, type=int)
    edicao = request.args.get('edicao', default=2023, type=int)

    pipeline = [
        {
            '$match': {
                'uf': estado,
                'nivel': nivel,
                'edicao': edicao
            }
        },
        {
            '$group': {
                '_id': '$escola',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                'total_premiacoes': -1
            }
        },
        {
            '$limit': 1  # Limitando para exibir apenas a instituição com mais premiações
        }
    ]

    resultados = list(collection.aggregate(pipeline))

    if resultados:
        return jsonify({
            'estado': estado,
            'nivel': nivel,
            'edicao': edicao,
            'instituicao': resultados[0]['_id'],
            'total_premiacoes': resultados[0]['total_premiacoes'],
        }), 200
    else:
        return jsonify({'message': 'Nenhuma instituição encontrada para os critérios especificados'}), 404
#-----------------------------------------------------------------------------------------------------------------------------------------------------
# ENDPOINT - Buscar instituição mais destacada em um município
@app.route('/api/buscarinstituicaomunicipio', methods=['GET'])
def buscar_instituicao_municipio():
    municipio = request.args.get('municipio', default='São Paulo', type=str)
    nivel = request.args.get('nivel', default=3, type=int)
    edicao = request.args.get('edicao', default=2023, type=int)

    pipeline = [
        {
            '$match': {
                'municipio': municipio,
                'nivel': nivel,
                'edicao': edicao
            }
        },
        {
            '$group': {
                '_id': '$escola',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                'total_premiacoes': -1
            }
        },
        {
            '$limit': 1  # Limitando para exibir apenas a instituição com mais premiações
        }
    ]

    resultados = list(collection.aggregate(pipeline))

    if resultados:
        return jsonify({
            'municipio': municipio,
            'nivel': nivel,
            'edicao': edicao,
            'instituicao': resultados[0]['_id'],
            'total_premiacoes': resultados[0]['total_premiacoes'],
        }), 200
    else:
        return jsonify({'message': 'Nenhuma instituição encontrada para os critérios especificados'}), 404


# ENDPOINT - Comparar desempenho entre escolas Estaduais e Municipais em um estado específico
@app.route('/api/comparar-desempenho-municipio', methods=['GET'])
def comparar_desempenho_muni():
    municipio = request.args.get('estado', default='PB', type=str)
    nivel = request.args.get('nivel', default=1, type=int)

    pipeline_municipais = [
        {
            '$match': {
                'municipio': municipio,
                'nivel': nivel,
                'tipo': 'M'
            }
        },
        {
            '$group': {
                '_id': '$escola',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                'total_premiacoes': -1
            }
        },
        {
            '$limit': 5  # Limitando para exibir as top 5 escolas Federais
        }
    ]

    pipeline_estaduais = [
        {
            '$match': {
                'uf': municipio,
                'nivel': nivel,
                'tipo': 'E'
            }
        },
        {
            '$group': {
                '_id': '$escola',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                'total_premiacoes': -1
            }
        },
        {
            '$limit': 5  # Limitando para exibir as top 5 escolas Estaduais
        }
    ]

    resultados_municipais = list(collection.aggregate(pipeline_municipais))
    resultados_estaduais = list(collection.aggregate(pipeline_estaduais))

    # Preparando resposta
    response = {
        'municipio': municipio,
        'nivel': nivel,
        'escolas_municipais:': [],
        'escolas_estaduais': []
    }

    # Adicionando escolas Federais no resultado
    for idx, resultado in enumerate(resultados_municipais):
        response['escolas_municipais'].append({
            'posicao': idx + 1,
            'instituicao': resultado['_id'],
            'total_premiacoes': resultado['total_premiacoes']
        })

    # Adicionando escolas Estaduais no resultado
    for idx, resultado in enumerate(resultados_estaduais):
        response['escolas_estaduais'].append({
            'posicao': idx + 1,
            'instituicao': resultado['_id'],
            'total_premiacoes': resultado['total_premiacoes']
        })

    return jsonify(response), 200

#Metodo para comparar desempenho entre escolas Estaduais e Federais no nivel 3 em um Estado especifico (Ensino Médio)
@app.route('/api/comparar-desempenho', methods=['GET'])
def comparar_desempenho():
    estado = request.args.get('estado', default='PB', type=str)
    nivel = 3  # Considerando apenas o nível 3 (Ensino médio)

    pipeline_federais = [
        {
            '$match': {
                'uf': estado,
                'nivel': nivel,
                'tipo': 'Federal'
            }
        },
        {
            '$group': {
                '_id': '$escola',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                'total_premiacoes': -1
            }
        },
        {
            '$limit': 5  # Limitando para exibir as top 5 escolas Federais
        }
    ]

    pipeline_estaduais = [
        {
            '$match': {
                'uf': estado,
                'nivel': nivel,
                'tipo': 'Estadual'
            }
        },
        {
            '$group': {
                '_id': '$escola',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                'total_premiacoes': -1
            }
        },
        {
            '$limit': 5  # Limitando para exibir as top 5 escolas Estaduais
        }
    ]

    resultados_federais = list(collection.aggregate(pipeline_federais))
    resultados_estaduais = list(collection.aggregate(pipeline_estaduais))

    # Preparando resposta
    response = {
        'estado': estado,
        'nivel': nivel,
        'escolas_federais': [],
        'escolas_estaduais': []
    }

    # Adicionando escolas Federais no resultado
    for idx, resultado in enumerate(resultados_federais):
        response['escolas_federais'].append({
            'posicao': idx + 1,
            'instituicao': resultado['_id'],
            'total_premiacoes': resultado['total_premiacoes']
        })

    # Adicionando escolas Estaduais no resultado
    for idx, resultado in enumerate(resultados_estaduais):
        response['escolas_estaduais'].append({
            'posicao': idx + 1,
            'instituicao': resultado['_id'],
            'total_premiacoes': resultado['total_premiacoes']
        })

    return jsonify(response), 200

# ENDPOINT - Exibir Ranking por estados e tipo de premiação
@app.route('/api/ranking', methods=['GET'])
def ranking_por_estado():
    estado = request.args.get('estado', type=str)
    medalha = request.args.get('medalha', type=str)  # Pode ser 'ouro', 'prata', 'bronze' ou 'todas'
    edicao = request.args.get('edicao', type=int)

    match_filter = {
        'uf': estado,
        'edicao': edicao
    }

    if medalha and medalha != 'todas':
        match_filter['tipo'] = medalha

    pipeline = [
        {
            '$match': match_filter
        },
        {
            '$group': {
                '_id': '$instituicao',
                'total_premios': {'$sum': 1},
                'medalha': {'$first': '$medalha'}  # Para garantir que o tipo seja o mesmo para a instituição
            }
        },
        {
            '$sort': {
                'total_premios': -1
            }
        }
    ]

    resultados = list(collection.aggregate(pipeline))

    # Preparando resposta
    response = {
        'estado': estado,
        'tipo_premiacao': medalha if medalha else 'todas',
        'edicao': edicao,
        'ranking': []
    }

    for idx, resultado in enumerate(resultados):
        response['ranking'].append({
            'posicao': idx + 1,
            'instituicao': resultado['_id'],
            'total_premios': resultado['total_premios'],
            'tipo': resultado['tipo']
        })

    return jsonify(response), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
