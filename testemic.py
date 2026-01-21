import speech_recognition as sr
import time

r = sr.Recognizer()
m = sr.Microphone()

print("CALIBRANDO... FIQUE EM SILÊNCIO!")
with m as source:
    r.adjust_for_ambient_noise(source)
    print(f"⚡ Nível mínimo de energia (Threshold) definido auto: {r.energy_threshold}")
    
    while True:
        print("Fale algo...")
        audio = r.listen(source)
        print("Escutei! Agora vou tentar entender...")
        try:
            # Isso aqui é só pra forçar ele a processar e você ver se pegou
            valor = r.recognize_google(audio, language="pt-BR")
            print(f"--> ENTENDI: {valor}")
        except:
            print("--> Ruído (não entendi)")