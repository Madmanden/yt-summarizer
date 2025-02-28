#!/usr/bin/env python3
"""
CLI entrypoint for YouTube Video Transcript Summarizer
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .summarizer import (
    extract_video_id,
    get_video_info,
    get_transcript,
    format_transcript,
    generate_summary,
    save_summary
)

console = Console()

def main():
    """Main function to process command-line arguments and orchestrate the summarization"""
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Summarize YouTube video transcripts")
    parser.add_argument("url", help="YouTube video URL or ID")
    parser.add_argument("-o", "--output", help="Output directory for the summary file")
    parser.add_argument("-m", "--model", help="OpenRouter model to use (defaults to value in .env)")
    parser.add_argument("-k", "--api-key", help="OpenRouter API key (defaults to OPENROUTER_API_KEY env var)")
    parser.add_argument("--no-product-fix", action="store_true", help="Disable second pass to fix product names")
    parser.add_argument("--print", action="store_true", help="Print the summary to the terminal")
    args = parser.parse_args()
    
    # Get the model from arguments or environment
    model = args.model or os.getenv('OPENROUTER_MODEL', 'openai/gpt-4o-mini')
    
    # Get API key from arguments or environment
    api_key = args.api_key or os.getenv('OPENROUTER_API_KEY')
    
    # Default output directory to 'summaries' if not provided
    output_dir = args.output if args.output else 'summaries'
    
    try:
        # Extract video ID from URL or assume it's already an ID
        video_id = extract_video_id(args.url) or args.url
        if not video_id or len(video_id) != 11:
            console.print("[bold red]Error: Invalid YouTube URL or video ID[/bold red]")
            sys.exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Step 1: Get video information
            task = progress.add_task("[cyan]Fetching video information...", total=None)
            video_info = get_video_info(video_id)
            progress.update(task, completed=True)
            
            # Step 2: Download transcript
            task = progress.add_task("[cyan]Downloading transcript...", total=None)
            transcript_data = get_transcript(video_id)
            transcript_text = format_transcript(transcript_data)
            progress.update(task, completed=True)
            
            # Step 3: Generate summary
            task = progress.add_task("[cyan]Generating summary...", total=None)
            summary = generate_summary(transcript_text, video_info, model, api_key, not args.no_product_fix)
            progress.update(task, completed=True)
            
            # Step 4: Save summary
            task = progress.add_task("[cyan]Saving summary...", total=None)
            output_path = save_summary(summary, video_info, video_id, output_dir, args.print)
            progress.update(task, completed=True)
        
        console.print(f"[bold green]Summary saved to:[/bold green] {output_path}")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
