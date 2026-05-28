import math
import re
import pdfplumber
from datetime import date, timedelta
import traceback
import logging # <-- NOVA IMPORTAÇÃO

# Silencia os avisos de FontBBox e outras anomalias de PDFs malformados.
# Dizemos ao motor para só imprimir algo no terminal se for um ERRO CRÍTICO (ERROR), ignorando avisos (WARNING).
logging.getLogger("pdfminer").setLevel(logging.ERROR)

def buscar_valor(barcode, tipo_barcode):
    """
    Função matemática pura. Não acessa o arquivo físico.
    Transforma a string do código de barras em um float de valor monetário.
    """
    try:
        if tipo_barcode == 48:
            # Arrecadação: O valor está fatiado em duas partes
            valor = float(barcode[4:11] + barcode[12:16]) / 100
            return valor
        elif tipo_barcode == 47:
            # Cobrança FEBRABAN: Os últimos 10 dígitos formam o valor
            valor = float(str(barcode)[-10:]) / 100
            return valor
        else:
            return "Revisão Manual"
    except Exception:
        # Se a matemática falhar (ex: boleto zerado), não quebramos o servidor.
        return "Falha na leitura do valor"

def buscar_vencimento(pagina_alvo, barcode, tipo_barcode):
    """
    Função tática. Executa matemática rápida ou varredura espacial pesada
    APENAS se for estritamente necessário.
    """
    try:
        # 1. A VIA EXPRESSA (Matemática FEBRABAN)
        # Se for padrão 47 e o fator de vencimento for maior que zero, ignoramos o mapa espacial.
        if tipo_barcode == 47 and int(str(barcode)[33:37]) != 0:
            vencimento = date(2022, 5, 29) + timedelta(days=int(str(barcode)[33:37]))
            return vencimento.strftime("%d/%m/%Y")

        # 2. A VIA ESPACIAL EM CADEIA (Para padrão 48 ou fator 0000)
        # Só executamos o extract_words() quando a matemática falha.
        palavras = pagina_alvo.extract_words()
        
        # PASSO 2.1: Encontrar o Marco Zero (Reconstrução Geométrica de Linhas)
        linhas_visuais = []
        
        # 1. Agrupa as palavras fragmentadas em linhas baseadas na coordenada Y
        for p in palavras:
            adicionado = False
            for linha in linhas_visuais:
                # Tolerância de 4 pixels de altura para considerar que estão na mesma linha
                if abs(linha['top'] - p['top']) < 4:
                    linha['palavras'].append(p)
                    adicionado = True
                    break
            
            if not adicionado:
                # Cria uma nova linha visual se a palavra estiver em uma altura inédita
                linhas_visuais.append({'top': p['top'], 'palavras': [p]})

        marco_zero = None
        
        # 2. Varre as linhas remontadas para achar o código inteiro
        for linha in linhas_visuais:
            # Ordena as palavras da linha da esquerda para a direita (coordenada X)
            linha['palavras'].sort(key=lambda w: w['x0'])
            
            # Concatena todos os dígitos puros encontrados nesta linha horizontal
            numeros_da_linha = "".join([re.sub(r"\D", "", w["text"]) for w in linha['palavras']])
            
            # O teste de precisão absoluta: O código TEM que estar nesta linha exata
            if barcode in numeros_da_linha:
                # O Marco Zero se torna a primeira palavra do Bounding Box dessa linha
                marco_zero = linha['palavras'][0]
                break
                
        # FALLBACK: Se a linha digitável for uma imagem e o texto não existir
        if not marco_zero:
            return "Revisão Manual (Coordenada cega)"

        # PASSO 2.2: Achar o rótulo "vencimento" mais próximo do Marco Zero
        ancora_vencimento = None
        menor_distancia_venc = float('inf') # Começa com distância infinita
        
        for p in palavras:
            if "vencimento" in p["text"].lower():
                # Teorema de Pitágoras para medir a distância da palavra até o código de barras atual
                dist = math.hypot(p['x0'] - marco_zero['x0'], p['top'] - marco_zero['top'])
                if dist < menor_distancia_venc:
                    menor_distancia_venc = dist
                    ancora_vencimento = p
                    
        if not ancora_vencimento:
            return "Revisão Manual (Rótulo não encontrado)"

        # PASSO 2.3: Achar a data real mais próxima do rótulo "vencimento"
        possiveis_datas = []
        for p in palavras:
            if re.match(r"\d{2}/\d{2}/\d{4}", p["text"]):
                # Filtro: Ignora datas que estão visualmente acima do rótulo (cabeçalhos velhos)
                if p['top'] >= (ancora_vencimento['top'] - 5):
                    # Filtro: Ignora datas que estão exatamente na mesma posição vertical grudadas à esquerda
                    if abs(p['top'] - ancora_vencimento['top']) < 5 and p['x0'] <= ancora_vencimento['x0']:
                        continue 
                    
                    distancia_data = math.hypot(p['x0'] - ancora_vencimento['x0'], p['top'] - ancora_vencimento['top'])
                    possiveis_datas.append((distancia_data, p['text']))

        if possiveis_datas:
            # Ordena as datas pela menor distância (índice 0 da tupla) e retorna o texto (índice 1)
            possiveis_datas.sort(key=lambda x: x[0])
            return possiveis_datas[0][1] 
        else:
            return "Revisão Manual (Data ilegível)"

    except Exception:
        # Erro silencioso de contingência. Mantém o motor rodando para o próximo boleto.
        return "Falha estrutural"

