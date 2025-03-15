from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import openai
import os
import requests

app = Flask(__name__)

# Configurar a API da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    """Recebe mensagens do WhatsApp e responde com IA."""

    # Obtém o tipo de mensagem (texto ou áudio)
    user_message = request.form.get("Body", "")
    media_url = request.form.get("MediaUrl0", None)

    if media_url:  # Se for um áudio
        user_message = transcrever_audio(media_url)

    # Gera resposta da IA
    response_text = gerar_resposta_ia(user_message)

    # Envia a resposta de volta ao WhatsApp
    response = MessagingResponse()
    response.message(response_text)

    return str(response)

def transcrever_audio(audio_url):
    """Baixa e transcreve o áudio usando Whisper."""
    
    headers = {"Authorization": f"Bearer {openai.api_key}"}
    
    # Baixar o áudio do link
    audio_data = requests.get(audio_url).content
    with open("audio.ogg", "wb") as f:
        f.write(audio_data)

    # Enviar para a API do Whisper
    response = openai.Audio.transcribe("whisper-1", open("audio.ogg", "rb"))

    return response["text"]

def gerar_resposta_ia(texto_usuario):
    """Gera resposta simulando um cliente interessado em imóveis."""
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
    app.run(host="0.0.0.0", port=10000)
