import os
from pydub import AudioSegment
import math

def parse_time(time_str):
    """
    Parses a time string in the format 'MM:SS' or 'SS' into milliseconds.
    """
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return (minutes * 60 + seconds) * 1000
        else:
            return float(time_str) * 1000
    except ValueError:
        return None

def main():
    print("--- Manual Audio Splitter ---")
    
    # 1. Get input file
    input_file = input("Enter the path to the audio file: ").strip().strip("'").strip('"')
    
    if not os.path.isfile(input_file):
        print(f"Error: File not found at '{input_file}'")
        return

    # 2. Start time
    while True:
        start_str = input("Enter start time (MM:SS or seconds): ").strip()
        start_ms = parse_time(start_str)
        if start_ms is not None:
            break
        print("Invalid format. Please use MM:SS or seconds (e.g., 1:30 or 90).")

    # 3. End time
    while True:
        end_str = input("Enter end time (MM:SS or seconds): ").strip()
        end_ms = parse_time(end_str)
        if end_ms is not None:
            if end_ms > start_ms:
                break
            else:
                print("End time must be greater than start time.")
        else:
            print("Invalid format. Please use MM:SS or seconds.")

    try:
        print("Loading audio file... (this might take a moment)")
        audio = AudioSegment.from_file(input_file)
        
        # Check if times are within bounds
        if start_ms < 0 or end_ms > len(audio):
            print(f"Warning: Specified range is out of bounds. Audio length: {len(audio)/1000:.2f}s")
            # Clamp end time if needed? Or just let pydub handle/error? 
            # Pydub slicing handles out of bounds gracefully usually, but let's be safe
            end_ms = min(end_ms, len(audio))

        # Split
        print(f"Cutting from {start_ms/1000:.2f}s to {end_ms/1000:.2f}s...")
        cut_segment = audio[start_ms:end_ms]

        # Output folder
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Output filename
        base_name = os.path.basename(input_file)
        name, ext = os.path.splitext(base_name)
        # remove dot from ext for export format if needed, but pydub infers from filename usually
        # format string for filename
        output_filename = f"{name}_{int(start_ms/1000)}_{int(end_ms/1000)}{ext}"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"Exporting to {output_path}...")
        cut_segment.export(output_path, format=ext.replace('.', ''))
        
        print("Done!")

    except Exception as e:
        print(f"An error occurred: {e}")
        # Hint about ffmpeg if it's a likely cause
        if "ffmpeg" in str(e).lower() or "file not found" in str(e).lower():
            print("Tip: Make sure ffmpeg is installed and accessible in your system PATH.")

if __name__ == "__main__":
    main()
