from flask import Flask
import requests
import pandas as pd
import json
from datetime import date
from datetime import datetime
import sendgrid
import os
import os.path
from sendgrid.helpers.mail import Mail, Email, To, Content
import getpass
import requests

app = Flask(__name__)

@app.route("/")
def gastos_deputados():
    return "Olá, este site coleta os gastos com alimentação dos deputados federais dos estados do Nordeste"

#Função para coletar os dados da API da Câmara dos Deputados, com filtro nos estados do Nordeste
@app.route('/sobre')
def enviando_email():
    url = 'https://dadosabertos.camara.leg.br/api/v2/deputados'
    params = {
        'formato': 'json',
        'itens': 100,
        'siglaUf': 'AL,BA,CE,MA,PB,PE,PI,RN,SE',
        'idLegislatura': '57',
        'ordenarPor': 'siglaUf'
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        deputados = response.json()['dados']
    else:
        print('Erro ao obter dados dos deputados')
        deputados = []
        
    #Filtrando apenas as despesas com alimentação 
    from pandas.io.formats.info import DataFrameTableBuilder
    ALIMENTACAO = 'FORNECIMENTO DE ALIMENTAÇÃO DO PARLAMENTAR'
    despesas_total = []

    # Verificar se já existe um arquivo CSV com despesas antigas
    if os.path.exists('despesas_alimentacao.csv'):
        df_despesas_antigas = pd.read_csv('despesas_alimentacao.csv')
        despesas_total = df_despesas_antigas.to_dict('records')

    # Criar um conjunto contendo todos os códigos de documentos enviados
    cod_documentos_enviados = set(row['codDocumento'] for row in despesas_total)

    for deputado in deputados[:2]:
        url_despesas = f'https://dadosabertos.camara.leg.br/api/v2/deputados/{deputado["id"]}/despesas'
        params_despesas = {
            'formato': 'json',
            'itens': 100,
             'ordenarPor':'ano',
             'ordem':'DESC'
        }

        response_despesas= requests.get(url_despesas, params=params_despesas)

        if response_despesas.status_code == 200:
            despesas = response_despesas.json()['dados']
        else:
            despesas = []    

        for despesa in despesas:
            despesa['siglaUf'] = deputado['siglaUf']
            despesa['nomeParlamentar'] = deputado['nome']
            if despesa['codDocumento'] not in cod_documentos_enviados:
                despesas_total.append(despesa)
                cod_documentos_enviados.add(despesa['codDocumento'])

    despesas_alimentacao = [despesa for despesa in despesas_total if despesa['tipoDespesa'] == ALIMENTACAO]
    despesas_acima_100 = [despesa for despesa in despesas_alimentacao if despesa['valorLiquido'] >= 100]

    df_despesas = pd.DataFrame(despesas_acima_100)

    # Selecionando apenas as colunas que você deseja manter no arquivo CSV
    df_despesas = df_despesas[['nomeParlamentar', 'siglaUf', 'tipoDespesa', 'nomeFornecedor','cnpjCpfFornecedor','valorLiquido', 'mes', 'ano','codDocumento']]

    # Salvando o DataFrame como um arquivo CSV
    df_despesas.to_csv('despesas_alimentacao.csv', index=False)

    #datas e dias da semana

    hj = date.today()
    dias = ('terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo', 'segunda-feira')
    dia_semana = dias[hj.weekday()]
    data_atual = datetime.now()
    mes_atual = data_atual.strftime('%m')
    dia_atual = data_atual.strftime('%d')

    estado = ['BA', 'SE', 'AL', 'PE', 'RN', 'PB', 'CE', 'PI', 'MA']

    #informações do fornecedor e gastos

    nomeFornecedor='' #como trazer as informações do fornecedor para essa variável?

    valorLiquido='' #como trazer as informações do valor para essa variável?

    meses_pt = {
        "January": "Janeiro",
        "February": "Fevereiro",
        "March": "Março",
        "April": "Abril",
        "May": "Maio",
        "June": "Junho",
        "July": "Julho",
        "August": "Agosto",
        "September": "Setembro",
        "October": "Outubro",
        "November": "Novembro",
        "December": "Dezembro"
    }
    linhas = []
    # loop através de cada linha do dataframe "despesas"
    for index, row in df_despesas.iterrows():
        parlamentar = row["nomeParlamentar"]
        nome_estabelecimento= row['nomeFornecedor']
        valor_liquido = row['valorLiquido']
        mes = meses_pt[datetime.strptime(str(row['mes']), '%m').strftime('%B')].lower()
        ano=row['ano']
        cnpj=row['cnpjCpfFornecedor']

        # aqui vem o resto do código para gerar o texto do e-mail para cada despesa

#         texto = (f"No mês de {mes} de {ano}, {parlamentar} gastou R$ {valor_liquido} no estabelecimento {nome_estabelecimento}, que tem como CNPJ {cnpj}.")
#         print(texto) #alterei para imprimir cada texto no console, para visualização
#         linhas.append(texto + "\n") # adiciona a quebra de linha
#         # junta todas as linhas em uma única string
#         textofinal = "".join(linhas)
#         print(textofinal)
        
        # define o texto introdutório
        texto_intro = "Olá, como vai? A seguir você confere a lista de despesas do parlamentar no mês de {mes} de {ano}:\n\n"

        # inicia a lista de linhas vazia
        linhas = []

        # loop sobre as despesas do parlamentar
        for despesa in despesas:

            # extrai os dados da despesa
            mes = despesa['mes']
            ano = despesa['ano']
            parlamentar = despesa['parlamentar']
            valor_liquido = despesa['valor_liquido']
            nome_estabelecimento = despesa['nome_estabelecimento']
            cnpj = despesa['cnpj']

            # gera o texto da despesa
            texto = (f"No mês de {mes} de {ano}, {parlamentar} gastou R$ {valor_liquido} no estabelecimento {nome_estabelecimento}, que tem como CNPJ {cnpj}.")

            # adiciona o texto da despesa à lista de linhas
            linhas.append(texto + "\n")

        # adiciona a quebra de linha
        linhas.append("\n")

        # junta todas as linhas em uma única string
        textofinal = "".join(linhas)

        # adiciona o texto introdutório no início da string
        textofinal = texto_intro.format(mes=mes, ano=ano) + textofinal

        # imprime o texto final
        print(textofinal)


    sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    from_email = Email("ola@agenciatatu.com.br")  # Change to your verified sender
    to_email = To("graziela.fcs@gmail.com")  # Change to your recipient
    subject = "Confira as despesas com alimentação dos deputados federais do NE"

    conteudo_email = f"{textofinal}" 
    content = Content("text/plain", conteudo_email)
    mail = Mail(from_email, to_email, subject, content)


    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()
    # Send an HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)
    print(response.status_code)
    print(response.headers)
