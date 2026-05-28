# BoletoFlow Engine ⚙️

Núcleo de extração vetorial e processamento espacial para automação de faturas financeiras e boletos bancários (Padrões FEBRABAN e Arrecadação).

## 🎯 O Custo do Problema

A extração manual de dados em lotes de faturas (como faturas de energia, telecomunicações e borderôs atacadistas) gera um gargalo operacional massivo. Digitar linhas de 47 ou 48 dígitos manualmente resulta em quebras de caixa por falha humana, multas por atraso (vencimentos lidos incorretamente) e um desperdício incalculável de horas-homem em tarefas puramente administrativas.

O **BoletoFlow Engine** é uma API construída para substituir esse trabalho braçal. Ele recebe documentos PDF complexos, varre a geometria das páginas e devolve os dados estruturados em milissegundos.

## 🧠 Arquitetura e Engenharia

Este não é um simples extrator de texto baseado em Regex. Documentos financeiros reais possuem layouts caóticos, marcas d'água, códigos repetidos e linhas digitáveis fragmentadas ou ausentes. Para garantir precisão absoluta, o motor foi forjado com três pilares de engenharia:

1. **Reconstrução Geométrica (Spatial Bounding Boxes):** O motor contorna as falhas de formatação de PDFs legados agrupando caracteres pelas suas coordenadas `(X, Y)`. Ele cria "linhas físicas" virtuais na memória RAM para garantir que a leitura de blocos numéricos não sofra colisões com outras informações na página.
2. **Processamento em Lote com Idempotência (Hash Sets):** Projetado para faturas corporativas de múltiplas páginas, o sistema acumula todas as faturas encontradas em um único processamento vetorial (Array). Para evitar a duplicação de dados gerada por boletos impressos duas vezes na mesma folha (Ficha de Compensação e Recibo), o algoritmo utiliza conjuntos (`set`) de busca $O(1)$ para barrar códigos repetidos na porta de entrada, economizando ciclos de CPU.
3. **Escalonamento Tático de Extração (Marco Zero):** A localização do vencimento não usa âncoras fixas. O algoritmo crava um alfinete matemático nas coordenadas do código de barras recém-descoberto e usa o Teorema de Pitágoras (Distância Euclidiana) para rastrear os rótulos e datas mais próximos àquele boleto específico, ignorando datas fantasmas ou faturas vizinhas na mesma folha.

## 🛠️ Stack Tecnológica

* **Linguagem:** Python 3.10+
* **Framework:** FastAPI / Uvicorn (Alta performance e assincronismo)
* **Motor de Geometria:** pdfplumber (Baseado em pdfminer.six)
* **Isolamento de Erros:** Traceback puro e contingência silenciosa com manipulação de `logging`.

## 🚀 Como Executar (Ambiente Local)

1. Clone este repositório e acesse a pasta raiz.
2. Crie um ambiente virtual para isolar as dependências:
   ```bash
   python -m venv venv
   source venv/bin/activate  # No Linux/Mac
Instale as dependências estritas do projeto:

Bash
pip install -r requirements.txt
Suba o servidor Uvicorn:

Bash
uvicorn servidor:app --reload
O motor estará escutando na porta http://localhost:8000.

📡 Endpoints (API)
POST /api/extrair
Recebe o arquivo físico (PDF) via formulário multipart/form-data e retorna um JSON contendo a matriz de faturas extraídas. O ambiente está configurado para lidar graciosamente com falhas parciais (Fallback para "Revisão Manual") sem derrubar o serviço.


***
