"""Cue - Experimental generative art using sentiment analysis."""

import argparse
import os
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
import sys

from sentiment_analyzer import SentimentAnalyzer
from art_generator import ArtGenerator
from parameter_mapper import ParameterMapper
from config import DEFAULT_IMAGE_SIZE


def create_output_structure() -> Path:
    """Create output directory structure and return the session directory."""
    base_dir = Path("output")
    base_dir.mkdir(exist_ok=True)
    
    # Create timestamped session directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = base_dir / f"session_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    return session_dir


def save_generation_log(session_dir: Path, filename_prefix: str, **log_data) -> Path:
    """Save comprehensive generation log."""
    log_file = session_dir / f"{filename_prefix}_log.json"
    
    # Add system info and command
    full_log = {
        "generation_info": log_data,
        "system_info": {
            "timestamp": datetime.now().isoformat(),
            "command": " ".join(sys.argv),
            "working_directory": str(Path.cwd()),
            "cue_version": "1.0.0"
        }
    }
    
    with open(log_file, 'w') as f:
        json.dump(full_log, f, indent=2, ensure_ascii=False)
    
    return log_file


def parse_size(size_str: str) -> tuple[int, int]:
    """Parse size string like '1920x1080' into (width, height)."""
    try:
        width, height = map(int, size_str.split('x'))
        return width, height
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid size format '{size_str}'. Use WIDTHxHEIGHT (e.g., 1920x1080)")


