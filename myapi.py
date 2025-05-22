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

from flask import Flask, jsonify
from pymongo import MongoClient

# Supondo que 'app' e 'collection' já estão configurados
# Exemplo de configuração:
# app = Flask(__name__)
# client = MongoClient('mongodb://localhost:27017/')
# db = client['seu_banco_de_dados']
# collection = db['sua_colecao_de_medalhas']
#ROTA NOVA
@app.route('/api/medalhas-escola-ano-nivel', methods=['GET'])
def medalhas_escola_ano_nivel():
    pipeline = [
        {
            # 1. Filtrar medalhas válidas e garantir que 'edicao' e 'nivel' existam (opcional)
            '$match': {
                'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']},
                'edicao': {'$ne': None, '$exists': True}, # Garante que a edição existe
                'nivel': {'$ne': None, '$exists': True}   # Garante que o nível existe
            }
        },
        {
            # 2. Primeiro agrupamento: Contar medalhas por Escola, Edição e Nível
            '$group': {
                '_id': {
                    'uf': '$uf',
                    'municipio': '$municipio',
                    'escola': '$escola',
                    'edicao': '$edicao',
                    'nivel': '$nivel'
                },
                'total_medalhas': {'$sum': 1}
            }
        },
        {
            # 3. Ordenar para o próximo $group (para $push ordenado dentro dos arrays)
            # Ordena primeiro por identificadores da escola, depois por edição, depois por nível
            '$sort': {
                '_id.uf': 1,
                '_id.municipio': 1,
                '_id.escola': 1,
                '_id.edicao': 1,
                '_id.nivel': 1
            }
        },
        {
            # 4. Segundo agrupamento: Agrupar por Escola e Edição
            # para criar um array de níveis com suas medalhas para cada edição
            '$group': {
                '_id': {
                    'uf': '$_id.uf',
                    'municipio': '$_id.municipio',
                    'escola': '$_id.escola',
                    'edicao': '$_id.edicao'
                },
                'niveis_nesta_edicao': {
                    '$push': {
                        'nivel': '$_id.nivel',
                        'medalhas': '$total_medalhas'
                    }
                },
                # Também podemos calcular o total de medalhas para esta edição específica da escola
                'total_medalhas_edicao': {'$sum': '$total_medalhas'}
            }
        },
        {
            # 5. Terceiro agrupamento: Agrupar por Escola
            # para criar um array de edições (com seus níveis) para cada escola
            '$group': {
                '_id': {
                    'uf': '$_id.uf',
                    'municipio': '$_id.municipio',
                    'escola': '$_id.escola'
                },
                'participacoes_por_ano': {
                    '$push': {
                        'ano_edicao': '$_id.edicao',
                        'total_medalhas_neste_ano': '$total_medalhas_edicao',
                        'detalhes_por_nivel': '$niveis_nesta_edicao'
                    }
                },
                # Calcular o total geral de medalhas da escola em todas as edições
                'total_geral_medalhas_escola': {'$sum': '$total_medalhas_edicao'}
            }
        },
        {
            # 6. Formatar a saída final
            '$project': {
                '_id': 0,
                'uf': '$_id.uf',
                'municipio': '$_id.municipio',
                'escola': '$_id.escola',
                'total_geral_medalhas_escola': 1,
                'participacoes_por_ano': 1
            }
        },
        {
            # 7. Ordenar o resultado final pelas escolas com mais medalhas no geral
            '$sort': {
                'total_geral_medalhas_escola': -1,
                'uf': 1,
                'municipio': 1,
                'escola': 1
            }
        }
    ]

    try:
        resultados_cursor = collection.aggregate(pipeline, allowDiskUse=True)
        resultados = list(resultados_cursor)

        if resultados:
            return jsonify({'medalhas_detalhadas_por_escola': resultados}), 200
        else:
            return jsonify({'message': 'Nenhuma escola com dados de medalhas encontrados'}), 404
    except Exception as e:
        # app.logger.error(f"Erro em /api/medalhas-escola-ano-nivel: {e}")
        print(f"Erro em /api/medalhas-escola-ano-nivel: {e}")
        return jsonify({'message': 'Erro ao processar a solicitação', 'error': str(e)}), 500
@app.route('/api/listar-total-medalhas-por-escola', methods=['GET'])
def listar_total_medalhas_por_escola():
    pipeline = [
        {
            # 1. Filtrar apenas documentos que representam medalhas válidas
            '$match': {
                'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']},
                # Opcional: Adicionar filtro para 'nivel' se necessário
                # 'nivel': {'$ne': None, '$exists': True}
            }
        },
        {
            # 2. Agrupar por escola E nível para obter o total de medalhas para cada nível da escola
            '$group': {
                '_id': {
                    'uf': '$uf',
                    'municipio': '$municipio',
                    'escola': '$escola',
                    'nivel': '$nivel'
                },
                'medalhas_neste_nivel': {'$sum': 1}
            }
        },
        {
            # 3. Opcional, mas recomendado: Ordenar antes do próximo $group para que o $push
            # mantenha uma ordem previsível (ex: alfabética por nível) dentro do array.
            '$sort': {
                '_id.uf': 1,
                '_id.municipio': 1,
                '_id.escola': 1,
                '_id.nivel': 1 # Ordena por nível aqui
            }
        },
        {
            # 4. Agrupar novamente, desta vez apenas por escola, para:
            #    a) Calcular o total geral de medalhas da escola.
            #    b) Criar um array com os detalhes de cada nível.
            '$group': {
                '_id': { # Chave de agrupamento é apenas a identificação da escola
                    'uf': '$_id.uf',
                    'municipio': '$_id.municipio',
                    'escola': '$_id.escola'
                },
                'total_geral_medalhas': {'$sum': '$medalhas_neste_nivel'}, # Soma as medalhas de todos os níveis da escola
                'detalhes_por_nivel': {
                    '$push': { # Cria um array com os detalhes de cada nível
                        'nivel': '$_id.nivel', # O nível original
                        'total_medalhas_nivel': '$medalhas_neste_nivel' # As medalhas daquele nível específico
                    }
                }
            }
        },
        {
            # 5. Formatar a saída final
            '$project': {
                '_id': 0, # Remover o _id estruturado
                'uf': '$_id.uf',
                'municipio': '$_id.municipio',
                'escola': '$_id.escola',
                'total_geral_medalhas': 1,
                'detalhes_por_nivel': 1
            }
        },
        {
            # 6. Ordenar o resultado final pelo total geral de medalhas (maior para menor)
            # e por critérios de desempate.
            '$sort': {
                'total_geral_medalhas': -1,
                'uf': 1,
                'municipio': 1,
                'escola': 1
            }
        }
    ]

    try:
        resultados_cursor = collection.aggregate(pipeline, allowDiskUse=True)
        resultados = list(resultados_cursor)

        if resultados:
            # A chave na resposta JSON pode ser mantida ou ajustada conforme sua preferência
            return jsonify({'escolas_com_detalhes_medalhas': resultados}), 200
        else:
            return jsonify({'message': 'Nenhuma escola com medalhas encontrada'}), 404
    except Exception as e:
        # app.logger.error(f"Erro na rota /api/listar-total-medalhas-por-escola: {e}") # Se logger configurado
        print(f"Erro na rota /api/listar-total-medalhas-por-escola: {e}")
        return jsonify({'message': 'Erro ao processar a solicitação', 'error': str(e)}), 500

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

#TESTES




if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(sys.path)
    app.run(host='0.0.0.0', port=port, debug=True)
