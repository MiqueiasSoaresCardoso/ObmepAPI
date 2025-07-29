import os
import pdfkit
import hashlib

# Função para gerar hash SHA-256 de um arquivo
def gerar_hash_arquivo(nome_arquivo):
    sha256 = hashlib.sha256()
    with open(nome_arquivo, 'rb') as f:
        while True:
            bloco = f.read(4096)  # Leitura por blocos de 4KB
            if not bloco:
                break
            sha256.update(bloco)
    return sha256.hexdigest()

# Função para gerar PDF único com índice
def gerar_pdf_unico(conteudos, caminho_saida):
    # Defina o caminho para o executável wkhtmltopdf
    path_to_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

    # Inicializa o conteúdo do PDF com um índice vazio
    conteudo_pdf = '<html><head><meta charset="utf-8"></head><body>'

    # Adiciona cada conteúdo de arquivo ao PDF com link para o nome do arquivo
    for nome_arquivo, conteudo in conteudos.items():
        nome_projeto = os.path.splitext(nome_arquivo)[0]  # Nome do arquivo sem extensão
        conteudo_pdf += f'<h1><a name="{nome_projeto}">{nome_arquivo}</a></h1>'
        conteudo_pdf += f'<pre>{conteudo}</pre>'

    conteudo_pdf += '</body></html>'

    # Use a configuração para gerar o PDF
    pdfkit.from_string(conteudo_pdf, caminho_saida, configuration=config)

def juntar_codigo_em_pdf(diretorio_projeto, caminho_saida_pdf):
    conteudos = {}  # Dicionário para armazenar conteúdo de cada arquivo

    # Função para percorrer recursivamente as pastas e coletar arquivos
    def percorrer_pastas(diretorio):
        for nome_arquivo in os.listdir(diretorio):
            caminho_arquivo = os.path.join(diretorio, nome_arquivo)

            if os.path.isdir(caminho_arquivo):
                # Se for um diretório, chama recursivamente a função
                percorrer_pastas(caminho_arquivo)
            else:
                # Verifica se o arquivo é um arquivo de texto
                if nome_arquivo.endswith('.html') or nome_arquivo.endswith('.css') or nome_arquivo.endswith('.js'):
                    with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                        conteudo = arquivo.read()
                        conteudos[nome_arquivo] = conteudo

    # Percorre o diretório do projeto
    percorrer_pastas(diretorio_projeto)

    # Gerar PDF único com todo o código coletado
    gerar_pdf_unico(conteudos, caminho_saida_pdf)

    # Gerar hash para o PDF gerado
    hash_pdf = gerar_hash_arquivo(caminho_saida_pdf)
    print(f'Arquivo PDF gerado: {caminho_saida_pdf}')
    print(f'Hash SHA-256 do PDF: {hash_pdf}')



# Exemplo de uso
if __name__ == "__main__":
    diretorio_projeto = 'C:\\Users\\mique\\OneDrive\\Área de Trabalho\\Obmep\\Frontend\\src'
    caminho_saida_pdf = 'C:\\Users\\mique\\OneDrive\\Área de Trabalho\\Obmep'
    juntar_codigo_em_pdf(diretorio_projeto,caminho_saida_pdf)

