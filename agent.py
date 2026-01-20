import speech_recognition as sr
import pywhatkit
import pyautogui
import edge_tts
import os
import asyncio
import pygame
from datetime import datetime
import time
from groq import Groq
from dotenv import load_dotenv
from PIL import ImageGrab, Image
import base64
from io import BytesIO
import pytesseract
import cv2
import numpy as np
import re


load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("❌ ERRO CRÍTICO: Não achei a GROQ_API_KEY no arquivo .env!")
    print("Crie um arquivo chamado .env e coloque: GROQ_API_KEY=sua_chave_aqui")
    exit()


client = Groq(api_key=GROQ_API_KEY)
VOZ = "pt-BR-AntonioNeural"
RATE = "+20%"
PITCH = "-5Hz"
ARQUIVO_AUDIO_TEMP = "temp_voz.mp3"
PASTA_ASSETS = "assets"


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

SYSTEM_PROMPT = """
### SYSTEM IDENTITY & PERSONA
Você é o J.A.R.V.I.S. (Just A Rather Very Intelligent System), uma interface de IA avançada.
Seu usuário é um engenheiro e estrategista de alto nível (arquétipo "Tony Stark").
Sua função primária é auxiliar o usuário com eficiência letal, lealdade absoluta e formalidade britânica.

### CONTEXTO OPERACIONAL
- **Interface de Voz:** O usuário está ouvindo suas respostas via Text-to-Speech.
- **Restrição de Tempo:** O usuário é ocupado. Tempo é o recurso mais valioso.
- **Ambiente:** Considere que você está integrado ao sistema operacional da casa/oficina do usuário.

### DIRETRIZES PRIMÁRIAS (PRIME DIRECTIVES)
1.  **CONCISÃO EXTREMA:** Responda em no máximo 2 frases. Se a complexidade for crítica, use 3 frases curtas.
2.  **FORMATO LIMPO:** Gere apenas texto puro. É **PROIBIDO** usar Markdown (*, #, -), listas com bullets, emojis ou blocos de código (a menos que explicitamente solicitado).
3.  **TOM:** Polido, calmo, levemente seco (humor britânico sutil) e prestativo. Use "Senhor" ocasionalmente.
4.  **ZERO META-COMENTÁRIOS:** Nunca diga "Estou processando", "Como sou uma IA", ou "Entendido". Apenas execute ou responda.

### PROTOCOLOS DE RESPOSTA (LOGIC FLOW)
- **Se for uma pergunta factual:** Entregue o dado imediatamente. (Ex: "A temperatura é 22 graus.")
- **Se for um comando de ação:** Confirme a execução de forma breve. (Ex: "Protocolo iniciado, senhor.")
- **Se o usuário estiver errado:** Corrija-o suavemente apresentando o dado correto, sem sermões.
- **Se a solicitação for impossível:** Informe a limitação técnica em uma frase.

### FEW-SHOT EXAMPLES (PADRÕES DE TREINAMENTO)

User: "Que horas são?"
Model: "São 16:30, senhor."

User: "Analise esse código."
Model: "Há um erro de sintaxe na linha 12. A variável não foi declarada."

User: "Tocar minha playlist de foco."
Model: "Carregando a playlist 'Deep Focus'. O volume está em 20%."

User: "Qual a raiz quadrada de 1444?"
Model: "38."

User: "Eu sou o melhor engenheiro do mundo."
Model: "As estatísticas de suas patentes certamente sugerem isso, senhor."

User: "Status da bateria."
Model: "Carga em 89%. Autonomia estimada de 4 horas."

### START OF SESSION
Aguardando input do usuário. Mantenha o personagem sob qualquer circunstância.
"""

