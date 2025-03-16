from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
import openai
import os
import requests

app = Flask(__name__)

# Configurar a API da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def home():
    return "Servidor está rodando!"

# 📞 Rota para responder ligações de voz
@app.route("/voice", methods=["POST"])
def voice():
    """Responde chamadas de voz do Twilio"""
    
    # Captura o que foi dito pelo corretor
    user_input = request.form.get("SpeechResult", "")

    if not user_input:
        user_input = "Olá, estou interessado em um apartamento."

    # Gera resposta da IA
    response_text = gerar_resposta_ia(user_input)

    # Responde com áudio para o Twilio
    resposta = VoiceResponse()
    resposta.say(response_text, voice="alice", language="pt-BR")

    return str(resposta)

# 💬 Rota para responder mensagens no WhatsApp
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    """Responde mensagens e áudios no WhatsApp"""

    # Captura mensagem ou áudio enviado pelo corretor
    user_message = request.form.get("Body", "")
    media_url = request.form.get("MediaUrl0", None)

    if media_url:  # Se for um áudio, transcreve
        user_message = transcrever_audio(media_url)

    # Gera resposta da IA
    response_text = gerar_resposta_ia(user_message)

    # Envia a resposta de volta ao WhatsApp
    response = MessagingResponse()
    response.message(response_text)

    return str(response)

# 🎙️ Função para transcrever áudios do WhatsApp
def transcrever_audio(audio_url):
    """Baixa e transcreve o áudio usando Whisper"""
    
    headers = {"Authorization": f"Bearer {openai.api_key}"}
    
    # Baixa o áudio da URL enviada pelo Twilio
    audio_data = requests.get(audio_url).content
    with open("audio.ogg", "wb") as f:
        f.write(audio_data)

    # Envia o áudio para a API do Whisper para transcrição
    response = openai.Audio.transcribe("whisper-1", open("audio.ogg", "rb"))

    return response["text"]

# 🧠 Função que gera resposta da IA simulando um cliente
def gerar_resposta_ia(texto_usuario):
    """Gera resposta para o corretor como se fosse um cliente"""
    
    prompt = f"""
    Você é um cliente interessado em comprar um apartamento. 
    O corretor disse: '{texto_usuario}'. Como você responde?
    """

    resposta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )

    return resposta["choices"][0]["message"]["content"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
