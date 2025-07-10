# Cue

An experimental generative art system that transforms text sentiment into abstract visual compositions.

## Overview

Cue analyzes text across multiple emotional and structural dimensions using Claude 3.5 Sonnet, then generates unique abstract art based on these sentiment scores. Each dimension influences specific visual parameters like color, texture, shape, and composition.

## Features

- **Multi-dimensional sentiment analysis**: Analyzes text across 4 dimensions (positiveness, energy, complexity, conflictness)
- **Advanced noise algorithms**: From simple gradients to reaction-diffusion patterns
- **Direct parameter mapping**: Each dimension controls specific visual aspects
- **Height map approach**: Creates depth and texture through elevation-based coloring
- **Multiple output modes**: Single images, variations, or batch processing
- **CLI interface**: Easy-to-use command-line tools

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cue.git
cd cue
```

2. Install dependencies:
```bash
pip install -e .
```

This will install console scripts so you can run commands directly (e.g., `generate`, `batch`, `test`) without needing to type `python main.py`.

3. Set up your Anthropic API key:
```bash
cp env.example .env
# Edit .env and add your API key
```

## Usage

### Basic Usage

Generate art from a text prompt:
```bash
# Using the main command
cue generate "The storm raged with unprecedented fury!"

# Or use the direct command
generate "The storm raged with unprecedented fury!"
```

### Options

- `--output, -o`: Specify output filename
- `--size, -s`: Image dimensions (default: 1920x1080)
- `--variations, -v`: Generate multiple variations
- `--show-scores, -S`: Display sentiment analysis scores
- `--all-noise`: Generate all 5 noise variations (gradient, perlin, fbm, worley, reaction) instead of a single image

### Examples

```bash
# Generate with custom size and show scores
generate "A serene morning by the lake" -s 800x600 -S

# Generate 4 variations
generate "Chaos and beauty intertwined" -v 4 -o variations/

# Generate all 5 noise variations to compare
generate "A peaceful forest at dawn" --all-noise

# Batch process from file
batch texts.txt -o batch_output/
```

### Other Commands

```bash
# Test your setup
test

# Show configuration info
info

# Browse previous output sessions
browse

# Show details of a specific session
show session_20240710_180456
```

## Output Structure

Cue automatically organizes all generated images and logs in a structured directory system:

```
output/
├── session_20240710_180456/
│   ├── art_peaceful_morning.png        # Generated image
│   ├── art_peaceful_morning_log.json   # Complete generation log
│   ├── variations_stormy_night/        # Variation subdirectory
│   │   ├── variation_01.png
│   │   ├── variation_02.png
│   │   ├── variation_03.png
│   │   └── variations_stormy_night_log.json
│   └── noise_variations_forest_dawn/   # All noise algorithms
│       ├── gradient.png
│       ├── perlin.png
│       ├── fbm.png
│       ├── worley.png
│       ├── reaction.png
│       └── noise_variations_forest_dawn_log.json
└── session_20240710_181230/
    ├── batch_output/                    # Batch processing results
    │   ├── 001_text_sample_name.png
    │   ├── 001_text_sample_name_log.json
    │   ├── 002_another_text.png
    │   └── 002_another_text_log.json
    └── batch_summary_log.json          # Batch processing summary
```

### Generation Logs

Each generation automatically creates a comprehensive log file containing:

```json
{
  "generation_info": {
    "text": "Input text that was analyzed",
    "sentiment_scores": {
      "positiveness": 0.75,
      "energy": 0.45,
      "complexity": 0.60,
      "conflictness": 0.25
    },
    "style_description": "Warm, moderate energy abstract composition...",
    "image_size": [1920, 1080],
    "output_path": "/path/to/generated/image.png",
    "all_parameters": {/* Complete parameter mapping */}
  },
  "system_info": {
    "timestamp": "2024-07-10T18:04:56.123456",
    "command": "python main.py generate 'input text' --size 1920x1080",
    "working_directory": "/path/to/cue",
    "cue_version": "1.0.0"
  }
}
```

### Session Management

- **Automatic organization**: Each run creates a timestamped session directory
- **Complete reproducibility**: All parameters and system info logged
- **Easy browsing**: Use `python main.py browse` to see all sessions
- **Detailed inspection**: Use `python main.py show <session_name>` for session details

## Sentiment Dimensions

- **Positiveness** (0.0-1.0): Color temperature from cold blues/purples to warm oranges/yellows
- **Energy** (0.0-1.0): Turbulence and chaos level from smooth flows to sharp spikes
- **Complexity** (0.0-1.0): Noise algorithm selection from simple gradients to reaction-diffusion
- **Conflictness** (0.0-1.0): Color variance from unified palette to highly mixed emotions

## Visual Mapping

### Direct Parameter Control
- **Positiveness** → Color warmth: cold blues/teals (0.0) to warm oranges/yellows (1.0)
- **Conflictness** → Color diversity: 2-color gradients (low) to 3-color spreads (high)
- **Energy** → Detail level, turbulence, and larger film-grain intensity
- **Complexity** → No longer used for algorithm selection (use `--all-noise` to generate all algorithms)

### Noise Algorithms Available
When using `--all-noise`, you'll get 4 different interpretations of the same sentiment:
- **Terrain**: Smooth, organic hills using gaussian blobs - no grid artifacts
- **Value**: Interpolated random values creating flowing patterns
- **Worley**: Cellular/crystalline patterns  
- **Gradient**: Enhanced gradient with organic terrain variation

## Architecture

```
cue/
├── main.py               # CLI interface and orchestration
├── sentiment_analyzer.py # Claude API integration
├── art_generator.py      # Generative art engine
├── noise_algorithms.py   # Collection of noise generation algorithms
├── parameter_mapper.py   # Sentiment validation and description
└── config.py            # Configuration and constants
```

## API Configuration

Get your Anthropic API key from: https://console.anthropic.com/

Create a `.env` file:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Examples

The system generates abstract, grainy compositions where:
- **Warm + Low Conflict**: Unified orange/yellow gradients with consistent tones
- **Cold + High Conflict**: Mixed blue/purple palettes with varied emotional depth
- **High Energy**: Turbulent patterns with sharp details and visible grain
- **Low Energy**: Smooth, flowing forms with subtle transitions
- **High Complexity**: Intricate cellular or reaction-diffusion patterns
- **Low Complexity**: Simple gradients or basic Perlin noise

## License

MIT License - see LICENSE file for details
