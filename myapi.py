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
from flask import Flask, jsonify
from pymongo import MongoClient
from flask_cors import CORS # Importar CORS

# Configuração da conexão com MongoDB Atlas
uri = "mongodb+srv://miqueiassoares:pMmAke6bpsOI8u6T@cluster0.sjuug1b.mongodb.net/Obmep" # Sua URI
client = MongoClient(uri, ssl=True) # ssl=True é geralmente o padrão para Atlas, mas bom explicitar
db = client['Obmep']
collection = db['Aluno']

app = Flask(__name__)
CORS(app) # Habilitar CORS para todas as rotas

optimized_index_fields = [
    ("medalha", 1),
    ("uf", 1),
    ("municipio", 1),
    ("escola", 1),
    ("nivel", 1),
    ("edicao", 1) # Certifique-se que 'edicao' é o nome correto do campo
]
try:
    collection.create_index(optimized_index_fields, name="idx_medalhas_agregacao_otimizada")
    print("Índice composto otimizado criado/verificado: idx_medalhas_agregacao_otimizada")
except Exception as e:
    print(f"Erro ao criar índice otimizado: {e}")

# Você PODE manter outros índices individuais se forem necessários para OUTRAS consultas
# mas para ESTA agregação, eles são menos relevantes que o composto acima.
# Exemplos (se necessários para outras partes da sua aplicação):
# collection.create_index({"escola": 1}, name="idx_escola")
# collection.create_index({"municipio": 1}, name="idx_municipio")
# collection.create_index({"tipo": 1}, name="idx_tipo") # Campo "tipo" não está na agregação
# collection.create_index({"uf": 1}, name="idx_uf")

@app.route('/api/top-escolas-globais-com-historico', methods=['GET'])
def top_escolas_globais_com_historico():
    # --- Etapa 1: Identificar as Top 10 escolas globais ---
    #COLOCAR CO_ENTIDADE DE VOLTA
    #'CO_ENTIDADE': '$CO_ENTIDADE'
    pipeline_top_10_escolas_global = [
        {'$match': {'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']}}},
        {
            '$group': {
                '_id': {'escola': '$escola', 'uf': '$uf', 'municipio': '$municipio'},
                'total_global_medalhas': {'$sum': 1}
            }
        },
        {'$sort': {'total_global_medalhas': -1}},
        {'$limit': 377},
        {'$project': {'_id': 0, 'escola_id': '$_id', 'total_global_medalhas_da_escola': '$total_global_medalhas' }} # Incluindo o total global
    ]

    try:
        top_escolas_cursor = collection.aggregate(pipeline_top_10_escolas_global, allowDiskUse=True)
        lista_identificadores_top_escolas = list(top_escolas_cursor)

        if not lista_identificadores_top_escolas:
            return jsonify({'message': 'Nenhuma escola encontrada'}), 404

    except Exception as e_etapa1:
        print(f"Erro na Etapa 1 (Global): {e_etapa1}")
        return jsonify({'message': 'Erro ao buscar top escolas globais', 'error': str(e_etapa1)}), 500

    # --- Etapa 2: Para cada top escola, buscar histórico detalhado ---
    resultados_finais_detalhados = []
    for identificador_escola_obj in lista_identificadores_top_escolas:
        escola_info = identificador_escola_obj['escola_id']
        total_global_da_escola = identificador_escola_obj['total_global_medalhas_da_escola'] # Pegando o total

        pipeline_historico_escola = [
            {
                '$match': {
                    #'CO_ENTIDADE': escola_info['CO_ENTIDADE'],
                    'escola': escola_info['escola'], 'uf': escola_info['uf'],
                    'municipio': escola_info['municipio'],
                    'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']}
                }
            },
            {'$group': {'_id': {'edicao': '$edicao', 'nivel': '$nivel'}, 'quantidade_medalhas': {'$sum': 1}}},
            {'$sort': {'_id.edicao': -1, '_id.nivel': 1}},
            {
                '$group': {
                    '_id': '$_id.edicao',
                    'detalhes_por_nivel': {'$push': {'nivel': '$_id.nivel', 'premiacoes': '$quantidade_medalhas'}},
                    'total_medalhas_na_edicao_para_esta_escola': {'$sum': '$quantidade_medalhas'}
                }
            },
            {'$sort': {'_id': -1}},
            {
                '$project': {
                    '_id': 0, 'edicao': '$_id',
                    'total_medalhas_na_edicao': '$total_medalhas_na_edicao_para_esta_escola',
                    'premiacoes_por_nivel': '$detalhes_por_nivel'
                }
            }
        ]
        try:
            historico_cursor = collection.aggregate(pipeline_historico_escola, allowDiskUse=True)
            lista_historico_premiacoes = list(historico_cursor)

            resultados_finais_detalhados.append({
                #'CO_ENTIDADE': escola_info['CO_ENTIDADE'],
                'escola': escola_info['escola'],
                'uf': escola_info['uf'],
                'municipio': escola_info['municipio'],
                'total_global_de_medalhas_da_escola': total_global_da_escola, # Adicionado
                'historico_premiacoes_por_edicao': lista_historico_premiacoes
            })
        except Exception as e_hist:
            print(f"Erro ao buscar histórico para {escola_info['escola']}: {e_hist}")
            resultados_finais_detalhados.append({
                'escola': escola_info['escola'], 'uf': escola_info['uf'],
                'municipio': escola_info['municipio'],
                'total_global_de_medalhas_da_escola': total_global_da_escola,
                'historico_premiacoes_por_edicao': [] # Histórico vazio em caso de erro
            })

    return jsonify({'top_escolas_com_historico': resultados_finais_detalhados}), 200

