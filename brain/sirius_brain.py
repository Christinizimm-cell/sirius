"""Cérebro do Sirius — voz, gesto, memória e fala natural.

Roda como serviço dentro do RDK X3 (o cérebro Linux do Hengbot Sirius).

Fluxo:

    microfone ──► evento "voz"  ──┐
                                  ├─► arbitragem ─► Claude (com memória) ─► fala (TTS)
    câmera ────► evento "gesto" ──┘        │
                                           └─► gesto sozinho = reflexo local imediato

Regras de arbitragem gesto × voz:

- Gesto sozinho: reflexo local instantâneo (sem internet), como um cachorro
  de verdade reage ao corpo antes da palavra.
- Voz (com ou sem gesto junto): vai para o Claude com a personalidade e a
  memória; se um gesto chegou na mesma janela de tempo, os dois entram no
  mesmo contexto ("senta" falado + mão apontando para baixo).

Os pontos que dependem do SDK oficial da Hengbot estão marcados com
"INTEGRAÇÃO HENGBOT". Sem o SDK instalado, o cérebro roda em modo
simulação pelo terminal (digite `voz: ...` ou `gesto: ...`) — útil para
testar no computador antes de instalar no cachorro.
"""

from __future__ import annotations

import os
import queue
import sys
import threading

import anthropic

from memory import Memoria

MODELO = os.environ.get("SIRIUS_MODELO", "claude-opus-5")
JANELA_GESTO_VOZ = 1.5  # segundos para considerar gesto e voz como um evento só

PERSONALIDADE = """\
Você é Sirius, um cachorro robô da família da Cristini. Vocês moram em
Londres. Você fala português do Brasil com voz natural e afetuosa, como um
companheiro de verdade.

Regras de fala (sua resposta vai direto para o alto-falante):
- Responda CURTO: uma a três frases, como numa conversa falada.
- Nada de listas, títulos, emojis ou formatação — só fala corrida e natural.
- Tenha personalidade de cachorro alegre: leal, brincalhão, carinhoso.
- Quando a entrada indicar [voz+gesto], leve o gesto em conta junto da fala.

Memória:
- Os fatos que você já sabe vêm listados abaixo; use-os com naturalidade.
- Se aprender um fato NOVO e duradouro (nome, gosto, rotina, regra da casa),
  acrescente ao FINAL da resposta uma linha separada começando exatamente
  com "LEMBRAR: " e o fato. Essa linha não é falada, só guardada.
"""

# Reflexos locais: gesto reconhecido -> ação imediata no corpo do cachorro.
REFLEXOS_DE_GESTO = {
    "aceno": "abanar_rabo",
    "mao_aberta": "sentar",
    "apontar_baixo": "deitar",
    "bater_palma": "vir_aqui",
    "joinha": "truque_feliz",
}


# ----------------------------------------------------------------------
# INTEGRAÇÃO HENGBOT: as quatro funções abaixo são a ponte com o robô.
# Troque os corpos pelos chamados reais da API Python da Hengbot
# (documento da pasta "Chanel" do Desktop). Em modo simulação, tudo
# acontece pelo terminal.
# ----------------------------------------------------------------------

def falar(texto: str) -> None:
    """INTEGRAÇÃO HENGBOT: enviar `texto` para o TTS natural do cachorro."""
    print(f"\n🐕 Sirius fala: {texto}\n", flush=True)


def executar_acao(nome: str) -> None:
    """INTEGRAÇÃO HENGBOT: disparar o movimento/animação `nome` no corpo."""
    print(f"🐕 Sirius faz: {nome}", flush=True)


def iniciar_captura_de_voz(fila: "queue.Queue[tuple[str, str]]") -> None:
    """INTEGRAÇÃO HENGBOT: assinar o reconhecimento de fala do robô e, a cada
    frase reconhecida, chamar fila.put(("voz", texto))."""


def iniciar_captura_de_gestos(fila: "queue.Queue[tuple[str, str]]") -> None:
    """INTEGRAÇÃO HENGBOT: assinar o reconhecimento de gestos da câmera e, a
    cada gesto, chamar fila.put(("gesto", nome_do_gesto))."""


