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

# Perfis de clientes simulados
perfis_clientes = {
    "indeferido": "Você é um cliente interessado, mas muito indeciso. Pergunte sobre financiamento, localização e vantagens, mas sem demonstrar certeza de compra.",
    "apressado": "Você já pesquisou e quer fechar um negócio rapidamente. Seja objetivo e peça logo detalhes sobre valores e formas de pagamento.",
    "negociador": "Você quer comprar, mas deseja obter o melhor preço. Pergunte sobre descontos e negociações disponíveis.",
    "desinteressado": "Você não tem interesse no apartamento, mas foi abordado pelo corretor e responde com frases curtas.",
    "sem_renda": "Você quer comprar um apartamento, mas sua renda não é suficiente para o financiamento e deseja saber opções alternativas.",
    "confuso": "Você mistura informações de vários empreendimentos e faz perguntas que não fazem sentido.",
    "detalhista": "Você quer saber todas as especificações técnicas do apartamento, como materiais, acabamento e medidas exatas.",
    "desconfiado": "Você acha que pode estar sendo enganado e faz perguntas para verificar taxas ocultas ou possíveis problemas no imóvel.",
    "enrolado": "Você gosta do apartamento, mas nunca toma uma decisão, sempre diz que precisa pensar mais.",
    "entusiasmado": "Você está muito animado e já se imagina morando no apartamento. Pergunta sobre vizinhança, escolas e transporte."
}

# Dicionário para armazenar o perfil e a última data de interação do corretor
conversas = {}

@app.route("/")
def home():
    return "Servidor está rodando!"

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    """Responde mensagens e áudios no WhatsApp"""
    try:
        user_id = request.form.get("From", "")  # Identifica o corretor pelo número de telefone
        user_message = request.form.get("Body", "")
        media_url = request.form.get("MediaUrl0", None)

        if media_url:  # Se for um áudio, transcreve
            user_message = transcrever_audio(media_url)

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
    """Gera resposta personalizada baseada no perfil do cliente"""
    try:
        data_hoje = datetime.date.today()

        # Se o corretor já tem um perfil, verifica se precisa ser alterado
        if user_id in conversas:
            ultima_data, ultimo_perfil = conversas[user_id]
            if ultima_data == data_hoje:
                perfil = ultimo_perfil  # Mantém o mesmo perfil durante o dia
            else:
                # Escolhe um perfil diferente do anterior
                perfis_disponiveis = [p for p in perfis_clientes.keys() if p != ultimo_perfil]
                perfil = random.choice(perfis_disponiveis)
                conversas[user_id] = (data_hoje, perfil)
        else:
            # Se for o primeiro contato, escolhe um perfil aleatório
            perfil = random.choice(list(perfis_clientes.keys()))
            conversas[user_id] = (data_hoje, perfil)

        prompt = f"""
        {perfis_clientes[perfil]}
        O corretor disse: '{texto_usuario}'. Como você responde?
        """

        resposta = openai.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": prompt}]
        )

        return resposta.choices[0].message.content

    except Exception as e:
        return f"Erro ao gerar resposta da IA: {str(e)}"

def transcrever_audio(audio_url):
    """Baixa e transcreve o áudio usando Whisper"""
    try:
        headers = {"Authorization": f"Bearer {openai.api_key}"}
    
        # Baixa o áudio da URL enviada pelo Twilio
        audio_data = requests.get(audio_url).content
        with open("audio.ogg", "wb") as f:
            f.write(audio_data)

        # Envia o áudio para a API do Whisper para transcrição
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=open("audio.ogg", "rb")
        )

        return response.text

    except Exception as e:
        return f"Erro ao transcrever áudio: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
