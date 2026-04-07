# Game Over Cast - Podcast AI de Games

Podcast automatizado sobre games, gerado inteiramente por IA e publicado diariamente no Spotify.

## Como funciona?

1. **Coleta automática** - Puxa notícias de RSS feeds (IGN, PC Gamer, Eurogamer, The Enemy, etc.)
2. **Resumo por IA** - Claude agrupa e resume as notícias em tópicos
3. **Roteiro por IA** - Claude gera um diálogo natural entre dois apresentadores
4. **Áudio por IA** - ElevenLabs sintetiza vozes distintas para cada host
5. **Publicação automática** - Push para GitHub Pages, Spotify busca o feed automaticamente

## Apresentadores

- **Lucas** - Entusiasmado, adora jogos indie, faz piadas e referências a cultura pop
- **Marina** - Analítica, fã de jogos competitivos, faz perguntas provocativas

## Setup

### Requisitos

- Python 3.11+
- ffmpeg (para processamento de áudio)
- Git configurado com push access ao repositório
- Chaves de API: [Anthropic](https://console.anthropic.com/) e [ElevenLabs](https://elevenlabs.io/)

### Instalação

```bash
git clone https://github.com/brunocsantos/podcast-ai.git
cd podcast-ai

python -m venv .venv
source .venv/bin/activate

pip install -e .

cp .env.example .env
# Edite o .env com suas chaves de API
```

## Uso

### Gerar um episódio manualmente

```bash
podcast-ai run                    # Auto-incrementa número do episódio
podcast-ai run --episode-number 1 # Número específico
podcast-ai run --verbose          # Com logs detalhados
```

### Iniciar geração diária automática

```bash
# Usar horário do config (padrão: 8h Brasília)
podcast-ai schedule

# Ou especificar horário
podcast-ai schedule --hour 10 --minute 30
```

### Etapas individuais

```bash
podcast-ai collect                                        # Coletar notícias
podcast-ai script --from-file data/collected.json         # Gerar roteiro
podcast-ai audio --from-file data/scripts/ep_001.json     # Gerar áudio
podcast-ai episodes                                       # Listar episódios
```

## Publicar no Spotify (100% gratuito)

O projeto usa **GitHub Pages** para hospedar o feed RSS e os episódios.
Não precisa de cartão de crédito nem de serviço pago.

### 1. Ativar GitHub Pages

1. Vá no repositório no GitHub
2. **Settings** > **Pages**
3. Em "Source", selecione **Deploy from a branch**
4. Selecione a branch **gh-pages** e pasta **/ (root)**
5. Clique em **Save**

O site ficará disponível em: `https://brunocsantos.github.io/Podcast-AI/`

### 2. Adicionar artwork

Spotify exige uma imagem de capa (1400x1400 a 3000x3000, JPEG/PNG).
Coloque o arquivo em `assets/artwork.jpg` e configure no `settings.yaml`:

```yaml
podcast:
  artwork_url: "https://brunocsantos.github.io/Podcast-AI/artwork.jpg"
```

### 3. Gerar primeiro episódio

```bash
podcast-ai run
```

O pipeline automaticamente:
- Gera o episódio (coleta, roteiro, áudio)
- Publica na branch `gh-pages` (feed.xml + MP3)

Verifique: `https://brunocsantos.github.io/Podcast-AI/feed.xml`

### 4. Submeter ao Spotify

1. Acesse [Spotify for Podcasters](https://podcasters.spotify.com/)
2. Clique em **"Add your podcast"**
3. Cole a URL do feed: `https://brunocsantos.github.io/Podcast-AI/feed.xml`
4. Siga as instruções de verificação

O Spotify busca o feed automaticamente a cada poucas horas.

### 5. Automatizar geração diária

```bash
podcast-ai schedule
```

Para rodar como serviço permanente, use systemd, Docker, ou um servidor com cron.

## Arquitetura

```
src/podcast_ai/
├── main.py              # CLI (typer)
├── pipeline.py          # Pipeline completo de geração
├── scheduler.py         # Agendamento diário (APScheduler)
├── collector/           # Coleta de notícias (RSS)
├── scriptwriter/        # Geração de roteiro (Claude API)
│   ├── summarizer.py    # Agrupamento e resumo de artigos
│   ├── script_generator.py  # Geração de diálogo
│   └── prompts.py       # Templates de prompt
├── audio/               # Síntese de voz e montagem
│   ├── tts_engine.py    # ElevenLabs TTS
│   └── audio_assembler.py   # Concatenação com pydub
├── publisher/           # Publicação
│   ├── feed_generator.py    # Feed RSS (Spotify-compatible)
│   ├── storage.py       # Deploy via GitHub Pages
│   └── episode_tracker.py   # Histórico de episódios
├── models/              # Modelos de dados (Pydantic)
└── utils/               # Config e logging

worker/                  # Landing page do podcast
└── public/index.html
```

## Tecnologias

| Componente | Tecnologia |
|-----------|------------|
| Roteiro | Claude API (Anthropic) |
| Vozes | ElevenLabs |
| Coleta de notícias | feedparser |
| Áudio | pydub + ffmpeg |
| Feed RSS | podgen |
| Hosting | GitHub Pages (gratuito) |
| Agendamento | APScheduler |
| CLI | typer |
