# YouTube Transcript Summarizer

A CLI tool that downloads YouTube video transcripts and generates summaries using the OpenRouter API.

## Features

- Download transcripts from YouTube videos
- Generate comprehensive summaries using LLMs via OpenRouter
- Save summaries as Markdown files
- Support for different OpenRouter models
- Progress indicators and error handling

## Installation

### Option 1: Install from source

1. Clone this repository:
   ```
   git clone https://github.com/madmanden/yt-summarizer.git
   cd yt-summarizer
   ```

2. Install the package:
   ```
   pip install -e .
   ```

### Option 2: Install via pip (once published)

```
pip install yt-summarizer
```

## Configuration

Create a `.env` file with your OpenRouter API key:
```
cp .env.example .env
```
Then edit the `.env` file to add your API key:
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini
```

## Usage

```
yt-summarize [VIDEO_URL_OR_ID] [OPTIONS]
```

### Arguments

- `VIDEO_URL_OR_ID`: YouTube video URL or ID (required)

### Options

- `-o, --output`: Output directory for the summary file (defaults to "summaries")
- `-m, --model`: OpenRouter model to use (defaults to value in .env)
- `-k, --api-key`: OpenRouter API key (can be used instead of .env file)
- `-h, --help`: Show help message

### Examples

```bash
# Summarize a video using the default model
yt-summarize "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Specify an output directory
yt-summarize dQw4w9WgXcQ -o my-summaries/

# Use a specific model
yt-summarize https://youtu.be/dQw4w9WgXcQ -m anthropic/claude-3-opus-20240229

# Provide API key directly
yt-summarize https://youtu.be/dQw4w9WgXcQ -k your_api_key_here
```

## Supported Models

You can use any model available on OpenRouter. Some recommendations:

- `openai/gpt-4o-mini` (default)
- `anthropic/claude-3-haiku-20240307` (fast, economical)
- `anthropic/claude-3-sonnet-20240229` (balanced)
- `anthropic/claude-3-opus-20240229` (highest quality)

## Error Handling

The tool handles various errors:
- Invalid YouTube URLs
- Videos without transcripts
- API failures
- Network issues

## License

MIT