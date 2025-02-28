"""
Core functionality for the YouTube transcript summarizer.
"""

import os
import re
import requests
from pathlib import Path
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, VideoUnavailable
from rich.console import Console
from rich.markdown import Markdown

# Initialize Rich console for prettier output
console = Console()

def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    # Common YouTube URL patterns
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard YouTube URLs
        r'(?:embed\/)([0-9A-Za-z_-]{11})',  # Embedded URLs
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})'  # Short youtu.be URLs
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_video_info(video_id):
    """Get video title and other metadata using YouTube API"""
    try:
        # We'll use a simple technique to extract the title from the oEmbed endpoint
        # This doesn't require an API key
        response = requests.get(f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json")
        if response.status_code == 200:
            data = response.json()
            return {
                'title': data.get('title', f'Video {video_id}'),
                'author': data.get('author_name', 'Unknown')
            }
        return {'title': f'Video {video_id}', 'author': 'Unknown'}
    except Exception as e:
        console.print(f"[yellow]Warning: Could not fetch video info: {e}[/yellow]")
        return {'title': f'Video {video_id}', 'author': 'Unknown'}

def get_transcript(video_id):
    """Download transcript for a YouTube video"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        
        # Try to get English transcript first
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            # If no English transcript, get the first available and translate it
            transcript = transcript_list.find_transcript(['en-US', 'en-GB'])
            
        if not transcript:
            # If still no transcript, get any available one and translate it
            transcript = transcript_list[0]
            transcript = transcript.translate('en')
            
        return transcript.fetch()
    except NoTranscriptFound:
        raise Exception("No transcript found for this video.")
    except TranscriptsDisabled:
        raise Exception("Transcripts are disabled for this video.")
    except VideoUnavailable:
        raise Exception("The video is unavailable.")
    except Exception as e:
        raise Exception(f"Error fetching transcript: {str(e)}")

def format_transcript(transcript_data):
    """Format transcript data into a single text string"""
    return " ".join([item['text'] for item in transcript_data])

def generate_summary(transcript_text, video_info, model, api_key, fix_products=True):
    """Generate a summary using OpenRouter API"""
    if not api_key:
        raise Exception("OpenRouter API key not found. Please set it in the .env file.")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Craft a prompt that instructs the model to create a cohesive, well-structured summary
    prompt = f"""
You are a professional content editor who creates clear, cohesive summaries of YouTube videos.

VIDEO TITLE: {video_info['title']}
VIDEO AUTHOR: {video_info['author']}

Below is the transcript of the video. Create a well-structured summary that:

1. Begins with a brief overview of the video's main purpose and core message (1-2 paragraphs)

2. Organizes information into logical, thematic sections with clear headings, even if the original video jumped between topics
   - Group related concepts and points together under common themes. Use natural language, no bullet points
   - Ensure smooth transitions between sections
   - Present information in a logical progression

3. Captures all key information, including:
   - Main arguments and their supporting evidence
   - Important facts, figures, and examples
   - Noteworthy quotes or insights

4. Concludes with a concise paragraph summarizing the video's main takeaways

Format guidelines:
- Use Markdown formatting
- Create a logical hierarchy with headings (## for main sections, ### for subsections)
- Bold key terms or important statements
- Include a "Key Points" section at the end that highlights 3-5 essential takeaways

The summary should read as a cohesive whole, as if it were a well-structured article on the topic, not just a collection of notes.

TRANSCRIPT:
{transcript_text}
"""

    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text}")
        
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            initial_summary = result['choices'][0]['message']['content']
            # Second pass to fix product names if enabled
            if fix_products:
                return fix_product_names(initial_summary, video_info, model, api_key, headers)
            else:
                return initial_summary
        else:
            raise Exception("Unexpected API response format")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error generating summary: {str(e)}")

def fix_product_names(summary, video_info, model, api_key, headers):
    """Second pass to fix any incorrect product names in the summary"""
    
    prompt = f"""
You are a product name accuracy reviewer. Review the following summary of a YouTube video and fix any product names that seem incorrect based on the context. 

VIDEO TITLE: {video_info['title']}
VIDEO AUTHOR: {video_info['author']}

Focus ONLY on correcting product names, brand names, and technical terms that appear to be incorrect or misspelled based on the context. 
Do not make any other changes to the summary's content, structure, or style.

Return the entire summary with any product name corrections made.

SUMMARY:
{summary}
"""

    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        console.print("[cyan]Running second pass to fix product names...[/cyan]")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            console.print("[yellow]Warning: Second pass failed, using initial summary[/yellow]")
            return summary
        
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            console.print("[yellow]Warning: Unexpected API response in second pass, using initial summary[/yellow]")
            return summary
    except Exception as e:
        console.print(f"[yellow]Warning: Error in second pass: {str(e)}. Using initial summary.[/yellow]")
        return summary

def sanitize_filename(title):
    """Convert a string to a safe filename"""
    # Replace illegal filename characters with underscores
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
    # Limit length and trim spaces
    return safe_title[:100].strip()

def save_summary(summary, video_info, video_id, output_dir=None):
    """Save the summary as a markdown file and print it to the terminal"""
    # Create output directory if specified
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        base_path = Path(output_dir)
    else:
        base_path = Path.cwd()
    
    # Get current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create filename from video title or ID with timestamp
    filename = f"{sanitize_filename(video_info['title'])}-{video_id}_{timestamp}.md"
    file_path = base_path / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        # Add metadata at the top of the file
        f.write(f"# {video_info['title']}\n\n")
        f.write(f"**Channel:** {video_info['author']}\n")
        f.write(f"**Video ID:** {video_id}\n")
        f.write(f"**URL:** https://www.youtube.com/watch?v={video_id}\n\n")
        f.write("---\n\n")
        f.write(summary)
    
    # Print the summary to the terminal in a pretty way
    console.print("\n[bold green]Summary Generated:[/bold green]")
    console.print(f"[bold cyan]# {video_info['title']}[/bold cyan]")
    console.print(f"[cyan]Channel:[/cyan] {video_info['author']}")
    console.print(f"[cyan]Video ID:[/cyan] {video_id}")
    console.print(f"[cyan]URL:[/cyan] https://www.youtube.com/watch?v={video_id}")
    console.print("\n[cyan]---[/cyan]\n")
    
    # Use Rich's Markdown rendering to display the summary with formatting
    md = Markdown(summary)
    console.print(md)
    
    console.print(f"\n[green]Summary saved to:[/green] {file_path}\n")
    
    return file_path
