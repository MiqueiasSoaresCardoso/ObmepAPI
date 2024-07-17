import ssl
from flask import Flask, jsonify, request
from pymongo import MongoClient
import os
import sys

from flask_cors import CORS

# Configuração da conexão com MongoDB Atlas
uri = "mongodb+srv://miqueiassoares:pMmAke6bpsOI8u6T@cluster0.sjuug1b.mongodb.net/Obmep"
client = MongoClient(uri, ssl=True)
db = client['Obmep']
collection = db['Aluno']

app = Flask(__name__)


CORS(app)
#Criação dos Indices
collection.create_index({"escola": 1})
collection.create_index({"municipio": 1})
collection.create_index({"tipo": 1})
collection.create_index({"edição": 1})
collection.create_index({"nivel": 1})
collection.create_index({"uf": 1})


# ENDPOINTS GERAIS
@app.route('/api/listar-escolas', methods=['GET'])

def listar_escolas():
    estado = request.args.get('estado', default='PB', type=str)
    municipio = request.args.get('municipio', default='JOÃO PESSOA', type=str)


    pipeline = [
        {
            '$match': {
                'uf': estado,
                'municipio': municipio

            }
        },
        {
            '$group': {
                '_id': '$escola',

            }
        },


    ]

    resultados = list(collection.aggregate(pipeline))

    if resultados:
        return jsonify({
            'estado': estado,
            'instituicao': resultados,
        }), 200
    else:
        return jsonify({'message': 'Nenhuma instituição encontrada para os critérios especificados'}), 404


@app.route('/api/listar-municipios', methods=['GET'])
def listar_municipios():
    estado = request.args.get('estado', default='PB', type=str)


    pipeline = [
        {
            '$match': {
                'uf': estado,

            }
        },
        {
            '$group': {
                '_id': '$municipio',
            }
        },

    ]

    resultados = list(collection.aggregate(pipeline))

    if resultados:
        return jsonify({
            'estado': estado,
            'municipio': resultados,

        }), 200
    else:
        return jsonify({'message': 'Nenhum Municipio encontrada para os critérios especificados'}), 404


#01 ENDPOINT ESPECIFICOS
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
#02 ENDPOINT - Buscar instituição mais destacada em um município
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

