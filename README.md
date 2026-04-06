# 🎙️ Podcast AI - Game Over Cast

Podcast automatizado sobre games, gerado inteiramente por IA.

## O que é?

O **Game Over Cast** é um podcast onde:
- As **notícias são coletadas automaticamente** de feeds RSS de sites de games
- O **roteiro é gerado por IA** (Claude) com dois apresentadores virtuais
- O **áudio é sintetizado** com vozes realistas (ElevenLabs)
- O **feed RSS é gerado automaticamente** para distribuição

## Apresentadores

- **Lucas** - Entusiasmado, adora jogos indie, faz piadas e referências a cultura pop
- **Marina** - Analítica, fã de jogos competitivos, faz perguntas provocativas

## Setup

### Requisitos

- Python 3.11+
- ffmpeg (para processamento de áudio)
- Chaves de API: [Anthropic](https://console.anthropic.com/) e [ElevenLabs](https://elevenlabs.io/)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/brunocsantos/podcast-ai.git
cd podcast-ai

# Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate

# Instale as dependências
pip install -e .

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves de API
```

## Uso

### Pipeline completo

```bash
# Gerar um episódio completo
podcast-ai run --episode-number 1

# Com logs detalhados
podcast-ai run --episode-number 1 --verbose
```

### Etapas individuais

```bash
# Apenas coletar notícias
podcast-ai collect

# Gerar roteiro a partir de notícias coletadas
podcast-ai script --from-file data/collected.json --episode-number 1

# Gerar áudio a partir de roteiro
podcast-ai audio --from-file data/scripts/ep_001.json
```

## Estrutura do projeto

```
src/podcast_ai/
├── main.py              # CLI e orquestrador do pipeline
├── collector/           # Coleta de notícias (RSS feeds)
├── scriptwriter/        # Geração de roteiro (Claude API)
├── audio/               # Síntese de voz (ElevenLabs) e montagem
├── publisher/           # Geração do feed RSS
├── models/              # Modelos de dados (Pydantic)
└── utils/               # Config e logging
```

## Configuração

Edite `config/settings.yaml` para personalizar:
- Nome do podcast e descrição
- Apresentadores e suas personalidades
- Feeds RSS de notícias
- Duração alvo dos episódios
- Configurações de áudio

## Tecnologias

- **Claude API** (Anthropic) - Geração de roteiro
- **ElevenLabs** - Text-to-Speech
- **feedparser** - Coleta de RSS
- **pydub** - Manipulação de áudio
- **podgen** - Geração de feed RSS
- **typer** - Interface CLI
