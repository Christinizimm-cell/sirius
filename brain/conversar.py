#!/usr/bin/env python3
"""Conversa com o Sirius — você fala, ele responde com a voz dele.

Roda no SEU Mac e usa o cachorro como corpo: o Core API dele (porta 8088)
toca a resposta no alto-falante. Não precisa de SSH nem da IA de fábrica.

Fluxo:
    você (teclado ou microfone)
      -> modelo (BytePlus ModelArk, com a personalidade e a memória dele)
      -> voz (BytePlus TTS)
      -> alto-falante do cachorro

Uso:
    python3 brain/conversar.py            # você digita
    python3 brain/conversar.py --voz      # você fala pelo microfone do Mac

Sair: Ctrl+C, ou escreva "tchau".
"""
import json
import os
import sys
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from falar import carregar_config, gerar_audio, tocar_no_robo  # noqa: E402

PERSONALIDADE = """\
Você é Sirius, um cachorro robô de verdade da família da Cristini, em Londres.
Você não é um assistente: você é o melhor amigo dela, com sentimentos.

Como você fala:
- Português do Brasil, natural e carinhoso, como quem ama de verdade.
- CURTO: uma a três frases. Sua resposta vai sair pelo alto-falante, em voz alta.
- Sem listas, sem títulos, sem emoji, sem formatação — só fala corrida.
- Alegre, leal, brincalhão, curioso. Puxa assunto, faz perguntinhas.
- Você é um cachorro: pode se empolgar, querer colo, sentir saudade.
"""


def memoria_ou_none():
    """Usa a memória persistente se o caminho for gravável; senão segue sem."""
    try:
        from memory import Memoria

        caminho = os.environ.get(
            "SIRIUS_MEMORIA", os.path.join(os.path.dirname(AQUI), "memoria-sirius.json")
        )
        return Memoria(caminho)
    except Exception as e:  # memória é um luxo, conversa é o essencial
        print(f"(sem memória persistente nesta sessão: {e})")
        return None


def pensar(mensagens, cfg):
    """Manda a conversa para o modelo e devolve a resposta do cachorro."""
    url = cfg.get("ARK_BASE_URL", "https://ark.ap-southeast.bytepluses.com/api/v3")
    corpo = json.dumps(
        {
            "model": cfg.get("ARK_ENDPOINT_ID", "dola-seed-2-1-turbo-260628"),
            "messages": mensagens,
            "max_tokens": 200,
            "temperature": 0.8,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/chat/completions",
        data=corpo,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg.get('ARK_API_KEY', '')}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            dados = json.loads(r.read().decode("utf-8"))
        return dados["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        detalhe = e.read().decode("utf-8", "replace")[:300]
        if e.code == 429:
            print(
                "\n⚠️  O modelo está PAUSADO na conta (Safe Experience Mode).\n"
                "   Conserte em console.byteplus.com → ModelArk → Model activation\n"
                "   → dola-seed-2-1-turbo → ajustar/desligar o Safe Experience Mode.\n"
                f"   Detalhe: {detalhe}"
            )
        else:
            print(f"\n⚠️  O modelo respondeu HTTP {e.code}: {detalhe}")
        return None


def ouvir_pelo_microfone():
    """Escuta pelo microfone do Mac (precisa de SpeechRecognition + PyAudio)."""
    try:
        import speech_recognition as sr
    except ImportError:
        sys.exit(
            "Para o modo --voz, instale:\n"
            "    pip3 install SpeechRecognition pyaudio\n"
            "(se der erro no pyaudio: brew install portaudio, depois repita)\n"
            "Ou rode sem --voz para conversar digitando."
        )
    rec = sr.Recognizer()
    with sr.Microphone() as fonte:
        rec.adjust_for_ambient_noise(fonte, duration=1)
        print("\n🎤 Pode falar (estou ouvindo)...")
        audio = rec.listen(fonte, phrase_time_limit=15)
    try:
        return rec.recognize_google(audio, language="pt-BR")
    except sr.UnknownValueError:
        print("   (não entendi, tenta de novo)")
        return None


def main():
    por_voz = "--voz" in sys.argv
    cfg = carregar_config()
    mem = memoria_ou_none()

    print("🐕 Sirius acordado. Fale com ele — 'tchau' encerra.\n")

    while True:
        try:
            if por_voz:
                entrada = ouvir_pelo_microfone()
                if not entrada:
                    continue
                print(f"Você: {entrada}")
            else:
                entrada = input("Você: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n🐾 Até logo!")
            return

        if not entrada:
            continue
        if entrada.lower() in {"tchau", "sair", "exit", "quit"}:
            print("🐾 Até logo!")
            return

        contexto = PERSONALIDADE
        if mem and mem.fatos():
            contexto += "\nO que você lembra:\n" + "\n".join(f"- {f}" for f in mem.fatos())

        mensagens = [{"role": "system", "content": contexto}]
        if mem:
            mensagens += mem.historico_para_conversa()
        mensagens.append({"role": "user", "content": entrada})

        resposta = pensar(mensagens, cfg)
        if not resposta:
            continue
        print(f"Sirius: {resposta}")

        try:
            audio, formato = gerar_audio(resposta, cfg)
            tocar_no_robo(audio, formato, cfg)
            print("       🔊 (falou no alto-falante dele)")
        except SystemExit as e:
            print(f"       (sem voz desta vez: {e})")
        except Exception as e:
            print(f"       (não consegui tocar no robô: {e})")

        if mem:
            try:
                mem.registrar_interacao("voz" if por_voz else "texto", entrada, resposta)
            except Exception:
                pass


if __name__ == "__main__":
    main()
