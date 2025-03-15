from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
import openai

app = Flask(__name__)

# Substitua pela sua chave da OpenAI
openai.api_key = "SUA_CHAVE_OPENAI"

@app.route("/voice", methods=["POST"])
def voice():
    """Recebe a chamada do Twilio e responde com IA."""
    user_input = request.form.get("SpeechResult", "")

    response_text = gerar_resposta_ia(user_input)

    resposta = VoiceResponse()
    resposta.say(response_text, voice="alice", language="pt-BR")

    return str(resposta)

def gerar_resposta_ia(texto_usuario):
    """Gera uma resposta simulando um cliente."""
    prompt = f"""
    Você é um cliente interessado em imóveis. O corretor disse: '{texto_usuario}'. Como você responde?
    """

    resposta = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )

    return resposta["choices"][0]["message"]["content"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    
