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

# ENDPOINT01 - Listar todas as escolas existentes
@app.route('/api/listar-escolas', methods=['GET'])
def listar_escolas():
    try:
        escolas = collection.distinct('escola')
        return jsonify({'escolas': escolas}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# ENDPOINT - Listar todos os municípios existentes
@app.route('/api/listar-municipios', methods=['GET'])
def listar_municipios():
    try:
        municipios = collection.distinct('municipio')
        return jsonify({'municipios': municipios}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


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
    municipio = request.args.get('municipio', default='RIO DE JANEIRO', type=str)
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
####################################################################################################################

# ENDPOINT - Exibir trajetória de um estado ao longo das edições
@app.route('/api/trajetoria-estado', methods=['GET'])
def trajetoria_estado():
    estado = request.args.get('estado', default='PB', type=str)

    pipeline = [
        {
            '$match': {
                'uf': estado
            }
        },
        {
            '$group': {
                '_id': '$edicao',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                '_id': 1  # Ordenar por edição (ano)
            }
        }
    ]

    resultados = list(collection.aggregate(pipeline))

    if resultados:
        # Preparando resposta
        response = {
            'estado': estado,
            'trajetoria': []
        }

        for resultado in resultados:
            response['trajetoria'].append({
                'edicao': resultado['_id'],
                'total_premiacoes': resultado['total_premiacoes']
            })

        return jsonify(response), 200
    else:
        return jsonify({'message': 'Nenhuma informação encontrada para o estado especificado'}), 404

# ENDPOINT - Exibir trajetória de um município ao longo das edições
@app.route('/api/trajetoria-municipio', methods=['GET'])
def trajetoria_municipio():
    municipio = request.args.get('municipio', default='RIO DE JANEIRO', type=str)

    pipeline = [
        {
            '$match': {
                'municipio': municipio
            }
        },
        {
            '$group': {
                '_id': '$edicao',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                '_id': 1  # Ordenar por edição (ano)
            }
        }
    ]

    resultados = list(collection.aggregate(pipeline))

    if resultados:
        # Preparando resposta
        response = {
            'municipio': municipio,
            'trajetoria': []
        }

        for resultado in resultados:
            response['trajetoria'].append({
                'edicao': resultado['_id'],
                'total_premiacoes': resultado['total_premiacoes']
            })

        return jsonify(response), 200
    else:
        return jsonify({'message': 'Nenhuma informação encontrada para o município especificado'}), 404

# ENDPOINT - Exibir trajetória de uma escola ao longo das edições
@app.route('/api/trajetoria-escola', methods=['GET'])
def trajetoria_escola():
    escola = request.args.get('escola', type=str)

    if not escola:
        return jsonify({'message': 'O parâmetro "escola" é obrigatório'}), 400

    pipeline = [
        {
            '$match': {
                'escola': escola
            }
        },
        {
            '$group': {
                '_id': '$edicao',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                '_id': 1  # Ordenar por edição (ano)
            }
        }
    ]

    resultados = list(collection.aggregate(pipeline))

    if resultados:
        # Preparando resposta
        response = {
            'escola': escola,
            'trajetoria': []
        }

        for resultado in resultados:
            response['trajetoria'].append({
                'edicao': resultado['_id'],
                'total_premiacoes': resultado['total_premiacoes']
            })

        return jsonify(response), 200
    else:
        return jsonify({'message': 'Nenhuma informação encontrada para a escola especificada'}), 404


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
                'tipo': 'F'
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


# ENDPOINT - Listar estados com mais premiações em uma determinada edição
@app.route('/api/estados-mais-premiacoes', methods=['GET'])
def estados_mais_premiacoes():
    edicao = request.args.get('edicao',default='2021', type=int)

    if not edicao:
        return jsonify({'message': 'O parâmetro "edicao" é obrigatório'}), 400

    pipeline = [
        {
            '$match': {
                'edicao': edicao
            }
        },
        {
            '$group': {
                '_id': '$uf',
                'total_premiacoes': {'$sum': 1}
            }
        },
        {
            '$sort': {
                'total_premiacoes': -1
            }
        }
    ]

    resultados = list(collection.aggregate(pipeline))

    if resultados:
        response = {
            'edicao': edicao,
            'estados': []
        }

        for resultado in resultados:
            response['estados'].append({
                'estado': resultado['_id'],
                'total_premiacoes': resultado['total_premiacoes']
            })

        return jsonify(response), 200
    else:
        return jsonify({'message': 'Nenhuma informação encontrada para a edição especificada'}), 404

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
