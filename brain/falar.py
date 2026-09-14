#!/usr/bin/env python3
"""Faz o Sirius FALAR uma frase, agora.

Caminho: texto -> TTS da BytePlus (a voz que vocês já contrataram)
         -> upload no robô (Core API porta 8088) -> sai no alto-falante.

Não depende do SSH nem da IA de fábrica do robô.

Uso:
    python3 brain/falar.py "Oi Cristini! Senti sua falta!"
"""
import base64
import json
import os
import sys
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def carregar_config():
    """Lê brain/config.env (formato CHAVE=valor)."""
    cfg = {}
    caminho = os.path.join(RAIZ, "brain", "config.env")
    if os.path.exists(caminho):
        for linha in open(caminho, encoding="utf-8"):
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, _, v = linha.partition("=")
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    cfg.update({k: v for k, v in os.environ.items() if k in cfg or k.startswith(("ARK_", "SIRIUS_", "BYTEPLUS_", "VOZ_"))})
    return cfg


def pedir(url, corpo, cabecalhos, timeout=60):
    dados = json.dumps(corpo).encode("utf-8")
    req = urllib.request.Request(url, data=dados, headers=cabecalhos, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def gerar_audio(texto, cfg):
    """Chama o TTS da BytePlus e devolve os bytes do áudio."""
    chave = cfg.get("BYTEPLUS_VOICE_API_KEY", "")
    if not chave:
        sys.exit(
            "Falta BYTEPLUS_VOICE_API_KEY no brain/config.env.\n"
            "É a chave de voz (x-api-key) que está na sua nota."
        )
    voz = cfg.get("VOZ_SPEAKER", "S_h2kddmXc2")
    formato = cfg.get("VOZ_FORMATO", "wav")

    bruto = pedir(
        "https://voice.ap-southeast-1.bytepluses.com/api/v3/tts/unidirectional",
        {
            "req_params": {
                "text": texto,
                "speaker": voz,
                "audio_params": {"format": formato, "sample_rate": 24000},
            }
        },
        {
            "Content-Type": "application/json",
            "x-api-key": chave,
            "X-Api-Resource-Id": cfg.get("VOZ_RESOURCE_ID", "seed-tts-2.0"),
        },
    )

    # A resposta vem em pedaços (streaming): junta todo base64 do campo "data".
    pedacos = []
    for linha in bruto.splitlines():
        linha = linha.strip()
        if linha.startswith(b"data:"):
            linha = linha[5:].strip()
        if not linha or linha == b"[DONE]":
            continue
        try:
            obj = json.loads(linha)
        except json.JSONDecodeError:
            continue
        d = obj.get("data")
        if isinstance(d, str) and d:
            pedacos.append(base64.b64decode(d))
        elif obj.get("code") not in (None, 0, 20000000):
            print(f"   aviso do TTS: {obj.get('message') or obj}", file=sys.stderr)

    if not pedacos:
        print("Resposta crua do TTS (primeiros 400 bytes):", file=sys.stderr)
        print(bruto[:400], file=sys.stderr)
        sys.exit("O TTS não devolveu áudio. Confira a chave de voz e o nome da voz (VOZ_SPEAKER).")

    return b"".join(pedacos), formato


def tocar_no_robo(audio, formato, cfg):
    """Sobe o áudio para o robô — ele toca assim que recebe."""
    ip = cfg.get("SIRIUS_HOST")
    if not ip:
        sys.exit("Falta SIRIUS_HOST no brain/config.env (o IP do cachorro).")
    resp = pedir(
        f"http://{ip}:8088/api/v1/material/upload",
        {
            "filename": f"fala.{formato}",
            "content": base64.b64encode(audio).decode("ascii"),
            "upload_only": False,
        },
        {"Content-Type": "application/json"},
        timeout=30,
    )
    return json.loads(resp.decode("utf-8"))


def main():
    texto = " ".join(sys.argv[1:]).strip()
    if not texto:
        sys.exit('Uso: python3 brain/falar.py "a frase que o Sirius vai dizer"')

    cfg = carregar_config()
    print(f'🗣️  Gerando a voz para: "{texto}"')
    audio, formato = gerar_audio(texto, cfg)
    print(f"   áudio pronto ({len(audio)/1024:.1f} KB, {formato})")

    caminho = os.path.join(RAIZ, f"ultima-fala.{formato}")
    with open(caminho, "wb") as f:
        f.write(audio)
    print(f"   cópia salva em {caminho} (dá para ouvir no Mac: afplay {caminho})")

    print("📡 Enviando para o cachorro...")
    r = tocar_no_robo(audio, formato, cfg)
    if r.get("success"):
        print("🐕 Pronto! O Sirius deve ter falado agora.")
    else:
        print(f"❌ O robô recusou: {r.get('message') or r}")


if __name__ == "__main__":
    main()
