# Projeto Sirius — Cérebro do cachorro robô (Hengbot Sirius)

Kit completo para transformar o Hengbot Sirius em um cachorro com **memória
persistente**, **fala natural** (LLM + voz), e **diferenciação entre gesto e
voz** — tudo rodando dentro do próprio robô (cérebro RDK X3, Linux).

## O que tem aqui

| Pasta / arquivo | O que é |
|---|---|
| `brain/sirius_brain.py` | O cérebro: recebe eventos de voz e gesto, decide, responde falando |
| `brain/memory.py` | Memória persistente do cachorro (fatos + histórico), sobrevive a reinícios |
| `brain/config.example.env` | Chaves e configurações (copiar para `config.env` e preencher) |
| `brain/requirements.txt` | Dependências Python |
| `deploy/diagnostico.sh` | **Fase 1:** testa a corrente IA ↔ API ↔ robô elo por elo e aponta onde quebra |
| `deploy/deploy.sh` | Instala tudo no cachorro via SSH com um único comando |
| `deploy/sirius-brain.service` | Serviço systemd — o cérebro liga sozinho quando o cachorro liga |
| `docs/PESQUISA-HENGBOT-SIRIUS.md` | Tudo que foi pesquisado sobre o Hengbot Sirius, com fontes |
| `docs/API-SIRIUS-CORE.md` | **Referência oficial** Sirius Core API v4.0.0 (HTTP 8088, WS 8765, vídeo 8080) |

## Fase 1 — Descobrir onde a comunicação quebra (antes de mudar qualquer coisa)

O plano é em duas fases: primeiro **engenharia reversa** para achar o ponto
exato de falha; depois correções pontuais, uma por vez, sempre testando.
Ordem de construção: falar/entender → movimento → personalidade → memória →
visão (a visão já existe no hardware — câmera 8 MP e reconhecimento de
gestos/pessoas; não vamos criá-la, vamos aprender a acessá-la).

O que já sabemos (validado em 2026-09):

- ✅ A API do ModelArk funciona a partir do Mac: endpoint `Conciencia`
  (`ep-20260901203214-pbcr4`, modelo Dola-Seed-2.1-turbo, região Johor)
  respondeu ao teste com a chave da conta.
- ❌ O painel "Mundo Interior" do robô mostra `网络异常, 未能连上模型服务`
  ("erro de rede: não conectou ao serviço de modelo") — a falha está em
  algum elo entre **o robô** e a API, não na API em si.

Para achar o elo exato, rode no seu computador (mesma rede do cachorro):

```bash
cp brain/config.example.env brain/config.env   # só na primeira vez
# preencha ARK_API_KEY e SIRIUS_HOST no config.env
./deploy/diagnostico.sh
```

O script testa um elo por vez (seu computador → internet → API → robô →
internet do robô → API de dentro do robô), **para no primeiro que falhar**
e diz o que corrigir. Ele não instala nem altera nada no robô, e a chave
só é enviada à própria API — nunca a outro serviço.

## Como instalar no cachorro (passo a passo)

> **Importante:** este repositório foi preparado numa sessão remota do Claude
> Code (na nuvem), que **não alcança** o seu computador nem a rede onde o
> cachorro está. Para fazer a instalação ao vivo, com terminal compartilhado,
> abra o **Claude Code no seu computador** (app desktop ou `claude` no
> terminal) dentro desta pasta clonada — de lá o Claude enxerga suas pastas
> do Desktop (`Chanel`, `SSH`) e consegue conectar no cachorro via SSH.

1. No seu computador, clone este repositório e entre na branch:
   ```bash
   git clone https://github.com/christinizimm-cell/sirius.git
   cd sirius
   git checkout claude/agent-sdk-overview-w6bvr8
   ```
2. Copie `brain/config.example.env` para `brain/config.env` e preencha:
   - `ANTHROPIC_API_KEY` — a chave que está no documento da pasta **Chanel** do seu Desktop
   - `SIRIUS_HOST` — o IP do cachorro na sua rede (está nas guias da pasta **SSH**)
   - `SIRIUS_SSH_USER` — o usuário SSH do cachorro (idem)
3. Rode o instalador:
   ```bash
   ./deploy/deploy.sh
   ```
   Ele copia o cérebro para o cachorro via SSH, instala as dependências e
   registra o serviço para iniciar automaticamente.
4. Pronto: o cachorro passa a ouvir, ver gestos, lembrar e falar sozinho.
   A memória fica em `/opt/sirius-brain/memoria.json` dentro dele.

## Como funciona por dentro

- **Voz** → o texto reconhecido vai para o Claude com a personalidade e a
  memória do cachorro; a resposta curta e natural sai pela voz (TTS).
- **Gesto** → reflexo imediato e local (abanar, sentar, latir), sem esperar
  a internet — como um cachorro de verdade reage ao corpo antes da palavra.
- **Gesto + voz juntos** → os dois entram no mesmo contexto, e o cérebro
  entende a combinação ("senta" falado + mão apontando para baixo).
- **Memória** → depois de cada conversa, fatos importantes são guardados
  ("o nome da dona é Cristini", "ele gosta do tapete azul") e voltam em toda
  conversa futura, mesmo depois de desligar o cachorro.

Os pontos de encaixe com o SDK oficial da Hengbot (movimento, expressões,
voz nativa) estão marcados no código com `# INTEGRAÇÃO HENGBOT:` — são as
únicas partes que dependem da API que está na pasta Chanel do seu Desktop.