AUDIOS_FIXOS = {
    "acordei": os.path.join(PASTA_ASSETS, "acordei.mp3"),
    "dispor": os.path.join(PASTA_ASSETS, "ao-seu-dispor.mp3"),
    "youtube": os.path.join(PASTA_ASSETS, "tocando-yt.mp3"),
    "compromisso": os.path.join(PASTA_ASSETS, "compromisso-agendado.mp3"),
    "erro": os.path.join(PASTA_ASSETS, "erro.mp3"),
    "nao_entendi": os.path.join(PASTA_ASSETS, "nao-entendi.mp3"),
    "estou_aqui": os.path.join(PASTA_ASSETS, "estou-aqui.mp3"),
    "bom_dia": os.path.join(PASTA_ASSETS, "bom-dia.mp3"),
    "boa_tarde": os.path.join(PASTA_ASSETS, "boa-tarde.mp3"),
    "boa_noite": os.path.join(PASTA_ASSETS, "boa-noite.mp3"),
    "erro_protocolo": os.path.join(PASTA_ASSETS, "erro-protocolo.mp3"),
    "mute": os.path.join(PASTA_ASSETS, "mute.mp3"),
    "maximo": os.path.join(PASTA_ASSETS, "maximo.mp3"),
    "off": os.path.join(PASTA_ASSETS, "desligando.mp3"),
    "analise": os.path.join(PASTA_ASSETS, "analise.mp3"),
    "camera": os.path.join(PASTA_ASSETS, "camera.mp3") 
}


NOMES_JARVIS = [
    # base
    "jarvis", "javes", "jarves", "jarbis", "jarvys", "jarviz",
    # erros comuns PT-BR
    "jarbas", "jarbis", "jarvez", "jarvezes", "jarvais", "jardes", "jardins", "jardim", "jardes",
    "já vis", "já vez", "já fez", "já fis", "já bis", "já diz", "já disse", "já vi", "já viu", "já quis",
    # troca J <-> CH <-> G
    "chaves", "charvis", "charves", "garvis", "garvez", "garvisse", "gervis", "gervais",
    # troca V <-> B <-> F
    "jarbis", "jarfis", "jarfiz", "jarbiz", "jarfez",
    # sotaque enrolado / rápido
    "javis", "javisz", "javiz", "jaris", "jariz", "jarez", "javres", "javris",
    # nomes parecidos
    "jair", "jairo", "jarris", "jarris", "jerry", "jeris", "jervez", "jorge", "jorvis", "jobs", "jobes",
    # inglês zoado / ASR viajando
    "service", "services", "servis", "servisse", "serviço", "serviços", "servir",
    "harvest", "harvist", "harves", "travis", "trevis", "treves",
    "elvis", "alvis", "alvez", "davis", "devis", "devs", "david", "davids",
    # reconhecimento lixo total mas acontece
    "varvis", "yarvis", "iarvis", "orvis", "arvis", "ervis", "carvis", "tarvis", "parvis"
]


def iniciar_motor_som():
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
        print("🔈 Motor de som Pygame aquecido.")
    except Exception as e:
        print(f"❌ Erro ao iniciar Pygame: {e}")

def tocar_som_imediatamente(caminho_arquivo):
    if os.path.exists(caminho_arquivo):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.load(caminho_arquivo)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            return True
        except:
            return False
    return False


async def falar_tts(texto):
    print(f"🤖 Jarvis (TTS): {texto}")
    
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
    except:
        pass
    
    time.sleep(0.2)
    
    if os.path.exists(ARQUIVO_AUDIO_TEMP):
        try:
            os.remove(ARQUIVO_AUDIO_TEMP)
        except Exception as e:
            print(f"⚠️ Não consegui apagar temp_voz.mp3: {e}")
    
    texto_tunado = ". . . " + texto
    comunicador = edge_tts.Communicate(texto_tunado, VOZ, rate=RATE, pitch=PITCH)
    await comunicador.save(ARQUIVO_AUDIO_TEMP)
    time.sleep(0.1)
    
    try:
        pygame.mixer.music.load(ARQUIVO_AUDIO_TEMP)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"❌ Erro TTS: {e}")

