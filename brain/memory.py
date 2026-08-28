"""Memória persistente do Sirius.

Guarda duas coisas num único arquivo JSON que sobrevive a reinícios:

- ``fatos``: lista de fatos duradouros sobre a família, o ambiente e o
  próprio cachorro ("a dona se chama Cristini", "não pode subir no sofá").
- ``historico``: as últimas interações, para dar continuidade às conversas.

O arquivo fica por padrão em /opt/sirius-brain/memoria.json (configurável
via SIRIUS_MEMORIA). A escrita é atômica (grava num temporário e renomeia)
para a memória nunca corromper se faltar bateria no meio da gravação.
"""

from __future__ import annotations

import json
import os
import tempfile
import time

CAMINHO_PADRAO = os.environ.get("SIRIUS_MEMORIA", "/opt/sirius-brain/memoria.json")
MAX_HISTORICO = 40  # interações recentes mantidas por inteiro
MAX_FATOS = 200


class Memoria:
    def __init__(self, caminho: str = CAMINHO_PADRAO):
        self.caminho = caminho
        self.dados = {"fatos": [], "historico": []}
        self._carregar()

    def _carregar(self) -> None:
        try:
            with open(self.caminho, "r", encoding="utf-8") as f:
                dados = json.load(f)
            if isinstance(dados, dict):
                self.dados["fatos"] = list(dados.get("fatos", []))[:MAX_FATOS]
                self.dados["historico"] = list(dados.get("historico", []))[-MAX_HISTORICO:]
        except FileNotFoundError:
            pass
        except (json.JSONDecodeError, OSError):
            # Memória ilegível: preserva o arquivo problemático para perícia
            # e recomeça, em vez de travar o cachorro na inicialização.
            try:
                os.replace(self.caminho, self.caminho + ".corrompida")
            except OSError:
                pass

    def _salvar(self) -> None:
        pasta = os.path.dirname(self.caminho) or "."
        os.makedirs(pasta, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=pasta, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.dados, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.caminho)
        except OSError:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    # ------------------------------------------------------------------
    # Fatos duradouros

    def lembrar_fato(self, fato: str) -> None:
        fato = fato.strip()
        if fato and fato not in self.dados["fatos"]:
            self.dados["fatos"].append(fato)
            del self.dados["fatos"][:-MAX_FATOS]
            self._salvar()

    def fatos(self) -> list[str]:
        return list(self.dados["fatos"])

    # ------------------------------------------------------------------
    # Histórico de conversa

    def registrar_interacao(self, origem: str, entrada: str, resposta: str) -> None:
        self.dados["historico"].append(
            {
                "quando": time.strftime("%Y-%m-%d %H:%M:%S"),
                "origem": origem,  # "voz", "gesto" ou "voz+gesto"
                "entrada": entrada,
                "resposta": resposta,
            }
        )
        del self.dados["historico"][:-MAX_HISTORICO]
        self._salvar()

    def historico_para_conversa(self) -> list[dict]:
        """Histórico no formato de mensagens da API do Claude."""
        mensagens = []
        for item in self.dados["historico"]:
            mensagens.append({"role": "user", "content": f"[{item['origem']}] {item['entrada']}"})
            mensagens.append({"role": "assistant", "content": item["resposta"]})
        return mensagens
