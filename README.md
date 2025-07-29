# Perfil de Escolas de Alto Desempenho na OBMEP: Análise Longitudinal e Sistema de Recomendação

Este repositório contém o código, os dados tratados e os recursos relacionados à pesquisa de mestrado profissional que investiga o perfil de escolas públicas de alto desempenho na Olimpíada Brasileira de Matemática das Escolas Públicas (OBMEP), com foco em uma análise longitudinal e no desenvolvimento de um protótipo de sistema de recomendação.

## 🚀 Sobre o Projeto

A Olimpíada Brasileira de Matemática das Escolas Públicas (OBMEP) é a maior competição científica do Brasil, com milhões de estudantes participantes anualmente. Apesar de seu impacto consolidado, a literatura ainda carece de uma compreensão aprofundada sobre o **perfil multifacetado e a evolução longitudinal das escolas que consistentemente alcançam os mais altos patamares de premiação** em nível nacional.

Este projeto busca preencher essa lacuna, identificando o perfil dessas "escolas de elite" e analisando como suas características (socioeconômicas, infraestrutura, corpo docente, desempenho em avaliações externas e contexto municipal) se modificaram entre 2010 e 2023. Adicionalmente, o estudo culmina no desenvolvimento de um **protótipo de sistema de recomendação** baseado em Inteligência Artificial para auxiliar gestores escolares.

## 🎯 Objetivos da Pesquisa

*   Mapear o perfil multidimensional das escolas públicas com desempenho consistentemente elevado na OBMEP (2010-2023) e analisar a evolução temporal de suas características.
*   A partir dos padrões de excelência identificados, desenvolver um *framework* de apoio à decisão, materializado em um protótipo de sistema de recomendação.

## ✨ Principais Insights (Resultados Parciais)

As análises preliminares sobre o perfil das 315 escolas de elite (top 2% das premiadas) já revelam padrões significativos:

*   **Dependência Administrativa:** As escolas da rede Federal apresentam uma taxa de sucesso para figurar no grupo de elite desproporcionalmente maior (aprox. 17 vezes mais chances que as estaduais).
*   **Localização Geográfica:** O perfil de excelência é predominantemente urbano (99.7% das escolas do grupo P98).
*   **Evolução da Infraestrutura:** As escolas de elite já possuíam alta infraestrutura digital em 2010 e mantiveram ou aprimoraram seus recursos ao longo dos 14 anos (ex: crescimento notável em quadras cobertas).
*   **Evolução do Porte Escolar:** Observa-se uma tendência geral de redução no porte médio das escolas de elite (de >1.150 alunos em 2010 para ~980 em 2023), mesmo mantendo-se como instituições de grande porte em comparação à média nacional.

## 🛠️ Metodologia e Tecnologias

A pesquisa adota uma abordagem **quantitativa e longitudinal**, baseada na integração de múltiplas bases de dados secundários:

*   **Seleção do Grupo de Estudo:** 315 escolas de elite identificadas via pontuação ponderada de medalhas da OBMEP e critério do 98º percentil (P98).
*   **Coleta de Dados:** Extração e consolidação de dados da **OBMEP**, **Microdados do Censo Escolar** (2010-2023), **INSE**, **SAEB/IDEB**, e indicadores docentes. A coleta inicial dos dados da OBMEP foi realizada via **Web Scraping** com **UiPath**. A atribuição dos códigos **INEP** foi feita manualmente para garantir a unicidade.
*   **Tratamento de Dados:** Utilização de técnicas como **LOCF (Last Observation Carried Forward)** para variáveis estáveis e **Interpolação Linear** para variáveis quantitativas com ausências pontuais, lidando com um painel de dados desbalanceado.
*   **Integração e Análise:** Desenvolvimento de scripts em **Python** com as bibliotecas **Pandas** e **NumPy**.
*   **Visualização:** Geração de gráficos para análise descritiva e longitudinal utilizando **Matplotlib** e **Seaborn**.
*   **Sistema de Recomendação:** Prototipagem de uma ferramenta que utiliza os perfis identificados, alimentando um **Modelo de Linguagem de Larga Escala (LLM)** como **Google Gemini** para gerar recomendações contextualizadas.

## 📂 Estrutura do Repositório
.
├── data/
│ ├── raw/ # Microdados brutos do Censo, INSE, SAEB/IDEB
│ ├── processed/ # Planilha OBMEP com INEP e dados tratados
│ └── final/ # Dataset longitudinal final cruzado
├── notebooks/ # Jupyter Notebooks para análise exploratória e scripts de processamento
│ ├── 01_selecao_escolas_obmep.ipynb
│ ├── 02_atribuicao_inep.ipynb
│ ├── 03_integracao_censo_docentes.ipynb
│ ├── 04_integracao_inse_ideb_idh.ipynb
│ └── 05_analise_resultados_parciais.ipynb
├── src/ # Código-fonte para o protótipo de recomendação (se aplicável)
│ └── recommendation_system.py
├── docs/ # Documentação adicional, relatórios intermediários
│ └── qualificação_mestrado.pdf
├── figures/ # Imagens de gráficos geradas
└── README.md # Este arquivo

## 🚀 Como Executar (Exemplo)

1.  **Clone o repositório:**
    `git clone https://github.com/SeuUsuario/NomeDoRepositorio.git`
    `cd NomeDoRepositorio`
2.  **Instale as dependências:**
    `pip install pandas numpy matplotlib seaborn requests`
3.  **Baixe os Microdados:** Os microdados completos do Censo, INSE, SAEB/IDEB devem ser baixados dos portais do INEP e organizados na pasta `data/raw/` conforme a estrutura de leitura dos notebooks.
4.  **Execute os Notebooks:** Siga a sequência dos notebooks `01_` a `05_` em `notebooks/` para replicar o processo de seleção, integração e análise de dados.

## 🤝 Contribuição e Contato

Contribuições são bem-vindas! Se tiver sugestões ou dúvidas, entre em contato:

*   **Miqueias Soares Cardoso**
*   Email: miqueiassoarescardoso@gmail.com

## 📄 Licença

Este projeto está licenciado sob a licença [Escolha uma licença, ex: MIT License] - veja o arquivo `LICENSE` para mais detalhes.

---
