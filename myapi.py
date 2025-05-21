import keep_alive;
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
from flask import Flask, jsonify
from pymongo import MongoClient

# Supondo que 'app' e 'collection' já estão configurados
# Exemplo de configuração (descomente e ajuste se necessário):
# app = Flask(__name__)
# client = MongoClient('mongodb://localhost:27017/') # Ajuste sua string de conexão
# db = client['seu_banco_de_dados'] # Ajuste o nome do banco
# collection = db['sua_colecao_de_medalhas'] # Ajuste o nome da coleção

# É uma boa prática renomear a rota para refletir sua nova funcionalidade
@app.route('/api/listar-total-medalhas-por-escola', methods=['GET'])
def listar_total_medalhas_por_escola():
    pipeline = [
        {
            # Primeiro, podemos opcionalmente filtrar documentos que não têm medalha,
            # se sua coleção puder ter entradas sem medalha.
            # Se toda entrada na coleção tem uma medalha (Ouro, Prata, Bronze, etc.),
            # este $match pode não ser estritamente necessário.
            '$match': {
                'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']} # Adicione outros tipos se houver
                # Ou, se qualquer valor não nulo em 'medalha' conta:
                # 'medalha': {'$ne': None, '$exists': True}
            }
        },
        {
            '$group': {
                '_id': {
                    'uf': '$uf',
                    'municipio': '$municipio',
                    'escola': '$escola'
                    # Nível, ciclo_avaliativo e edicao foram removidos do _id
                    # para que todas as medalhas de uma escola (mesmo nome, município, UF)
                    # sejam somadas, independentemente desses outros fatores.
                },
                # Simplesmente contamos quantos documentos (medalhas) existem para cada grupo de escola.
                'total_medalhas': {'$sum': 1}
                # Se você quisesse manter a contagem por tipo E o total, poderia ser:
                # 'total_ouro': {'$sum': {'$cond': [{'$eq': ['$medalha', 'Ouro']}, 1, 0]}},
                # 'total_prata': {'$sum': {'$cond': [{'$eq': ['$medalha', 'Prata']}, 1, 0]}},
                # 'total_bronze': {'$sum': {'$cond': [{'$eq': ['$medalha', 'Bronze']}, 1, 0]}},
                # 'total_medalhas_geral': {'$sum': 1} # Soma todas as medalhas para o grupo
            }
        },
        {
            # Opcional: Remodelar a saída para um formato mais plano e amigável
            '$project': {
                '_id': 0, # Remove o campo _id que é um objeto
                'uf': '$_id.uf',
                'municipio': '$_id.municipio',
                'escola': '$_id.escola',
                'total_medalhas': '$total_medalhas'
                # Se você manteve as contagens individuais no $group:
                # 'total_ouro': '$total_ouro',
                # 'total_prata': '$total_prata',
                # 'total_bronze': '$total_bronze',
            }
        },
        {
            '$sort': {
                'total_medalhas': -1, # <--- AQUI! -1 para ordem decrescente
                'uf': 1,
                'municipio': 1,
                'escola': 1    # E finalmente por Escola
            }
        }
    ]

    try:
        # Lembre-se de manter allowDiskUse=True para o caso de a ordenação
        # dos resultados agrupados ainda ser grande.
        resultados_cursor = collection.aggregate(pipeline, allowDiskUse=True)
        resultados = list(resultados_cursor)

        if resultados:
            # A chave no JSON de resposta foi alterada para refletir o conteúdo
            return jsonify({'escolas_com_total_medalhas': resultados}), 200
        else:
            return jsonify({'message': 'Nenhuma escola com medalhas encontrada'}), 404
    except Exception as e:
        # É uma boa prática logar o erro no servidor
        app.logger.error(f"Erro durante a agregação de medalhas por escola: {e}")
        return jsonify({'message': 'Erro ao processar a solicitação', 'error': str(e)}), 500

# Exemplo de como executar o Flask app (descomente se estiver rodando este arquivo diretamente)
# if __name__ == '__main__':
#     app.run(debug=True)
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
        {
            '$sort':{
                '_id': 1
            }
        }


    ]

    resultados = list(collection.aggregate(pipeline))

    if resultados:
        return jsonify({
            'estado': estado,
            'instituicao': resultados,
        }), 200
    else:
        return jsonify({'message': 'Nenhuma instituição encontrada para os critérios especificados'}), 404


@app.route('/api/listar-todas-escolas', methods=['GET'])
def listar_todas_escolas():
    pipeline = [
        {
            '$group': {
                '_id': {
                    'uf': '$uf',
                    'municipio': '$municipio',
                    'escola': '$escola',
                    'nivel': '$nivel',
                    'ciclo_avaliativo': '$ciclo_avaliativo',
                    'edicao': '$edicao'
                },
                'total_ouro': {'$sum': {'$cond': [{'$eq': ['$medalha', 'Ouro']}, 1, 0]}},
                'total_prata': {'$sum': {'$cond': [{'$eq': ['$medalha', 'Prata']}, 1, 0]}},
                'total_bronze': {'$sum': {'$cond': [{'$eq': ['$medalha', 'Bronze']}, 1, 0]}},
                'total_geral': {'$sum': 1}  # Conta o total de documentos agrupados
            }
        },
        {
            '$sort': {
                '_id.uf': 1,
                '_id.municipio': 1,
                '_id.escola': 1,
                '_id.edicao': 1
                # Considerar adicionar '_id.nivel' e '_id.ciclo_avaliativo' aqui
                # para uma ordenação mais determinística se houver múltiplos
                # níveis/ciclos para a mesma escola/edição.
            }
        }
    ]

    try:
        # Adicionar allowDiskUse=True
        resultados = list(collection.aggregate(pipeline, allowDiskUse=True))

        if resultados:
            return jsonify({'escolas': resultados}), 200
        else:
            return jsonify({'message': 'Nenhuma escola encontrada com os critérios fornecidos'}), 404
    except Exception as e:
        # Logar o erro pode ser útil para depuração
        print(f"Erro durante a agregação: {e}")
        return jsonify({'message': 'Erro ao processar a solicitação', 'error': str(e)}), 500


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
        {
            '$sort':{
                '_id': 1
            }
        }

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
    edicao = request.args.get('edicao', default=2023, type=int)
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
