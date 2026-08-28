# Pesquisa — Hengbot Sirius (o cachorro)

Resumo do que existe publicado na internet sobre o Hengbot Sirius, para
orientar a integração. (Lido e conferido; fontes no final.)

## O que é

O Hengbot Sirius é um cachorro robô treinável com IA, lançado em 2025 via
Kickstarter, voltado a consumidores e desenvolvedores.

## Hardware

- **Cérebro:** placa D-Robotics **RDK X3** rodando Linux, com acelerador de
  IA de **5 TOPS** — é nela que o nosso cérebro Python roda.
- **Articulações:** juntas proprietárias Hengbot Neurocore™, **14 graus de
  liberdade** — pula, estica, dança com movimento realista.
- **Sensores:** câmera de **8 MP**, par de microfones (dual-mic array),
  alto-falante.
- **Expansão:** USB-C para periféricos e desenvolvimento avançado.

## Software e APIs

- **APIs em C e Python** para desenvolvimento próprio.
- **Sirius Creator Studio / Creator Studio Pro** — programação visual
  (arrastar e soltar), pacotes de voz, personalidades trocáveis, expressões
  faciais customizadas. A edição **EDU** dá licença de desenvolvedor,
  suporte técnico direto e acesso ao Creator Studio Pro Masterpiece.
- **Acesso SSH** disponível — dá para entrar no Linux do cachorro e instalar
  o próprio modelo de linguagem, reconhecimento de fala local, web apps etc.
- **IA embarcada:** reconhecimento de voz, processamento de linguagem
  natural (LLM), visão computacional e **reconhecimento de gestos** — o
  robô entende e responde a gestos humanos, e dá para sincronizar gestos
  com comandos de voz.

## O painel AI Studio

O painel web (ex.: `http://<host>:8082/ai-studio`) é a interface de estúdio
de IA do Sirius. Ele não é alcançável a partir de ambientes de nuvem com
rede restrita — precisa ser acessado de um computador na mesma rede do
cachorro (ou com rota até o host do painel).

## Consequências para o nosso projeto

1. O cérebro deste repositório roda **dentro do RDK X3** (Linux + Python).
2. A ponte com movimento/expressões usa a **API Python da Hengbot** — o
   documento da API está na pasta *Chanel* do Desktop da Cristini e é a
   referência definitiva para os pontos `# INTEGRAÇÃO HENGBOT:` no código.
3. As credenciais e o IP para SSH estão nas guias da pasta *SSH* do Desktop.

## Fontes

- [CNX Software — Hengbot Sirius is a trainable AI robotic dog](https://www.cnx-software.com/2025/08/04/hengbot-sirius-is-a-trainable-ai-robotic-dog-for-consumers-and-developers/)
- [D-Robotics — Hengbot launches Sirius with RDK X3 as its brain](https://en.d-robotics.cc/blog/hengbot-launches-sirius-on-kickstarter-a-programmable-robotic-dog-with-d-robotics-rdk-x3-as-its-brain-for-consumers)
- [Kickstarter — Sirius, the world's most dynamic robotic dog](https://www.kickstarter.com/projects/hengbot/sirius-the-worlds-most-dynamic-robotic-dog-for-endless-fun)
- [Site oficial Hengbot](https://hengbot.com/)
- [PR Newswire — Hengbot launches Sirius](https://www.prnewswire.com/news-releases/hengbot-launches-sirius-an-ai-based-programmable-and-customizable-robotic-dog-for-consumers-302487927.html)
- [Yanko Design — Hengbot's AI LLM-powered open-source robot dog](https://www.yankodesign.com/2025/07/12/hengbots-ai-llm-powered-open-source-robot-dog-is-cheaper-than-an-iphone/)
- [Mia — Hengbot Sirius review](https://mia-cat.com/en/pet-robot/hengbot-sirius-review/)
