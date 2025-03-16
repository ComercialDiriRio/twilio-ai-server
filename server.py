from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
import openai
import os
import requests

app = Flask(__name__)

# Configurar a API da OpenAI (Certifique-se de que a variável está no Render)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/")
def home():
    return "Servidor está rodando!"

# 📞 Rota para responder ligações de voz
@app.route("/voice", methods=["POST"])
def voice():
    """Responde chamadas de voz do Twilio"""
    try:
        user_input = request.form.get("SpeechResult", "")

        if not user_input:
            user_input = "Olá, estou interessado em um apartamento."

        response_text = gerar_resposta_ia(user_input)

        resposta = VoiceResponse()
        resposta.say(response_text, voice="alice", language="pt-BR")

        return str(resposta)

    except Exception as e:
        return f"Erro no processamento da chamada: {str(e)}"

# 💬 Rota para responder mensagens no WhatsApp
@app.route("/whatsapp", methods=["POST"])
def whatsapp():
    """Responde mensagens e áudios no WhatsApp"""
    try:
        user_message = request.form.get("Body", "")
        media_url = request.form.get("MediaUrl0", None)

        if media_url:  # Se for um áudio, tenta transcrever
            user_message = transcrever_audio(media_url)

        response_text = gerar_resposta_ia(user_message)

        response = MessagingResponse()
        response.message(response_text)

        return str(response)

    except Exception as e:
        return f"Erro ao processar mensagem do WhatsApp: {str(e)}"

# 🎙️ Função para transcrever áudios do WhatsApp
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

# 🧠 Função que gera resposta da IA simulando um cliente
def gerar_resposta_ia(texto_usuario):
    """Gera resposta para o corretor como se fosse um cliente"""
    try:
        prompt = f"""
        Você é um cliente interessado em comprar um apartamento. 
        O corretor disse: '{texto_usuario}'. Como você responde?
        """

        resposta = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "system", "content": prompt}]
        )

        return resposta.choices[0].message.content

    except Exception as e:
        return f"Erro ao gerar resposta da IA: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