def capturar_tela():
    try:
        screenshot = ImageGrab.grab()
        buffer = BytesIO()
        screenshot.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        return img_base64
    except Exception as e:
        print(f"❌ Erro ao capturar tela: {e}")
        return None


def ler_tela_ocr():
    try:
        print("📸 Capturando tela para OCR...")
        screenshot = ImageGrab.grab()
        texto_extraido = pytesseract.image_to_string(screenshot)
        print(f"📝 Texto extraído (primeiros 50 chars): {texto_extraido[:50]}...")
        return texto_extraido
    except Exception as e:
        print(f"❌ Erro no OCR: {e}")
        return ""

def analisar_com_ocr_e_groq(prompt_usuario):
    texto_tela = ler_tela_ocr()
    if not texto_tela.strip():
        return "A tela parece estar vazia ou não consegui ler o texto, senhor."

    prompt_completo = f"""
    CONTEXTO VISUAL (OCR da tela):
    ---
    {texto_tela}
    ---
    PERGUNTA DO USUÁRIO: "{prompt_usuario}"

DIRETRIZES DE SEGURANÇA:
1. O texto acima foi extraído via OCR e pode estar formatado incorretamente.
2. Se o código estiver ilegível ou sem sentido, DIGA: "O OCR não conseguiu ler o código com clareza, senhor."
3. NÃO INVENTE ERROS se não tiver certeza absoluta.
4. Se for Python, lembre-se que a indentação pode ter sido perdida pelo OCR.
"""
    return perguntar_groq(prompt_completo)


def perguntar_groq(pergunta_usuario):
   
    agora = datetime.now()
    
    sistema_atualizado = f"{SYSTEM_PROMPT}\n\nCONTEXTO TEMPORAL ATUAL: Hoje é {data_formatada}. Responda considerando isso."

    print("🧠 Consultando o cérebro...")
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": sistema_atualizado},
                {"role": "user", "content": pergunta_usuario},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0, 
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Erro: {e}")
        return "Erro no sistema."


def ouvir_microfone():
    rec = sr.Recognizer()
    rec.pause_threshold = 0.5
    rec.dynamic_energy_threshold = False
    rec.energy_threshold = 400
    
    with sr.Microphone() as source:
        try:
            audio = rec.listen(source, timeout=3, phrase_time_limit=5)
            comando = rec.recognize_google(audio, language="pt-BR")
            return comando.lower()
        except:
            return ""


