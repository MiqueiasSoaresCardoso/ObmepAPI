import keep_alive;
import ssl
from flask import Flask, jsonify, request, Response
from pymongo import MongoClient
import os
import sys
import pandas as pd
import numpy as np
import io

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
@app.route('/api/top-escolas-globais-com-historico-salvar', methods=['GET'])
def top_escolas_com_historico_salvar():
    pipeline_top_377_escolas = [
        {'$match': {'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']}}},
        {
            '$group': {
                '_id': {'escola': '$escola', 'uf': '$uf', 'municipio': '$municipio'},
                'total_global_medalhas': {'$sum': 1}
            }
        },
        {'$sort': {'total_global_medalhas': -1}},
        {'$limit': 377},
        {
            '$project': {
                '_id': 0,
                'escola_id': '$_id',
                'total_global_medalhas_da_escola': '$total_global_medalhas'
            }
        }
    ]

    try:
        top_escolas_cursor = collection.aggregate(pipeline_top_377_escolas, allowDiskUse=True)
        lista_identificadores_top_escolas = list(top_escolas_cursor)

        if not lista_identificadores_top_escolas:
            return jsonify({'message': 'Nenhuma escola encontrada'}), 404

    except Exception as e_etapa1:
        return jsonify({'message': 'Erro ao buscar top escolas globais', 'error': str(e_etapa1)}), 500

    resultados_finais_detalhados = []
    for identificador_escola_obj in lista_identificadores_top_escolas:
        escola_info = identificador_escola_obj['escola_id']
        total_global_da_escola = identificador_escola_obj['total_global_medalhas_da_escola']

        pipeline_historico_escola = [
            {
                '$match': {
                    'escola': escola_info['escola'],
                    'uf': escola_info['uf'],
                    'municipio': escola_info['municipio'],
                    'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']}
                }
            },
            {'$group': {'_id': {'edicao': '$edicao', 'nivel': '$nivel'}, 'quantidade_medalhas': {'$sum': 1}}},
            {'$sort': {'_id.edicao': -1, '_id.nivel': 1}},
            {
                '$group': {
                    '_id': '$_id.edicao',
                    'detalhes_por_nivel': {
                        '$push': {
                            'nivel': '$_id.nivel',
                            'premiacoes': '$quantidade_medalhas'
                        }
                    },
                    'total_medalhas_na_edicao_para_esta_escola': {'$sum': '$quantidade_medalhas'}
                }
            },
            {'$sort': {'_id': -1}},
            {
                '$project': {
                    '_id': 0,
                    'edicao': '$_id',
                    'total_medalhas_na_edicao': '$total_medalhas_na_edicao_para_esta_escola',
                    'premiacoes_por_nivel': '$detalhes_por_nivel'
                }
            }
        ]

        try:
            historico_cursor = collection.aggregate(pipeline_historico_escola, allowDiskUse=True)
            lista_historico = list(historico_cursor)

            resultados_finais_detalhados.append({
                'escola': escola_info['escola'],
                'uf': escola_info['uf'],
                'municipio': escola_info['municipio'],
                'total_global_de_medalhas_da_escola': total_global_da_escola,
                'historico_premiacoes_por_edicao': lista_historico
            })
        except Exception as e_hist:
            resultados_finais_detalhados.append({
                'escola': escola_info['escola'],
                'uf': escola_info['uf'],
                'municipio': escola_info['municipio'],
                'total_global_de_medalhas_da_escola': total_global_da_escola,
                'historico_premiacoes_por_edicao': []
            })

    # Criando DataFrame para salvar em CSV
    linhas_csv = []
    for escola in resultados_finais_detalhados:
        for edicao in escola['historico_premiacoes_por_edicao']:
            linha = {
                'escola': escola['escola'],
                'uf': escola['uf'],
                'municipio': escola['municipio'],
                'total_global_medalhas': escola['total_global_de_medalhas_da_escola'],
                'edicao': edicao['edicao'],
                'total_medalhas_na_edicao': edicao['total_medalhas_na_edicao'],
                'premiacoes_por_nivel': "; ".join(
                    f"{p['nivel']}:{p['premiacoes']}" for p in edicao['premiacoes_por_nivel']
                )
            }
            linhas_csv.append(linha)

    df = pd.DataFrame(linhas_csv)

    # Caminho onde o CSV será salvo (pode personalizar)
    caminho_arquivo = os.path.join(os.getcwd(), 'top_escolas_historico.csv')
    df.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')

    return {'mensagem': f'Arquivo CSV salvo com sucesso em: {caminho_arquivo}'}, 200
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
#ENDPOINT REFORMULADO DE ACORDO COM O NOVO TEMA...
@app.route('/api/perfil-escolas-publicas-campeas-obmep', methods=['GET']) # Nome da rota atualizado
def obter_perfil_escolas_publicas_campeas(): # Nome da função atualizado
    try:
        # --- Etapa 1: Identificar as Top 377 ESCOLAS PÚBLICAS ... ---
        pipeline_selecao_top_escolas = [
            {
                '$match': {
                    'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']},
                    'edicao': {'$gte': 2010, '$lte': 2023},
                    'tipo': {'$ne': 'P'}  # <--- FILTRO ADICIONADO AQUI
                    # CONFIRME O NOME DO CAMPO 'tipo_escola' E O VALOR PARA PRIVADA ('P')
                    # OU USE {'$in': ['M', 'E', 'F']} se souber os códigos das públicas
                }
            },
            {
                '$addFields': {
                    'pontos_medalha': {
                        '$switch': {
                            'branches': [
                                {'case': {'$eq': ['$medalha', 'Ouro']}, 'then': 3},
                                {'case': {'$eq': ['$medalha', 'Prata']}, 'then': 2},
                                {'case': {'$eq': ['$medalha', 'Bronze']}, 'then': 1}
                            ],
                            'default': 0
                        }
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'escola_obmep': '$escola',
                        'uf_obmep': '$uf',
                        'municipio_obmep': '$municipio'
                    },
                    'pontuacao_total_ponderada_periodo': {'$sum': '$pontos_medalha'},
                    'total_medalhas_simples_periodo': {'$sum': 1}
                }
            },
            {'$sort': {'pontuacao_total_ponderada_periodo': -1}},
            {'$limit': 377},
            {
                '$project': {
                    '_id': 0,
                    'identificador_escola_obmep': '$_id',
                    'pontuacao_ponderada_da_escola': '$pontuacao_total_ponderada_periodo',
                    'total_medalhas_simples_da_escola': '$total_medalhas_simples_periodo'
                }
            }
        ]

        top_escolas_cursor = collection.aggregate(pipeline_selecao_top_escolas, allowDiskUse=True)
        lista_top_escolas_selecionadas = list(top_escolas_cursor)

        if not lista_top_escolas_selecionadas:
            return jsonify({'message': 'Nenhuma escola pública de alto desempenho encontrada para o período especificado.'}), 404

        # --- Etapa 2: Para cada escola pública selecionada, buscar o histórico detalhado ... ---
        resultados_finais_com_historico = []
        for escola_data in lista_top_escolas_selecionadas:
            id_obmep = escola_data['identificador_escola_obmep']
            pontuacao_total = escola_data['pontuacao_ponderada_da_escola']
            medalhas_simples_total = escola_data['total_medalhas_simples_da_escola']

            # O match para o histórico não precisa repetir o filtro de tipo_escola,
            # pois as escolas já foram selecionadas como públicas.
            # Mas, por segurança ou se os dados pudessem ser inconsistentes, não faria mal.
            # No entanto, para eficiência, podemos omitir se a Etapa 1 já garantiu.
            match_criteria_historico = {
                'escola': id_obmep['escola_obmep'],
                'uf': id_obmep['uf_obmep'],
                'municipio': id_obmep['municipio_obmep'],
                'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']},
                'edicao': {'$gte': 2010, '$lte': 2023}
            }

            pipeline_historico_escola = [
                {'$match': match_criteria_historico},
                {
                    '$group': {
                        '_id': {'edicao_hist': '$edicao', 'nivel_hist': '$nivel'},
                        'quantidade_medalhas_nivel_edicao': {'$sum': 1}
                    }
                },
                {'$sort': {'_id.edicao_hist': -1, '_id.nivel_hist': 1}},
                {
                    '$group': {
                        '_id': '$_id.edicao_hist',
                        'detalhes_por_nivel': {
                            '$push': {
                                'nivel': '$_id.nivel_hist',
                                'premiacoes': '$quantidade_medalhas_nivel_edicao'
                            }
                        },
                        'total_medalhas_na_edicao_para_esta_escola': {'$sum': '$quantidade_medalhas_nivel_edicao'}
                    }
                },
                {'$sort': {'_id': -1}},
                {
                    '$project': {
                        '_id': 0,
                        'edicao': '$_id',
                        'total_medalhas_na_edicao': '$total_medalhas_na_edicao_para_esta_escola',
                        'premiacoes_por_nivel': '$detalhes_por_nivel'
                    }
                }
            ]

            try:
                historico_cursor = collection.aggregate(pipeline_historico_escola, allowDiskUse=True)
                lista_historico_premiacoes_escola = list(historico_cursor)

                resultados_finais_com_historico.append({
                    'identificador_obmep': id_obmep,
                    'pontuacao_ponderada_total_2010_2023': pontuacao_total,
                    'total_medalhas_simples_2010_2023': medalhas_simples_total,
                    'historico_premiacoes_por_edicao': lista_historico_premiacoes_escola
                })
            except Exception as e_hist:
                print(f"Erro ao buscar histórico para {id_obmep['escola_obmep']}: {e_hist}")
                resultados_finais_com_historico.append({
                    'identificador_obmep': id_obmep,
                    'pontuacao_ponderada_total_2010_2023': pontuacao_total,
                    'total_medalhas_simples_2010_2023': medalhas_simples_total,
                    'historico_premiacoes_por_edicao': [],
                    'erro_historico': str(e_hist)
                })

        return jsonify({'escolas_publicas_alto_desempenho_obmep_2010_2023': resultados_finais_com_historico}), 200

    except Exception as e_geral:
        print(f"Erro geral na API: {e_geral}")
        return jsonify({'message': 'Erro interno no servidor ao processar a requisição', 'error': str(e_geral)}), 500

