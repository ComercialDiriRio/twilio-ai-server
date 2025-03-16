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

@app.route("/voice", methods=["POST"])
def voice():
    """Responde chamadas de voz do Twilio"""
    user_input = request.form.get("SpeechResult", "")
    
    if not user_input:
        user_input = "Olá, estou interessado em um apartamento."

    response_text = gerar_resposta_ia(user_input)

    resposta = VoiceResponse()
    resposta.say(response_text, voice="alice", language="pt-BR")

    return str(resposta)

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    """Responde mensagens do WhatsApp"""
    user_message = request.form.get("Body", "")
    media_url = request.form.get("MediaUrl0", None)

    if media_url:  # Se for um áudio
        user_message = transcrever_audio(media_url)

    response_text = gerar_resposta_ia(user_message)

    response = MessagingResponse()
    response.message(response_text)

    return str(response)

def transcrever_audio(audio_url):
    """Baixa e transcreve áudio usando Whisper"""
    headers = {"Authorization": f"Bearer {openai.api_key}"}
    
    audio_data = requests.get(audio_url).content
    with open("audio.ogg", "wb") as f:
        f.write(audio_data)

    response = openai.Audio.transcribe("whisper-1", open("audio.ogg", "rb"))
    
    return response["text"]

def gerar_resposta_ia(texto_usuario):
    """Gera resposta da IA"""
    prompt = f"Você é um cliente interessado em imóveis. O corretor disse: '{texto_usuario}'. Como você responde?"

    resposta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )

    return resposta["choices"][0]["message"]["content"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