# ENDPOINT - Comparar desempenho entre escolas Municipais e Estaduais em um estado e nível específicos, selecionado o ANO
#APENAS OS NIVEIS 1 E 2
#GRAFICO DE BARRAS SUBINDO, DUAS BARRAS, UMA ESTADUAL E OUTRA MUNICIPAL
@app.route('/api/comparar-desempenho-municipal-estadual', methods=['GET'])
def comparar_desempenho_municipal_estadual():
    estado = request.args.get('estado', default='PB', type=str)
    nivel = request.args.get('nivel', default=1, type=int)
    edicao = request.args.get('edicao', default=2023, type=int)

    pipeline_municipais = [
        {
            '$match': {
                'uf': estado,
                'nivel': nivel,
                'tipo': 'M',  # Escolas Municipais
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

    ]

    pipeline_estaduais = [
        {
            '$match': {
                'uf': estado,
                'nivel': nivel,
                'tipo': 'E' , # Escolas Estaduais
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

    ]

    resultados_municipais = list(collection.aggregate(pipeline_municipais))
    resultados_estaduais = list(collection.aggregate(pipeline_estaduais))

    # Preparando resposta
    response = {
        'estado': estado,
        'nivel': nivel,
        'escolas_municipais': [],
        'escolas_estaduais': []
    }

    # Adicionando escolas Municipais no resultado
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


# ENDPOINT - Exibir trajetória de um estado ao longo das edições
#PEDIR APENAS O ESTADO
#GRAFICO DE LINHA
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

#SELECIONAR O ESTADO
#MUNICIPIO
#REQUISIÇÃO PARA A LISTAGEM DE ESCOLAS
#SELECIONA UMA
@app.route('/api/trajetoria-escola', methods=['GET'])
def trajetoria_escola():
    escola = request.args.get('escola', type=str)

    if not escola:
        return jsonify({'message': 'O parâmetro "escola" é obrigatório'}), 400

    pipeline = [
        {
            '$match': {
                'escola': escola,

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
    edicao = request.args.get('edicao', default=2023, type=str)
    nivel = 3  # Considerando apenas o nível 3 (Ensino médio)


    pipeline_federais = [
        {
            '$match': {
                'uf': estado,
                'nivel': nivel,
                'edicao': edicao,
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

    ]

    pipeline_estaduais = [
        {
            '$match': {
                'uf': estado,
                'nivel': nivel,
                'tipo': 'E',
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

    ]

    resultados_federais = list(collection.aggregate(pipeline_federais))
    resultados_estaduais = list(collection.aggregate(pipeline_estaduais))

    # Preparando resposta
    response = {
        'estado': estado,
        'nivel': nivel,
        'edicao': edicao,
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

#exibe o total geral de premiações, e separa por medalhas de ouro, prata e bronze
@app.route('/api/listar-total-premiacoes', methods=['GET'])
def listar_total_premiacoes():

    pipeline = [

        {
            '$group': {
                '_id': '$medalha',
                'total_premiacoes': {'$sum': 1}
            }
        }
    ]

    resultados = list(collection.aggregate(pipeline))

    # Preparando resposta
    response = {
        'total_geral': 0,
        'medalhas': {
            'ouro': 0,
            'prata': 0,
            'bronze': 0
        }
    }

    # Adicionando premiações no resultado
    for resultado in resultados:
        medalha = resultado['_id']
        total = resultado['total_premiacoes']
        response['total_geral'] += total
        if medalha == 'Ouro':
            response['medalhas']['ouro'] = total
        elif medalha == 'Prata':
            response['medalhas']['prata'] = total
        elif medalha == 'Bronze':
            response['medalhas']['bronze'] = total

    return jsonify(response), 200


# ENDPOINT - Exibir Ranking geral de premiações por estado ao longo dos anos
# CONSULTAS PRINCIPAl

@app.route('/api/ranking-geral-estados', methods=['GET'])
def ranking_geral_estados():


    pipeline = [

        {
            '$group': {
                '_id': '$uf',  # Agrupa por estado (UF)
                'total_premios': {'$sum': 1}  # Conta o número total de premiações por estado
            }
        },
        {
            '$sort': {
                'total_premios': -1  # Ordena em ordem decrescente pelo total de premiações
            }
        }
    ]

    resultados = list(collection.aggregate(pipeline))

    # Preparando resposta
    response = {
        'ranking': []
    }

    for idx, resultado in enumerate(resultados):
        response['ranking'].append({
            'posicao': idx + 1,
            'estado': resultado['_id'],
            'total_premios': resultado['total_premios']
        })

    return jsonify(response), 200


#10 ENDPOINT - Comparar desempenho entre escolas Públicas e Privadas em um município e edição específicos, considerando um nivel especifico
@app.route('/api/comparar-desempenho-publico-privado', methods=['GET'])
def comparar_desempenho_publico_privado():
    municipio = request.args.get('municipio', default='RIO DE JANEIRO', type=str)
    edicao = request.args.get('edicao', default=2023, type=int)
    nivel = request.args.get('nivel', default=1, type=int)

    pipeline_publicas = [
        {
            '$match': {
                'municipio': municipio,
                'tipo': {'$ne': 'P'},  # Todas as escolas que não forem 'P' ou seja Privadas, serão consideradas
                'edicao': edicao,
                'nivel': nivel
            }
        },
        {
            '$group': {
                '_id': '$nivel',
                'total_premiacoes': {'$sum': 1}
            }
        }
    ]

    pipeline_privadas = [
        {
            '$match': {
                'municipio': municipio,
                'tipo': 'P',  # Escolas Privadas
                'edicao': edicao,
                'nivel': nivel
            }
        },
        {
            '$group': {
                '_id': '$nivel',
                'total_premiacoes': {'$sum': 1}
            }
        }
    ]

    resultados_publicas = list(collection.aggregate(pipeline_publicas))
    resultados_privadas = list(collection.aggregate(pipeline_privadas))

    # Preparando resposta
    response = {
        'municipio': municipio,
        'edicao': edicao,
        'escolas_publicas': [],
        'escolas_privadas': []
    }

    # Adicionando escolas Públicas no resultado
    for resultado in resultados_publicas:
        response['escolas_publicas'].append({
            'nivel': resultado['_id'],
            'total_premiacoes': resultado['total_premiacoes']
        })

    # Adicionando escolas Privadas no resultado
    for resultado in resultados_privadas:
        response['escolas_privadas'].append({
            'nivel': resultado['_id'],
            'total_premiacoes': resultado['total_premiacoes']
        })

    return jsonify(response), 200



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(sys.path)
    app.run(host='0.0.0.0', port=port, debug=True)