#OUTRO ENDPOINT VERSÃO 2

@app.route('/api/analise-distribuicao-pontuacao-obmep', methods=['GET'])
def analise_distribuicao_pontuacao():
    try:
        pipeline_todas_escolas_publicas_pontuadas = [
            {
                '$match': {
                    'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']},
                    'edicao': {'$gte': 2010, '$lte': 2023},
                    'tipo': {'$ne': 'P'} # CONFIRME O CAMPO E VALOR
                }
            },
            {
                '$addFields': {
                    'pontos_medalha': {
                        '$switch': {
                            'branches': [
                                {'case': {'$eq': ['$medalha', 'Ouro']}, 'then': 3},
                                {'case': {'$eq': ['$medalha', 'Prata']}, 'then': 2},
                                {'case': {'$eq': ['$medalha', 'Bronze']}, 'then': 1}
                            ],
                            'default': 0
                        }
                    }
                }
            },
            {
                '$group': {
                    '_id': {
                        'escola_obmep': '$escola',
                        'uf_obmep': '$uf',
                        'municipio_obmep': '$municipio'
                    },
                    'pontuacao_ponderada': {'$sum': '$pontos_medalha'},
                    'medalhas_simples': {'$sum': 1}
                }
            },
            {
                '$project': { # Não precisa mais do $project para renomear, o Pandas lida com _id
                    'pontuacao_ponderada': '$pontuacao_ponderada',
                    'medalhas_simples': '$medalhas_simples'
                    # Mantendo o _id para possível referência, embora não seja usado diretamente no Pandas depois
                }
            }
        ]

        cursor_todas_escolas = collection.aggregate(pipeline_todas_escolas_publicas_pontuadas, allowDiskUse=True)
        lista_todas_escolas = list(cursor_todas_escolas)

        if not lista_todas_escolas:
            return jsonify({'message': 'Nenhuma escola pública encontrada para análise de distribuição.'}), 404

        df_escolas = pd.DataFrame(lista_todas_escolas)

        if 'pontuacao_ponderada' not in df_escolas.columns or df_escolas['pontuacao_ponderada'].empty:
            return jsonify({'message': 'Dados de pontuação ponderada não encontrados ou vazios após agregação.'}), 500

        # --- Cálculos para a Análise da Distribuição ---
        descritivas = df_escolas['pontuacao_ponderada'].describe(
            percentiles=[.50, .75, .90, .95, .98, .99, .995, .999]
        ).to_dict() # Converte para dicionário para JSON

        percentis_calculados = {}
        contagem_acima_percentil = {}
        pontuacoes_para_percentis = [90, 95, 98, 99, 99.5, 99.9] # Adicione mais se precisar

        for p_val in pontuacoes_para_percentis:
            percentil_score = np.percentile(df_escolas['pontuacao_ponderada'], p_val)
            percentis_calculados[f'P{p_val}_pontuacao'] = round(percentil_score, 2)
            contagem_acima_percentil[f'N_escolas_acima_P{p_val}'] = int(df_escolas[df_escolas['pontuacao_ponderada'] >= percentil_score].shape[0])

        # Análise de Pareto Simplificada (quantas escolas para X% da pontuação)
        df_pareto = df_escolas.sort_values(by='pontuacao_ponderada', ascending=False).copy()
        df_pareto['pontuacao_acumulada_percent'] = (df_pareto['pontuacao_ponderada'].cumsum() / df_pareto['pontuacao_ponderada'].sum()) * 100

        pontos_pareto = {}
        for pct_pontuacao_alvo in [50, 75, 80, 90]: # % da pontuação total que queremos analisar
            try:
                # Encontra o primeiro índice onde a pontuação acumulada atinge ou ultrapassa o alvo
                idx_alvo = df_pareto[df_pareto['pontuacao_acumulada_percent'] >= pct_pontuacao_alvo].index[0]
                num_escolas_para_alvo = df_pareto.index.get_loc(idx_alvo) + 1 # +1 porque o índice é 0-based
                percentual_escolas_para_alvo = (num_escolas_para_alvo / len(df_pareto)) * 100
                pontos_pareto[f'N_escolas_para_{pct_pontuacao_alvo}%_pontuacao'] = num_escolas_para_alvo
                pontos_pareto[f'Percentual_escolas_para_{pct_pontuacao_alvo}%_pontuacao'] = round(percentual_escolas_para_alvo, 2)
            except IndexError: # Caso nenhuma escola alcance essa porcentagem (improvável para 50, 75, 80)
                pontos_pareto[f'N_escolas_para_{pct_pontuacao_alvo}%_pontuacao'] = "Não alcançado"
                pontos_pareto[f'Percentual_escolas_para_{pct_pontuacao_alvo}%_pontuacao'] = "Não alcançado"


        # Dados para Histograma (opcional, pode ser grande se muitas faixas)
        # counts, bin_edges = np.histogram(df_escolas['pontuacao_ponderada'], bins=50)
        # histogram_data = {'counts': counts.tolist(), 'bin_edges': bin_edges.tolist()}

        resposta_final = {
            'total_escolas_publicas_analisadas': len(df_escolas),
            'estatisticas_descritivas_pontuacao': descritivas,
            'pontuacao_por_percentil': percentis_calculados,
            'contagem_escolas_acima_de_cada_percentil': contagem_acima_percentil,
            'analise_pareto_simplificada': pontos_pareto,
            # 'dados_histograma': histogram_data # Descomente se quiser enviar dados para plotar histograma
        }

        return jsonify(resposta_final), 200

    except Exception as e:
        print(f"Erro no endpoint /api/analise-distribuicao-pontuacao-obmep: {e}")
        return jsonify({'message': 'Erro interno ao processar a análise de distribuição', 'error': str(e)}), 500

