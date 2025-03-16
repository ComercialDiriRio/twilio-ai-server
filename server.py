from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
import openai
import os
import requests
import random
import datetime

app = Flask(__name__)

# Configurar a API da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Perfis de clientes simulados - Todos começam com objeções
perfis_clientes = {
    "pesquisando": "Você está apenas pesquisando e não tem certeza se quer comprar agora. Faça perguntas genéricas e mostre dúvidas sobre o financiamento.",
    "preocupado": "Você acha que os preços estão muito altos e tem medo de assumir um financiamento. Questione as taxas e condições de pagamento.",
    "sem_tempo": "Você diz que está sem tempo para pensar nisso agora e evita se comprometer com uma visita ao stand.",
    "desconfiado": "Você tem medo de golpes ou promessas exageradas e questiona se o empreendimento é realmente uma boa opção.",
    "protelador": "Você sempre diz que vai pensar melhor e deixa a decisão para depois, sem marcar visitas.",
}

# Opções aleatórias para personalização do cliente
nomes_clientes = ["João", "Maria", "Carlos", "Ana", "Ricardo", "Fernanda", "Paulo", "Juliana", "Gabriel", "Camila"]
sobrenomes_clientes = ["Silva", "Oliveira", "Santos", "Ferreira", "Almeida", "Costa", "Pereira", "Martins", "Gomes", "Rodrigues"]
lugares_moradia = ["Centro do Rio", "Copacabana", "Barra da Tijuca", "Campo Grande", "São Gonçalo", "Niterói", "Nova Iguaçu"]
composicao_renda = ["Sozinho", "Com cônjuge", "Com pais", "Com irmãos", "Com amigo", "Com companheiro informal"]
tipo_renda = ["Formal", "Informal", "Mista (parte formal, parte informal)"]

# Lista de empreendimentos da Direcional no Rio de Janeiro
empreendimentos_rj = [
    {
        "nome": "Direcional Vert Alcântara",
        "local": "São Gonçalo",
        "stand": "Estrada dos Bandeirantes, 106 – Taquara",
    },
    {
        "nome": "Olinda Ellis",
        "local": "Campo Grande",
        "stand": "Rua Olinda Ellis, 810 – Campo Grande",
    },
    {
        "nome": "Reserva do Sol",
        "local": "Jacarepaguá",
        "stand": "Av. Embaixador Abelardo Bueno, 3300 – Jacarepaguá",
    }
]

# Dicionário para armazenar os dados do cliente e a última data de interação do corretor
conversas = {}

@app.route("/")
def home():
    return "Servidor está rodando!"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    """Responde mensagens no WhatsApp"""
    try:
        user_id = request.form.get("From", "")  # Identifica o corretor pelo número de telefone
        user_message = request.form.get("Body", "").strip().lower()

        # Se a mensagem for "cliente reiniciar", gera um novo cliente
        if user_message == "cliente reiniciar":
            cliente = gerar_novo_cliente()
            conversas[user_id] = (datetime.date.today(), cliente)
            return "Novo cliente gerado! Você pode começar a conversa."

        response_text = gerar_resposta_ia(user_message, user_id)

        response = MessagingResponse()
        response.message(response_text)

        return str(response)

    except Exception as e:
        return f"Erro ao processar mensagem do WhatsApp: {str(e)}"

@app.route("/voice", methods=["POST"])
def voice():
    """Responde chamadas de voz do Twilio"""
    try:
        user_id = request.form.get("Caller", "")  # Identifica o corretor pelo número de telefone
        user_input = request.form.get("SpeechResult", "")

        if not user_input:
            user_input = "Olá, estou interessado em um apartamento."

        response_text = gerar_resposta_ia(user_input, user_id)

        resposta = VoiceResponse()
        resposta.say(response_text, voice="alice", language="pt-BR")

        return str(resposta)

    except Exception as e:
        return f"Erro no processamento da chamada: {str(e)}"

def gerar_resposta_ia(texto_usuario, user_id):
    """Gera resposta baseada no comportamento do corretor"""
    try:
        data_hoje = datetime.date.today()

        # Se o corretor já tem um cliente definido, verifica se precisa mudar
        if user_id in conversas:
            ultima_data, cliente_info = conversas[user_id]
            if ultima_data == data_hoje:
                cliente = cliente_info  # Mantém o mesmo cliente durante o dia
            else:
                cliente = gerar_novo_cliente()
                conversas[user_id] = (data_hoje, cliente)
        else:
            cliente = gerar_novo_cliente()
            conversas[user_id] = (data_hoje, cliente)

        # Avalia se o corretor perguntou o nome do cliente
        if "seu nome" in texto_usuario or "como você se chama" in texto_usuario:
            nome_cliente = f"{cliente['nome']} {cliente['sobrenome']}"
        else:
            nome_cliente = "Prefiro não dizer no momento."

        # Avaliar a resposta do corretor
        feedback = avaliar_resposta_corretor(texto_usuario)

        # Se o corretor estiver indo bem, o cliente aceita uma visita
        if feedback == "positivo":
            return f"{nome_cliente}: Você me convenceu! Podemos marcar uma visita ao stand em {cliente['stand']}?"

        # Se o corretor estiver indo mal, o cliente enrola
        elif feedback == "neutro":
            return f"{nome_cliente}: Ainda não tenho certeza... Preciso pensar mais um pouco."

        # Se for muito mal, o cliente para de responder
        else:
            return f"{nome_cliente} parou de responder."

    except Exception as e:
        return f"Erro ao gerar resposta da IA: {str(e)}"

def avaliar_resposta_corretor(resposta):
    """Analisa a resposta do corretor e determina se foi boa, neutra ou ruim"""
    try:
        prompt = f"""
        O corretor respondeu: '{resposta}'
        Ele conseguiu vencer a objeção do cliente? Responda apenas com 'positivo', 'neutro' ou 'negativo'.
        """

        resposta_ai = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": prompt}]
        )

        return resposta_ai.choices[0].message.content.lower().strip()

    except Exception as e:
        return "neutro"

def gerar_novo_cliente():
    """Gera um novo cliente aleatório"""
    idade = random.randint(18, 50)
    ano_nascimento = datetime.date.today().year - idade
    data_nascimento = f"{random.randint(1, 28)}/{random.randint(1, 12)}/{ano_nascimento}"
    
    empreendimento = random.choice(empreendimentos_rj)

    return {
        "perfil": random.choice(list(perfis_clientes.keys())),
        "nome": random.choice(nomes_clientes),
        "sobrenome": random.choice(sobrenomes_clientes),
        "idade": idade,
        "data_nascimento": data_nascimento,
        "local": random.choice(lugares_moradia),
        "renda": random.choice(tipo_renda),
        "composicao_renda": random.choice(composicao_renda),
        "stand": empreendimento["stand"],
        "empreendimento": empreendimento["nome"],
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