@app.route('/api/listar-total-medalhas-por-escola', methods=['GET'])
def listar_total_medalhas_por_escola():
    # --- Etapa 1: Pipeline para Top Escolas ---
    pipeline_top_escolas = [
        {'$match': {'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']}}},
        {
            '$group': {
                '_id': {'escola': '$escola', 'edicao': '$edicao', 'uf': '$uf', 'municipio': '$municipio'},
                'total_medalhas_na_edicao': {'$sum': 1}
            }
        },
        {'$sort': {'_id.edicao': -1, 'total_medalhas_na_edicao': -1, '_id.escola': 1}},
        {'$limit': 50}, # Defina seu N aqui
        {
            '$project': {
                '_id': 0, 'escola': '$_id.escola', 'edicao': '$_id.edicao',
                'uf': '$_id.uf', 'municipio': '$_id.municipio',
                'total_medalhas_geral': '$total_medalhas_na_edicao'
            }
        }
    ]

    try:
        top_escolas_cursor = collection.aggregate(pipeline_top_escolas, allowDiskUse=True)
        lista_top_escolas = list(top_escolas_cursor)

        if not lista_top_escolas:
            return jsonify({'message': 'Nenhuma escola com medalhas encontrada para o top N'}), 404

        resultados_finais_com_detalhes = []
        # --- Etapa 2: Loop para buscar detalhes por nível ---
        for item_top_escola in lista_top_escolas:
            pipeline_detalhes_nivel = [
                {
                    '$match': {
                        'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']},
                        'escola': item_top_escola['escola'],
                        'edicao': item_top_escola['edicao'],
                        'uf': item_top_escola['uf'],
                        'municipio': item_top_escola['municipio']
                    }
                },
                {'$group': {'_id': '$nivel', 'quantidade_medalhas_neste_nivel': {'$sum': 1}}},
                {'$project': {'_id': 0, 'nivel': '$_id', 'premiacoes': '$quantidade_medalhas_neste_nivel'}},
                {'$sort': {'nivel': 1}}
            ]
            try:
                detalhes_nivel_cursor = collection.aggregate(pipeline_detalhes_nivel) # allowDiskUse pode não ser necessário
                lista_detalhes_nivel = list(detalhes_nivel_cursor)
                item_top_escola['detalhes_por_nivel'] = lista_detalhes_nivel
            except Exception as e_detail:
                print(f"Erro ao buscar detalhes para {item_top_escola['escola']} ({item_top_escola['edicao']}): {e_detail}")
                item_top_escola['detalhes_por_nivel'] = [] # Ou outra forma de tratamento
            resultados_finais_com_detalhes.append(item_top_escola)

        return jsonify({'escolas_com_detalhes_medalhas_por_ano': resultados_finais_com_detalhes}), 200

    except Exception as e:
        print(f"Erro na rota /api/listar-total-medalhas-por-escola: {e}")
        # Retornar o erro original se for da Etapa 1
        return jsonify({'message': 'Erro ao processar a solicitação', 'error': str(e)}), 500

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
            "$group": {
                "_id": "$escola"
            }
        },
        {
            "$project": {
                "_id": 0,
                "escola": "$_id"
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
