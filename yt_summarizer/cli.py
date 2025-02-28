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
    parser.add_argument("-f", "--fix-product-names", action="store_true", help="Enable second pass to fix product names")
    parser.add_argument("-p", "--print", action="store_true", help="Print the summary to the terminal")
    
    # Catch the case where no arguments are provided
    if len(sys.argv) == 1:
        console.print("\n[bold red]ERROR:[/bold red] [bold white on red]The following arguments are required: url[/bold white on red]\n")
        parser.print_help()
        sys.exit(1)
    
    try:
        args = parser.parse_args()
    except Exception as e:
        # Make the error message stand out
        error_msg = str(e)
        console.print(f"\n[bold red]ERROR:[/bold red] [bold white on red]{error_msg}[/bold white on red]\n")
        parser.print_help()
        sys.exit(1)
    
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
            console.print("\n[bold red]ERROR:[/bold red] [bold white on red]Invalid YouTube URL or video ID[/bold white on red]\n")
            sys.exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Create a single task with 4 steps
            task = progress.add_task("[cyan]Processing...", total=4)
            
            # Step 1: Get video information
            progress.update(task, description="[cyan]Fetching video information...")
            video_info = get_video_info(video_id)
            progress.update(task, advance=1)
            
            # Step 2: Download transcript
            progress.update(task, description="[cyan]Downloading transcript...")
            transcript_data = get_transcript(video_id)
            transcript_text = format_transcript(transcript_data)
            progress.update(task, advance=1)
            
            # Step 3: Generate summary
            progress.update(task, description="[cyan]Generating summary...")
            summary = generate_summary(transcript_text, video_info, model, api_key, args.fix_product_names)
            progress.update(task, advance=1)
            
            # Step 4: Save summary
            progress.update(task, description="[cyan]Saving summary...")
            output_path = save_summary(summary, video_info, video_id, output_dir, args.print, model)
            progress.update(task, advance=1)
        
        # Summary saved message is already printed in save_summary function
        
    except Exception as e:
        # Make the error message stand out
        console.print(f"\n[bold red]ERROR:[/bold red] [bold white on red]{str(e)}[/bold white on red]\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