#VERSÃO 3
import numpy as np
# --- Constante com o valor de corte P98 ---
P98_PONTUACAO_CORTE = 37.0

def gerar_dados_distribuicao_completa():
    """
    Função auxiliar para obter os dados de pontuação de todas as escolas públicas.
    Retorna um DataFrame do Pandas.
    """
    # ATENÇÃO: Confirme o nome do campo 'tipo_escola' ou 'tipo'
    pipeline_todas_escolas = [
        {'$match': {'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']}, 'edicao': {'$gte': 2010, '$lte': 2023}, 'tipo': {'$ne': 'P'}}},
        {'$addFields': {'pontos_medalha': {'$switch': {'branches': [{'case': {'$eq': ['$medalha', 'Ouro']}, 'then': 3},{'case': {'$eq': ['$medalha', 'Prata']}, 'then': 2},{'case': {'$eq': ['$medalha', 'Bronze']}, 'then': 1}],'default': 0}}}},
        {'$group': {'_id': {'escola_obmep': '$escola', 'uf_obmep': '$uf', 'municipio_obmep': '$municipio'}, 'pontuacao_ponderada': {'$sum': '$pontos_medalha'}}},
        # Não precisa do $project final aqui se o DataFrame for criado a partir da lista de dicionários com _id
    ]
    cursor = collection.aggregate(pipeline_todas_escolas, allowDiskUse=True)
    # Transforma o _id em colunas separadas ao criar o DataFrame
    lista_cursor = list(cursor)
    if not lista_cursor:
        return pd.DataFrame() # Retorna DataFrame vazio se não houver dados

    df = pd.json_normalize(lista_cursor) # Normaliza o _id aninhado
    # Renomear colunas que vieram de _id.
    df.rename(columns={
        '_id.escola_obmep': 'escola',
        '_id.uf_obmep': 'uf',
        '_id.municipio_obmep': 'municipio'
    }, inplace=True)
    return df