def generate_cmd(args):
    """Generate art from text sentiment analysis."""
    # Parse size
    image_size = parse_size(args.size)
    
    # Create output structure
    session_dir = create_output_structure()
    print(f"Output session: {session_dir}")
    
    # Initialize components
    print("Initializing Cue...")
    try:
        analyzer = SentimentAnalyzer()
        generator = ArtGenerator(size=image_size)
        mapper = ParameterMapper()
    except ValueError as e:
        print(f"Error: {e}")
        print("Make sure to set ANTHROPIC_API_KEY in your .env file")
        return
    
    # Analyze sentiment
    print(f"\nAnalyzing text: \"{args.text[:50]}{'...' if len(args.text) > 50 else ''}\"")
    try:
        sentiment_scores = analyzer.analyze(args.text)
    except Exception as e:
        print(f"Error analyzing text: {e}")
        return
    
    # Get parameters and description
    params = mapper.get_all_parameters(sentiment_scores)
    style_description = params["description"]
    
    # Display scores if requested
    if args.show_scores:
        print("\nSentiment Analysis Results:")
        for dim, score in sentiment_scores.items():
            bar_length = int(score * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"  {dim:15s}: [{bar}] {score:.2f}")
        print(f"\nStyle: {style_description}")
    
    # Generate art
    if args.all_noise:
        print("\nGenerating all 4 noise variations...")
        
        # Generate all noise variations
        noise_variations = generator.generate_all_noise_variations(sentiment_scores)
        
        # Create subdirectory for noise variations
        if args.output:
            noise_dir = session_dir / f"{args.output}_noise_variations"
        else:
            safe_text = "".join(c for c in args.text[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_text = safe_text.replace(' ', '_')
            noise_dir = session_dir / f"noise_variations_{safe_text}" if safe_text else session_dir / "noise_variations"
        
        noise_dir.mkdir(exist_ok=True)
        saved_paths = []
        
        for noise_type, image in noise_variations.items():
            image_path = noise_dir / f"{noise_type}.png"
            image.save(image_path)
            saved_paths.append(str(image_path))
            print(f"  ✓ Saved {noise_type} noise: {image_path.name}")
        
        # Save comprehensive log for noise variations
        log_path = save_generation_log(
            session_dir, noise_dir.name,
            text=args.text,
            sentiment_scores=sentiment_scores,
            style_description=style_description,
            image_size=list(image_size),
            output_paths=saved_paths,
            noise_types=list(noise_variations.keys()),
            generation_type="all_noise_variations",
            all_parameters=params
        )
        
        print(f"✓ Saved all noise variations to: {noise_dir}/")
        print(f"✓ Saved log to: {log_path}")
        
    elif args.variations > 1:
        print(f"\nGenerating {args.variations} variation(s)...")
        
        # Multiple variations (using default perlin noise)
        images = generator.generate_variations(sentiment_scores, count=args.variations)
        
        # Create subdirectory for variations
        if args.output:
            variations_dir = session_dir / args.output
        else:
            safe_text = "".join(c for c in args.text[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_text = safe_text.replace(' ', '_')
            dir_name = f"variations_{safe_text}" if safe_text else "variations"
            variations_dir = session_dir / dir_name
        
        variations_dir.mkdir(exist_ok=True)
        
        saved_paths = []
        for i, image in enumerate(images):
            image_path = variations_dir / f"variation_{i+1:02d}.png"
            image.save(image_path)
            saved_paths.append(str(image_path))
        
        # Save comprehensive log for variations
        log_path = save_generation_log(
            session_dir, variations_dir.name,
            text=args.text,
            sentiment_scores=sentiment_scores,
            style_description=style_description,
            image_size=list(image_size),
            output_paths=saved_paths,
            variations=args.variations,
            all_parameters=params
        )
        
        print(f"✓ Saved {args.variations} variations to: {variations_dir}/")
        print(f"✓ Saved log to: {log_path}")
        
    else:
        print(f"\nGenerating single image...")
        
        # Single image
        image = generator.generate(sentiment_scores)
        
        # Determine filename
        if args.output:
            filename_base = Path(args.output).stem
        else:
            # Create safe filename from text
            safe_text = "".join(c for c in args.text[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_text = safe_text.replace(' ', '_')
            filename_base = f"art_{safe_text}" if safe_text else "art"
        
        # Save image
        image_path = session_dir / f"{filename_base}.png"
        image.save(image_path)
        
        # Save comprehensive log
        log_path = save_generation_log(
            session_dir, filename_base,
            text=args.text,
            sentiment_scores=sentiment_scores,
            style_description=style_description,
            image_size=list(image_size),
            output_path=str(image_path),
            variations=1,
            all_parameters=params
        )
        
        print(f"✓ Saved art to: {image_path}")
        print(f"✓ Saved log to: {log_path}")


def batch_cmd(args):
    """Generate art for multiple texts from a file."""
    # Parse size
    image_size = parse_size(args.size)
    
    # Read texts
    with open(args.texts_file, 'r') as f:
        texts = [line.strip() for line in f if line.strip()]
    
    if not texts:
        print("Error: No texts found in file")
        return
    
    print(f"Found {len(texts)} texts to process")
    
    # Create output structure
    session_dir = create_output_structure()
    
    # Create batch directory
    batch_dir_name = args.output_dir if args.output_dir else "batch_output"
    batch_dir = session_dir / batch_dir_name
    batch_dir.mkdir(exist_ok=True)
    
    print(f"Batch session: {session_dir}")
    print(f"Batch output: {batch_dir}")
    
    # Initialize components
    try:
        analyzer = SentimentAnalyzer()
        generator = ArtGenerator(size=image_size)
        mapper = ParameterMapper()
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Process each text
    batch_log = {
        "batch_info": {
            "total_texts": len(texts),
            "image_size": list(image_size),
            "source_file": args.texts_file,
            "processing_results": []
        }
    }
    
    for i, text in enumerate(texts, 1):
        print(f"\n[{i}/{len(texts)}] Processing: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
        
        try:
            # Analyze and generate
            sentiment_scores = analyzer.analyze(text)
            image = generator.generate(sentiment_scores)
            params = mapper.get_all_parameters(sentiment_scores)
            
            # Create safe filename
            safe_filename = "".join(c for c in text[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_filename = safe_filename.replace(' ', '_')
            filename_base = f"{i:03d}_{safe_filename}" if safe_filename else f"{i:03d}_text"
            
            # Save image
            image_path = batch_dir / f"{filename_base}.png"
            image.save(image_path)
            
            # Save individual log
            individual_log_path = save_generation_log(
                batch_dir, filename_base,
                text=text,
                sentiment_scores=sentiment_scores,
                style_description=params["description"],
                image_size=list(image_size),
                output_path=str(image_path),
                batch_index=i,
                all_parameters=params
            )
            
            # Add to batch log
            batch_log["batch_info"]["processing_results"].append({
                "index": i,
                "text": text,
                "image_path": str(image_path),
                "log_path": str(individual_log_path),
                "status": "success"
            })
            
            print(f"  ✓ Generated art and logs")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            batch_log["batch_info"]["processing_results"].append({
                "index": i,
                "text": text,
                "status": "error",
                "error": str(e)
            })
            continue
    
    # Save batch summary log
    batch_log_path = save_generation_log(session_dir, "batch_summary", **batch_log)
    
    print(f"\n✓ Batch processing complete.")
    print(f"✓ Images saved to: {batch_dir}/")
    print(f"✓ Batch summary: {batch_log_path}")


def test_cmd(args):
    """Run a test with sample texts to verify setup."""
    test_texts = [
        "The storm raged with unprecedented fury, lightning splitting the darkness!",
        "A gentle breeze whispered through the meadow at dawn.",
        "Complex patterns emerged from the chaotic interplay of forces beyond comprehension."
    ]
    
    print("Running Cue test suite...\n")
    
    # Test sentiment analysis
    try:
        analyzer = SentimentAnalyzer()
        print("✓ Sentiment analyzer initialized")
    except Exception as e:
        print(f"✗ Failed to initialize sentiment analyzer: {e}")
        return
    
    # Test each sample
    for i, text in enumerate(test_texts, 1):
        print(f"\nTest {i}: \"{text}\"")
        try:
            scores = analyzer.analyze(text)
            print("  Sentiment scores:")
            for dim, score in scores.items():
                print(f"    {dim}: {score:.2f}")
        except Exception as e:
            print(f"  ✗ Analysis failed: {e}")
    
    print("\n✓ Test complete!")


def info_cmd(args):
    """Display information about Cue configuration."""
    from config import SENTIMENT_DIMENSIONS, MODEL_NAME
    
    print("Cue - Experimental Generative Art using Sentiment Analysis")
    print("=" * 60)
    print(f"\nModel: {MODEL_NAME}")
    print(f"\nSentiment Dimensions:")
    for dim in SENTIMENT_DIMENSIONS:
        print(f"  • {dim}")
    print(f"\nDefault Image Size: {DEFAULT_IMAGE_SIZE[0]}x{DEFAULT_IMAGE_SIZE[1]}")
    print("\nFor more information: https://github.com/yourusername/cue")


def browse_cmd(args):
    """Browse previous output sessions and their contents."""
    output_dir = Path("output")
    
    if not output_dir.exists():
        print("No output directory found. Generate some art first!")
        return
    
    # Find all session directories
    sessions = sorted([d for d in output_dir.iterdir() if d.is_dir() and d.name.startswith("session_")])
    
    if not sessions:
        print("No output sessions found.")
        return
    
    print(f"Found {len(sessions)} output session(s):\n")
    
    for session in sessions:
        # Parse timestamp from directory name
        timestamp_str = session.name.replace("session_", "")
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            formatted_time = timestamp_str
        
        print(f"📁 {session.name} ({formatted_time})")
        
        # Count contents
        images = list(session.glob("*.png"))
        logs = list(session.glob("*_log.json"))
        subdirs = [d for d in session.iterdir() if d.is_dir()]
        
        if images:
            print(f"   🖼️  {len(images)} image(s)")
        if logs:
            print(f"   📋 {len(logs)} log file(s)")
        if subdirs:
            print(f"   📂 {len(subdirs)} subdirectorie(s): {', '.join(d.name for d in subdirs)}")
        
        # Show recent log summary if available
        recent_logs = sorted(logs, key=lambda x: x.stat().st_mtime, reverse=True)
        if recent_logs:
            try:
                with open(recent_logs[0]) as f:
                    log_data = json.load(f)
                    if "generation_info" in log_data and "text" in log_data["generation_info"]:
                        text_preview = log_data["generation_info"]["text"][:60]
                        if len(log_data["generation_info"]["text"]) > 60:
                            text_preview += "..."
                        print(f"   💬 Last: \"{text_preview}\"")
            except:
                pass
        
        print()
    
    print(f"Output directory: {output_dir.absolute()}")


def show_cmd(args):
    """Show detailed information about a specific session."""
    session_dir = Path("output") / args.session_name
    
    if not session_dir.exists():
        print(f"Session '{args.session_name}' not found.")
        return
    
    print(f"Session: {args.session_name}")
    print("=" * (len(args.session_name) + 9))
    
    # List all files and directories
    items = sorted(session_dir.iterdir(), key=lambda x: (x.is_file(), x.name))
    
    for item in items:
        if item.is_file():
            if item.suffix == ".png":
                print(f"🖼️  {item.name}")
            elif item.name.endswith("_log.json"):
                print(f"📋 {item.name}")
                # Show log summary
                try:
                    with open(item) as f:
                        log_data = json.load(f)
                        if "generation_info" in log_data:
                            gen_info = log_data["generation_info"]
                            if "text" in gen_info:
                                text_preview = gen_info["text"][:80]
                                if len(gen_info["text"]) > 80:
                                    text_preview += "..."
                                print(f"     Text: \"{text_preview}\"")
                            if "sentiment_scores" in gen_info:
                                scores = gen_info["sentiment_scores"]
                                score_str = ", ".join(f"{k}:{v:.2f}" for k, v in scores.items())
                                print(f"     Scores: {score_str}")
                except:
                    print(f"     (Could not read log)")
            else:
                print(f"📄 {item.name}")
        else:
            # Directory
            subdir_contents = list(item.iterdir())
            images_count = len([f for f in subdir_contents if f.suffix == ".png"])
            print(f"📂 {item.name}/ ({images_count} images)")
    
    print(f"\nPath: {session_dir.absolute()}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Cue - Generate art from text sentiment analysis")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate art from text sentiment analysis')
    generate_parser.add_argument('text', help='The text to analyze and convert to art')
    generate_parser.add_argument('-o', '--output', help='Output image path (will be created in output structure)')
    generate_parser.add_argument('-s', '--size', default='1920x1080', help='Image size (WIDTHxHEIGHT)')
    generate_parser.add_argument('-v', '--variations', type=int, default=1, help='Number of variations to generate')
    generate_parser.add_argument('-S', '--show-scores', action='store_true', help='Display sentiment analysis scores')
    generate_parser.add_argument('--all-noise', action='store_true', help='Generate all 5 noise variations (gradient, perlin, fbm, worley, reaction) instead of a single image')
    generate_parser.set_defaults(func=generate_cmd)
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Generate art for multiple texts from a file')
    batch_parser.add_argument('texts_file', help='Path to file containing texts (one per line)')
    batch_parser.add_argument('-o', '--output-dir', help='Output directory name within session')
    batch_parser.add_argument('-s', '--size', default='1920x1080', help='Image size (WIDTHxHEIGHT)')
    batch_parser.set_defaults(func=batch_cmd)
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run a test with sample texts to verify setup')
    test_parser.set_defaults(func=test_cmd)
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Display information about Cue configuration')
    info_parser.set_defaults(func=info_cmd)
    
    # Browse command
    browse_parser = subparsers.add_parser('browse', help='Browse previous output sessions and their contents')
    browse_parser.set_defaults(func=browse_cmd)
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show detailed information about a specific session')
    show_parser.add_argument('session_name', help='Name of the session directory (e.g., session_20240710_180456)')
    show_parser.set_defaults(func=show_cmd)
    
    # Parse arguments and run command
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


# Direct command entry points for console scripts
def generate():
    """Direct entry point for generate command."""
    import sys
    sys.argv = ['cue', 'generate'] + sys.argv[1:]
    main()

def batch():
    """Direct entry point for batch command."""
    import sys
    sys.argv = ['cue', 'batch'] + sys.argv[1:]
    main()

def test():
    """Direct entry point for test command."""
    import sys
    sys.argv = ['cue', 'test'] + sys.argv[1:]
    main()

def info():
    """Direct entry point for info command."""
    import sys
    sys.argv = ['cue', 'info'] + sys.argv[1:]
    main()

def browse():
    """Direct entry point for browse command."""
    import sys
    sys.argv = ['cue', 'browse'] + sys.argv[1:]
    main()

def show():
    """Direct entry point for show command."""
    import sys
    sys.argv = ['cue', 'show'] + sys.argv[1:]
    main()


if __name__ == "__main__":
    main()