def extrair_boletos_em_lote(caminho_arquivo):
    """
    A FUNÇÃO MESTRA. Opera de forma vetorial e possui filtro 
    de idempotência (Set) para ignorar códigos repetidos na mesma fatura.
    """
    padrao_48 = r"(8\d{10}[.\- ]*\d)[.\- ]*(\d{11}[.\- ]*\d)[.\- ]*(\d{11}[.\- ]*\d)[.\- ]*(\d{11}[.\- ]*\d)"
    padrao_47 = r"(\d{5}[.\- ]*\d{5})[.\- ]*(\d{5}[.\- ]*\d{6})[.\- ]*(\d{5}[.\- ]*\d{6})[.\- ]*(\d)[.\- ]*(\d{14})"
    
    lote_extraido = []
    
    # 1. O ESCUDO: Memória de curto prazo para a fatura atual
    codigos_processados = set() 

    try:
        with pdfplumber.open(caminho_arquivo) as pdf:
            
            for pagina in pdf.pages:
                texto_bruto = pagina.extract_text()
                
                if not texto_bruto:
                    continue
                texto_bruto = texto_bruto.lower()
   
                # =========================================================
                # CAÇADA PADRÃO 48
                # =========================================================
                for match in re.finditer(padrao_48, texto_bruto):
                    codigo = re.sub(r"\D", "", "".join(match.groups()))
                    
                    # 2. A BARREIRA: Se o código já está no set, aborte este ciclo e vá para o próximo
                    if codigo in codigos_processados:
                        continue
                    
                    # 3. Se passou pela barreira, registre imediatamente para não processar de novo
                    codigos_processados.add(codigo)
                    
                    # 4. Só agora gastamos CPU com cálculos e varredura espacial
                    vencimento = buscar_vencimento(pagina, codigo, 48)
                    valor = buscar_valor(codigo, 48)
                    
                    lote_extraido.append({
                        "codigo": codigo,
                        "vencimento": vencimento,
                        "valor": valor,
                        "pagina": pagina.page_number
                    })

                # =========================================================
                # CAÇADA PADRÃO 47
                # =========================================================
                for match in re.finditer(padrao_47, texto_bruto):
                    codigo = re.sub(r"\D", "", "".join(match.groups()))
                    
                    if codigo in codigos_processados:
                        continue
                        
                    codigos_processados.add(codigo)
                    
                    vencimento = buscar_vencimento(pagina, codigo, 47)
                    valor = buscar_valor(codigo, 47)
                    
                    lote_extraido.append({
                        "codigo": codigo,
                        "vencimento": vencimento,
                        "valor": valor,
                        "pagina": pagina.page_number,
                    })

        if len(lote_extraido) == 0:
            return {"status": "erro", "mensagem": "Nenhum código de barras legível foi localizado neste documento."}

        return {
            "status": "sucesso",
            "quantidade": len(lote_extraido),
            "boletos": lote_extraido
        }
    
    except Exception as e:
        metadado = traceback.format_exc()
        print(f"\n[ERRO CATASTRÓFICO NO SERVIDOR]\n{metadado}")
        return {"status": "erro", "mensagem": "O motor colapsou ao tentar processar a estrutura matriz deste arquivo."}

# Teste local opcional (Comente ou apague em produção)
#if __name__ == "__main__":
#    resultado = extrair_boletos_em_lote("amostra.pdf")

#    print(resultado)