@app.route('/api/analise-completa-escolas-p98-obmep', methods=['GET'])
def obter_analise_completa_escolas_p98():
    try:
        # --- Parte 1: Obter dados para a justificativa (distribuição completa) ---
        df_todas_escolas = gerar_dados_distribuicao_completa()

        if df_todas_escolas.empty or 'pontuacao_ponderada' not in df_todas_escolas.columns:
            return jsonify({'message': 'Não foi possível obter dados para a análise de distribuição.'}), 500

        # Calcular estatísticas descritivas para o JSON de retorno
        descritivas_distribuicao = df_todas_escolas['pontuacao_ponderada'].describe(
            percentiles=[.50, .75, .90, .95, .98, .99] # P98 já sabemos o valor
        ).round(2).to_dict()

        # Dados para o histograma (frequências e bins) para você plotar
        counts, bin_edges = np.histogram(df_todas_escolas['pontuacao_ponderada'], bins=50) # Ajuste bins conforme necessidade
        dados_histograma_json = {'frequencias': counts.tolist(), 'intervalos_bins': bin_edges.tolist()}

        n_escolas_acima_p98_calculado = df_todas_escolas[df_todas_escolas['pontuacao_ponderada'] >= P98_PONTUACAO_CORTE].shape[0]

        # --- Parte 2: Selecionar as escolas P98 e buscar seus históricos ---
        # ATENÇÃO: Confirme o nome do campo 'tipo_escola' ou 'tipo'
        pipeline_selecao_escolas_p98 = [
            {'$match': {'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']},'edicao': {'$gte': 2010, '$lte': 2023},'tipo': {'$ne': 'P'}}},
            {'$addFields': {'pontos_medalha': {'$switch': {'branches': [{'case': {'$eq': ['$medalha', 'Ouro']}, 'then': 3},{'case': {'$eq': ['$medalha', 'Prata']}, 'then': 2},{'case': {'$eq': ['$medalha', 'Bronze']}, 'then': 1}],'default': 0}}}},
            {'$group': {'_id': {'escola_obmep': '$escola','uf_obmep': '$uf','municipio_obmep': '$municipio'},'pontuacao_total_ponderada_periodo': {'$sum': '$pontos_medalha'},'total_medalhas_simples_periodo': {'$sum': 1}}},
            {'$match': {'pontuacao_total_ponderada_periodo': {'$gte': P98_PONTUACAO_CORTE}}},
            {'$sort': {'pontuacao_total_ponderada_periodo': -1}},
            {'$skip': 316},
            {'$limit': 1},
            {'$project': {'_id': 0,'identificador_escola_obmep': '$_id','pontuacao_ponderada_da_escola': '$pontuacao_total_ponderada_periodo','total_medalhas_simples_da_escola': '$total_medalhas_simples_periodo'}}
        ]

        cursor_escolas_p98 = collection.aggregate(pipeline_selecao_escolas_p98, allowDiskUse=True)
        lista_escolas_p98_selecionadas = list(cursor_escolas_p98)

        # Isso não deve acontecer se P98_PONTUACAO_CORTE for um valor válido da distribuição
        if not lista_escolas_p98_selecionadas:
            return jsonify({'message': 'Nenhuma escola pública encontrada acima do corte P98 para detalhamento.'}), 404


        resultados_finais_com_historico = []
        for escola_data in lista_escolas_p98_selecionadas:
            id_obmep = escola_data['identificador_escola_obmep']
            # ... (Lógica da Etapa 2 para buscar histórico - igual ao seu código original) ...
            match_criteria_historico = {'escola': id_obmep['escola_obmep'],'uf': id_obmep['uf_obmep'],'municipio': id_obmep['municipio_obmep'],'medalha': {'$in': ['Ouro', 'Prata', 'Bronze']},'edicao': {'$gte': 2010, '$lte': 2023}}
            pipeline_historico_escola = [
                {'$match': match_criteria_historico},
                {'$group': {'_id': {'edicao_hist': '$edicao', 'nivel_hist': '$nivel'},'quantidade_medalhas_nivel_edicao': {'$sum': 1}}},
                {'$sort': {'_id.edicao_hist': -1, '_id.nivel_hist': 1}},
                {'$group': {'_id': '$_id.edicao_hist','detalhes_por_nivel': {'$push': {'nivel': '$_id.nivel_hist','premiacoes': '$quantidade_medalhas_nivel_edicao'}},'total_medalhas_na_edicao_para_esta_escola': {'$sum': '$quantidade_medalhas_nivel_edicao'}}},
                {'$sort': {'_id': -1}},
                {'$project': {'_id': 0,'edicao': '$_id','total_medalhas_na_edicao': '$total_medalhas_na_edicao_para_esta_escola','premiacoes_por_nivel': '$detalhes_por_nivel'}}
            ]
            try:
                historico_cursor = collection.aggregate(pipeline_historico_escola, allowDiskUse=True)
                lista_historico_premiacoes_escola = list(historico_cursor)
                resultados_finais_com_historico.append({
                    'identificador_obmep': id_obmep,
                    'pontuacao_ponderada_total_2010_2023': escola_data['pontuacao_ponderada_da_escola'],
                    'total_medalhas_simples_2010_2023': escola_data['total_medalhas_simples_da_escola'],
                    'historico_premiacoes_por_edicao': lista_historico_premiacoes_escola
                })
            except Exception as e_hist:
                print(f"Erro ao buscar histórico para {id_obmep['escola_obmep']}: {e_hist}")
                resultados_finais_com_historico.append({'identificador_obmep': id_obmep,'pontuacao_ponderada_total_2010_2023': escola_data['pontuacao_ponderada_da_escola'],'total_medalhas_simples_2010_2023': escola_data['total_medalhas_simples_da_escola'],'historico_premiacoes_por_edicao': [],'erro_historico': str(e_hist)})

        linhas_csv = []
        for escola in resultados_finais_com_historico:
            id_obmep = escola['identificador_obmep']
            linha_base = {
                'escola': id_obmep['escola_obmep'],
                'uf': id_obmep['uf_obmep'],
                'municipio': id_obmep['municipio_obmep'],
                'pontuacao_ponderada_total_2010_2023': escola['pontuacao_ponderada_total_2010_2023'],
                'total_medalhas_simples_2010_2023': escola['total_medalhas_simples_2010_2023']
            }
            for historico in escola['historico_premiacoes_por_edicao']:
                linha = linha_base.copy()
                linha['edicao'] = historico['edicao']
                linha['total_medalhas_na_edicao'] = historico['total_medalhas_na_edicao']


    # Detalhar por nível
                niveis = {d['nivel']: d['premiacoes'] for d in historico['premiacoes_por_nivel']}
                for nivel, quantidade in niveis.items():
                    linha[f'medalhas_nivel_{nivel}'] = quantidade

                linhas_csv.append(linha)
                historico_existe = True

            # Se não houver histórico, registrar mesmo assim
            if not historico_existe:
                linha_sem_historico = linha_base.copy()
                linha_sem_historico['edicao'] = 'Sem histórico'
                linha_sem_historico['total_medalhas_na_edicao'] = 0
                for nivel in [1, 2, 3]:
                    linha_sem_historico[f'medalhas_nivel_{nivel}'] = 0
                linhas_csv.append(linha_sem_historico)

        # Criar DataFrame
        df_csv = pd.DataFrame(linhas_csv)
        # Diagnóstico adicional
        print(f"Total de escolas no CSV final: {df_csv['escola'].nunique()}")
        print(f"Total de escolas retornadas da API (P98): {len(resultados_finais_com_historico)}")

        # Salvar como CSV
        print("SALVANDO....")
        caminho_csv = 'escolas_p98_com_historicoHELP.csv'
        df_csv.to_csv(caminho_csv, index=False, encoding='utf-8-sig')
        print("ARQUIVO SALVO!")

        lista_escolas_api = [
            (
                escola['identificador_obmep']['escola_obmep'],
                escola['identificador_obmep']['uf_obmep'],
                escola['identificador_obmep']['municipio_obmep']
            )
            for escola in resultados_finais_com_historico
        ]

