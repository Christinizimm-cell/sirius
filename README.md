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
| `deploy/deploy.sh` | Instala tudo no cachorro via SSH com um único comando |
| `deploy/sirius-brain.service` | Serviço systemd — o cérebro liga sozinho quando o cachorro liga |
| `docs/PESQUISA-HENGBOT-SIRIUS.md` | Tudo que foi pesquisado sobre o Hengbot Sirius, com fontes |

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
