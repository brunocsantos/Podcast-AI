# Game Over Cast - Podcast AI de Games

Podcast automatizado sobre games, gerado inteiramente por IA e publicado diariamente no Spotify.

## Como funciona?

1. **Coleta automática** - Puxa notícias de RSS feeds (IGN, PC Gamer, Eurogamer, The Enemy, etc.)
2. **Resumo por IA** - Claude agrupa e resume as notícias em tópicos
3. **Roteiro por IA** - Claude gera um diálogo natural entre dois apresentadores
4. **Áudio por IA** - ElevenLabs sintetiza vozes distintas para cada host
5. **Publicação automática** - Upload para S3/R2, feed RSS atualizado, Spotify busca automaticamente

## Apresentadores

- **Lucas** - Entusiasmado, adora jogos indie, faz piadas e referências a cultura pop
- **Marina** - Analítica, fã de jogos competitivos, faz perguntas provocativas

## Setup

### Requisitos

- Python 3.11+
- ffmpeg (para processamento de áudio)
- Chaves de API: [Anthropic](https://console.anthropic.com/) e [ElevenLabs](https://elevenlabs.io/)
- Storage na nuvem: AWS S3 ou [Cloudflare R2](https://www.cloudflare.com/products/r2/) (para Spotify)

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

### Configuração

Edite `config/settings.yaml`:

```yaml
podcast:
  artwork_url: "https://seu-dominio.com/podcast/artwork.jpg"  # 1400x1400+

publisher:
  storage_backend: "s3"
  base_url: "https://seu-dominio.com/podcast"
  s3_bucket: "meu-podcast-bucket"
  s3_region: "us-east-1"

scheduler:
  hour: 8
  timezone: "America/Sao_Paulo"
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

## Deploy no Cloudflare + Spotify

O projeto inclui um **Cloudflare Worker** que serve a landing page, feed RSS e episódios
a partir do **Cloudflare R2** (storage gratuito até 10GB/mês).

### 1. Criar o bucket R2

```bash
# Instale o Wrangler CLI
npm install -g wrangler

# Faça login na Cloudflare
wrangler login

# Crie o bucket R2
wrangler r2 bucket create podcast-ai
```

### 2. Configurar o projeto

Edite `config/settings.yaml`:

```yaml
publisher:
  storage_backend: "s3"
  base_url: "https://podcast-ai.<seu-subdomain>.workers.dev"
  s3_bucket: "podcast-ai"
  s3_endpoint_url: "https://<account_id>.r2.cloudflarestorage.com"
```

Edite `.env`:

```
AWS_ACCESS_KEY_ID=<R2 Access Key ID>
AWS_SECRET_ACCESS_KEY=<R2 Secret Access Key>
```

(Gere as chaves R2 em: Cloudflare Dashboard > R2 > Manage R2 API Tokens)

### 3. Deploy do Worker

```bash
# Deploy do Worker que serve os arquivos
wrangler deploy
```

O Worker fica disponível em `https://podcast-ai.<seu-subdomain>.workers.dev`

### 4. Configurar artwork

Spotify exige uma imagem de capa (1400x1400 a 3000x3000, JPEG/PNG):

```bash
# Upload manual da artwork para o R2
wrangler r2 object put podcast-ai/artwork.jpg --file=assets/artwork.jpg
```

Configure em `settings.yaml`:
```yaml
podcast:
  artwork_url: "https://podcast-ai.<seu-subdomain>.workers.dev/artwork.jpg"
```

### 5. Gerar primeiro episódio

```bash
podcast-ai run
```

Verifique o feed em: `https://podcast-ai.<seu-subdomain>.workers.dev/feed.xml`

### 6. Submeter ao Spotify

1. Acesse [Spotify for Podcasters](https://podcasters.spotify.com/)
2. Clique em "Add your podcast"
3. Cole a URL do feed: `https://podcast-ai.<seu-subdomain>.workers.dev/feed.xml`
4. Siga as instruções de verificação

O Spotify busca o feed automaticamente a cada poucas horas.

### 7. Automatizar geração diária

```bash
# Inicia o scheduler que gera um episódio novo todo dia
podcast-ai schedule
```

Para rodar como serviço em produção, use systemd, Docker, ou um servidor com cron.

## Estrutura do projeto

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
│   ├── storage.py       # Upload S3/R2
│   └── episode_tracker.py   # Histórico de episódios
├── models/              # Modelos de dados (Pydantic)
└── utils/               # Config e logging
```

## Tecnologias

| Componente | Tecnologia |
|-----------|------------|
| Roteiro | Claude API (Anthropic) |
| Vozes | ElevenLabs |
| Coleta de notícias | feedparser |
| Áudio | pydub + ffmpeg |
| Feed RSS | podgen |
| Storage | boto3 (S3/R2) |
| Agendamento | APScheduler |
| CLI | typer |