# Salvar essa lista como CSV temporário para comparação
        df_escolas_api = pd.DataFrame(lista_escolas_api, columns=['escola', 'uf', 'municipio'])
        df_escolas_api.to_csv('escolas_api_lista.csv', index=False, encoding='utf-8-sig')
        print("Lista de escolas da API salva como escolas_api_lista.csv")



        return jsonify({
            'justificativa_selecao': {
                'mensagem': f"Seleção do grupo de estudo baseada no P98 (pontuação ponderada >= {P98_PONTUACAO_CORTE}), resultando em {len(lista_escolas_p98_selecionadas)} escolas de um total de {len(df_todas_escolas)} escolas públicas premiadas (representando aproximadamente o top 2%).",
                'total_escolas_publicas_premiadas_periodo': len(df_todas_escolas),
                'p98_valor_corte': P98_PONTUACAO_CORTE,
                'n_escolas_selecionadas_p98': len(lista_escolas_p98_selecionadas), # Deve ser igual a n_escolas_acima_p98_calculado
                'estatisticas_descritivas_distribuicao_geral': descritivas_distribuicao,
                'dados_para_plot_histograma': dados_histograma_json # Você usa isso para gerar seu gráfico
            },
            'escolas_p98_selecionadas_com_historico': resultados_finais_com_historico
        }), 200


    except Exception as e_geral:
        print(f"Erro geral na API: {e_geral}")
        return jsonify({'message': 'Erro interno no servidor ao processar a requisição', 'error': str(e_geral)}), 500

#VERSÃO 3




# ... (seu if __name__ == '__main__': app.run(debug=True) existente) ...
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(sys.path)
    app.run(host='0.0.0.0', port=port, debug=True)