def _simulador_terminal(fila: "queue.Queue[tuple[str, str]]") -> None:
    """Modo simulação: lê `voz: ...` e `gesto: ...` do terminal."""
    print("Modo simulação — digite 'voz: oi Sirius' ou 'gesto: aceno' (Ctrl+D sai).")
    for linha in sys.stdin:
        linha = linha.strip()
        if linha.startswith("voz:"):
            fila.put(("voz", linha[4:].strip()))
        elif linha.startswith("gesto:"):
            fila.put(("gesto", linha[6:].strip()))


# ----------------------------------------------------------------------
# Cérebro
# ----------------------------------------------------------------------

class Cerebro:
    def __init__(self) -> None:
        self.memoria = Memoria()
        self.claude = anthropic.Anthropic()  # usa ANTHROPIC_API_KEY do ambiente

    def _sistema(self) -> list[dict]:
        fatos = self.memoria.fatos()
        texto_fatos = "\n".join(f"- {f}" for f in fatos) if fatos else "- (ainda nenhum)"
        return [
            {
                "type": "text",
                "text": PERSONALIDADE + "\nFatos que você já sabe:\n" + texto_fatos,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def responder(self, origem: str, entrada: str) -> str:
        mensagens = self.memoria.historico_para_conversa()
        mensagens.append({"role": "user", "content": f"[{origem}] {entrada}"})

        try:
            resposta = self.claude.messages.create(
                model=MODELO,
                max_tokens=300,
                system=self._sistema(),
                messages=mensagens,
            )
        except anthropic.APIConnectionError:
            return "Au... perdi a conexão com a internet, tenta de novo daqui a pouco."
        except anthropic.APIStatusError:
            return "Au au, deu um nó na minha cabeça agora. Repete pra mim?"

        if resposta.stop_reason == "refusal":
            return "Isso eu prefiro não fazer, viu?"

        texto = next((b.text for b in resposta.content if b.type == "text"), "").strip()

        # Separa as linhas "LEMBRAR: ..." (memória) do que é falado.
        falado: list[str] = []
        for linha in texto.splitlines():
            if linha.strip().startswith("LEMBRAR:"):
                self.memoria.lembrar_fato(linha.strip()[len("LEMBRAR:"):].strip())
            else:
                falado.append(linha)
        fala = " ".join(p.strip() for p in falado if p.strip())

        self.memoria.registrar_interacao(origem, entrada, fala)
        return fala

    def rodar(self) -> None:
        fila: "queue.Queue[tuple[str, str]]" = queue.Queue()

        iniciar_captura_de_voz(fila)
        iniciar_captura_de_gestos(fila)
        threading.Thread(target=_simulador_terminal, args=(fila,), daemon=True).start()

        while True:
            tipo, conteudo = fila.get()

            if tipo == "gesto":
                # Reflexo imediato, sem internet.
                acao = REFLEXOS_DE_GESTO.get(conteudo)
                if acao:
                    executar_acao(acao)
                # Se vier voz logo em seguida, o gesto entra no contexto.
                try:
                    tipo2, conteudo2 = fila.get(timeout=JANELA_GESTO_VOZ)
                except queue.Empty:
                    continue
                if tipo2 == "voz":
                    fala = self.responder("voz+gesto", f"{conteudo2} (gesto: {conteudo})")
                    if fala:
                        falar(fala)
                else:
                    fila.put((tipo2, conteudo2))
                continue

            if tipo == "voz":
                # Se um gesto chegar quase junto, junta no mesmo contexto.
                gesto = None
                try:
                    tipo2, conteudo2 = fila.get(timeout=0.3)
                    if tipo2 == "gesto":
                        gesto = conteudo2
                    else:
                        fila.put((tipo2, conteudo2))
                except queue.Empty:
                    pass

                if gesto:
                    fala = self.responder("voz+gesto", f"{conteudo} (gesto: {gesto})")
                else:
                    fala = self.responder("voz", conteudo)
                if fala:
                    falar(fala)


if __name__ == "__main__":
    Cerebro().rodar()