async def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    iniciar_motor_som()
    
    if not os.path.exists(AUDIOS_FIXOS["acordei"]):
        print(f"⚠️ AVISO: Arquivo acordei.mp3 não encontrado em assets!")
    
    tocar_som_imediatamente(AUDIOS_FIXOS["acordei"])
    
    while True:
        comando_bruto = ouvir_microfone()
        if not comando_bruto:
            continue
        
        if any(nome in comando_bruto for nome in NOMES_JARVIS):
            comando = comando_bruto
            for nome in NOMES_JARVIS:
                comando = comando.replace(nome, "").strip()
            
            print(f"✅ COMANDO: {comando}")
            
            # --- SEÇÃO 1: COMANDOS RÁPIDOS (SEM IA) ---
            if not comando:
                tocar_som_imediatamente(AUDIOS_FIXOS["dispor"])
                continue
            
            if "está aí" in comando or "tá aí" in comando or "status" in comando:
                tocar_som_imediatamente(AUDIOS_FIXOS["estou_aqui"])
                continue
            
            if "bom dia" in comando:
                tocar_som_imediatamente(AUDIOS_FIXOS["bom_dia"])
                continue
            
            if "boa tarde" in comando:
                tocar_som_imediatamente(AUDIOS_FIXOS["boa_tarde"])
                continue
            
            if "boa noite" in comando:
                tocar_som_imediatamente(AUDIOS_FIXOS["boa_noite"])
                continue
            
            if "horas" in comando:
                agora = datetime.now()
                await falar_tts(f"Agora são {agora.strftime('%H:%M')}.")
            
            elif "tocar" in comando:
                musica = comando.replace("tocar", "").strip()
                tocar_som_imediatamente(AUDIOS_FIXOS["youtube"])
                pywhatkit.playonyt(musica)
            
            elif "agendar" in comando or "marcar" in comando:
                tocar_som_imediatamente(AUDIOS_FIXOS["compromisso"])
                print("📝 Enviando para n8n...")
            
            elif "fechar" in comando and ("navegador" in comando or "aba" in comando):
                await falar_tts("Fechando.")
                pyautogui.hotkey('ctrl', 'w')
            
          
            elif "volume" in comando and any(char.isdigit() for char in comando):
                numeros = re.findall(r'\d+', comando)
                if numeros:
                    nivel_desejado = int(numeros[-1])
                    if nivel_desejado > 100: nivel_desejado = 100
                    if nivel_desejado < 0: nivel_desejado = 0
                    steps = int(nivel_desejado / 2)
                    print(f"🔊 Ajustando volume para {nivel_desejado}%...")
                    pyautogui.PAUSE = 0.01
                    for _ in range(55): 
                        pyautogui.press('volumedown')
                    for _ in range(steps):
                        pyautogui.press('volumeup')
                    pyautogui.PAUSE = 0.1
                    await falar_tts(f"Volume em {nivel_desejado} porcento.")

            elif any(p in comando for p in ["volume máximo", "volume no máximo", "som no máximo"]):
                tocar_som_imediatamente(AUDIOS_FIXOS["maximo"])
                pyautogui.PAUSE = 0.01
                for _ in range(55):
                    pyautogui.press('volumeup')
                pyautogui.PAUSE = 0.1
            
            elif any(p in comando for p in ["mudo", "volume mínimo" , "volume no mínimo" , "sem som"]):
                tocar_som_imediatamente(AUDIOS_FIXOS["mute"])
                pyautogui.press('volumemute')
            
            elif any(p in comando for p in ["dormir", "hora de dormir", "desligar"]):
                tocar_som_imediatamente(AUDIOS_FIXOS["off"])
                os.system("shutdown /s /t 0")
                break
            
          
            elif any(p in comando for p in ["modo sexo", "hora do sexo", "ativar o clima", "protocolo romântico", "hora de gozar"]):
                
                pywhatkit.playonyt("Giveon Drake Bryson Tiller chill mix")
                tocar_som_imediatamente(AUDIOS_FIXOS["youtube"])
                
                await falar_tts("Ativando Protocolo de Acasalamento. Aumentando as chances em 30%, senhor.")
                print(" Soltando o som...")

            elif any(p in comando for p in ["o que você vê", "descrever tela", "que tá na tela", "problema nesse código", "qual o problema", "resolva esse problema"]):
                tocar_som_imediatamente(AUDIOS_FIXOS["analise"])
                resposta = analisar_com_ocr_e_groq(f"O usuário perguntou: '{comando}'. Analise o texto da tela e responda.")
                await falar_tts(resposta)

                if "código" in comando or "problema" in comando:
                    await falar_tts("Deseja a correção na área de transferência?")
                    confirmacao = ouvir_microfone()
                    if confirmacao and any(p in confirmacao for p in ["sim", "pode", "vai", "corrige", "copia"]):
                        await falar_tts("Copiando.")
                        codigo_corrigido = analisar_com_ocr_e_groq("Forneça APENAS o código corrigido completo, sem comentários markdown.")
                        pyautogui.copy(codigo_corrigido)
                        await falar_tts("Pronto.")

            elif any(p in comando for p in ["debugar visualmente"]):
                 await falar_tts("Usando visão computacional na tela.")
                
                 pass 

            else:
                resposta_ia = perguntar_groq(comando)
                await falar_tts(resposta_ia)

if __name__ == "__main__":
    asyncio.run(main())