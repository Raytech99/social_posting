#Generate a script for a story
import ollama
import openai
import dotenv
from dotenv import load_dotenv
import os
# Import whisper-timestamped
import whisper_timestamped as whisper
import json # Useful for inspecting whisper results
# Import moviepy
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings # Optional: If ImageMagick path needs setting
change_settings({"IMAGEMAGICK_BINARY": r"/opt/homebrew/bin/magick"}) # Example for Homebrew on Apple Silicon

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LOCAL_LLM_PROVIDER = "ollama" # Or "lmstudio" if you add that function back
OLLAMA_MODEL = "mistral"
TEMP_AUDIO_FILENAME = "temp_story_audio.mp3"

# --- Whisper Configuration ---
WHISPER_MODEL_SIZE = "base" # Options: "tiny", "base", "small", "medium", "large"
WHISPER_DEVICE = "cpu" # Use "cpu" for reliability, "mps" might work on M4 Pro but can be less stable

# --- Video Configuration ---
BACKGROUND_VIDEO_DIR = "background_videos" # Folder for input videos
BACKGROUND_VIDEO_FILENAME = "minecraft_parkour.mp4" # IMPORTANT: Change to your video file name
BACKGROUND_VIDEO_PATH = os.path.join(BACKGROUND_VIDEO_DIR, BACKGROUND_VIDEO_FILENAME)
OUTPUT_VIDEO_FILENAME = "final_story_video.mp4"
OUTPUT_VIDEO_DIR = "output_videos" # Folder to save final videos
# Caption Styling (Updated for bold social media style)
CAPTION_FONT = 'Impact' # Popular social media font; alternatives: 'Arial-Black', 'Helvetica-Bold'
CAPTION_FONTSIZE = 35 # Much larger text
CAPTION_COLOR = 'white'
CAPTION_STROKE_COLOR = 'black' # Outline for better visibility
CAPTION_STROKE_WIDTH = 1.5 # Width of the outline

#Generate a script for a story
def generate_script_ollama(idea, model_name="mistral"): # Or specify a more precise model like "mistral:7b"
    print(f"Generating script with Ollama ({model_name})...")
    try:
        # Make sure Ollama server is running and the model is pulled/available
        response = ollama.chat(
            model=model_name,
            messages=[
                {
                    "role": "system", 
                    "content": """
                    You are a writer specializing in short, viral stories with unexpected twists, perfect for platforms like Reddit or short-form video. Your goal is to create narratives that immediately present a shocking or seemingly clear-cut situation, often negative (like a scandal, betrayal, or bizarre behavior), and then reveal hidden context or a twist later that completely re-frames the initial perception, creating a moral gray area.

                    Key requirements:
                    1.  **DIRECT HOOK START:** Start the story IMMEDIATELY with the single most dramatic, confusing, or outrageous sentence. **DO NOT** include any title, greeting, preamble, or introductory text like "Script:" or "Title:". The very first word of your response must be the first word of the story's hook. Use the "I" perspective.
                    2.  **Build on Premise:** Develop the story based on the initial (misleading) premise. Show reactions, consequences, or escalating weirdness based on that first impression.
                    3.  **The Twist/Reveal:** Introduce new information or context partway through that fundamentally changes the meaning of the initial hook and subsequent events. This reveal should make the audience rethink everything.
                    4.  **Show, Don't Just Tell:** Use specific details, actions, and dialogue snippets to make both the initial premise and the later reveal feel convincing. Include details like timelines or specific objects if relevant.
                    5.  **Engaging Tone:** Write in a slightly informal, potentially gossipy, or "I can't believe this happened" style.
                    6.  **Cliffhanger/Question:** End with an open question for the audience related to the moral dilemma or the aftermath ("AITA for thinking X?", "What would you have done?", "Is he the villain or the victim?").
                    7.  **Length:** Aim for 300 words.
                    """
                 },
                {
                    "role": "user",
                    "content": f"Write a story based on this core idea: {idea}"
                }
            ]
        )
        script = response['message']['content']
        print(f"Script: {script}")
        return script
    except Exception as e:
        print(f"Error connecting to Ollama or generating script: {e}")
        print("Make sure the Ollama server is running and the model is available.")
        return None # Handle error appropriately

#Generate speech for the script
# --- Text-to-Speech Function ---
def generate_audio_openai(script_text, output_path):
    """Generates audio from text using OpenAI TTS and saves it."""
    print(f"Generating audio using OpenAI TTS...")
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        return False
    if not script_text:
        print("Error: No script text provided to generate audio.")
        return False

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        # You can choose different models and voices:
        # Models: "tts-1" (faster), "tts-1-hd" (higher quality), "gpt-4o-mini-tts" (newest)
        # Voices: "alloy", "echo", "fable", "onyx", "nova", "shimmer" (coral for gpt-4o-mini-tts)
        # Stream the audio directly to the file
        with open(output_path, "wb") as file:
            with client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice="echo",
                input=script_text,
                speed=1.6  # Speed up the speech (0.25-4.0, default 1.0)
            ) as response:
                for chunk in response.iter_bytes():
                    file.write(chunk)
        print(f"Audio successfully saved to {output_path}")
        return True
    except openai.APIConnectionError as e:
        print(f"Failed to connect to OpenAI API: {e}")
        return False
    except openai.AuthenticationError as e:
         print(f"OpenAI Authentication Error: Check your API key. {e}")
         return False
    except openai.RateLimitError as e:
        print(f"OpenAI Rate Limit Exceeded: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during TTS generation: {e}")
        return False
    
# --- NEW: Word Timestamp Function ---
def get_word_timestamps(audio_path):
    """
    Transcribes audio using whisper-timestamped to get word-level timestamps.
    Requires ffmpeg to be installed system-wide.
    """
    print(f"\n--- Starting Word Timestamp Generation ---")
    print(f"Processing audio file: {audio_path}")
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return None

    try:
        # Load the Whisper model (runs locally).
        # Downloads the model automatically on first run for the specified size.
        print(f"Loading Whisper model '{WHISPER_MODEL_SIZE}' on device '{WHISPER_DEVICE}' (this may take time)...")
        model = whisper.load_model(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE)
        print("Whisper model loaded.")

        print("Loading audio data...")
        audio = whisper.load_audio(audio_path)
        print("Audio data loaded.")

        print("Transcribing and aligning audio (this is the core Whisper process)...")
        # Perform transcription with word-level timestamps
        # beam_size=5 and best_of=5 can improve accuracy but slow down transcription
        result = whisper.transcribe(model, audio, language="en", beam_size=5, best_of=5, vad=False)
        print("Transcription and alignment complete.")

        # Optional: Save the full transcription result as JSON for inspection
        json_output_path = os.path.splitext(audio_path)[0] + "_timestamps.json"
        with open(json_output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Full timestamp data saved to {json_output_path}")

        # Extract and return the segments containing word timestamps
        if 'segments' in result and result['segments']:
             print(f"Successfully extracted {len(result['segments'])} segments with word timestamps.")
             print(f"--- Word Timestamp Generation Finished ---")
             return result['segments'] # Return the list of segments
        else:
            print("Warning: No segments or words found in the transcription.")
            print(f"--- Word Timestamp Generation Finished (No Segments) ---")
            return [] # Return empty list if no segments found

    except Exception as e:
        print(f"An error occurred during Whisper timestamp generation: {e}")
        # Specific check for ffmpeg error
        if "ffmpeg" in str(e).lower():
             print("Hint: Make sure ffmpeg is installed and accessible in your system's PATH (e.g., 'brew install ffmpeg' on macOS).")
        print(f"--- Word Timestamp Generation Failed ---")
        return None

# --- Video Creation Function (Improved Captions) ---
def create_video(background_video_path, audio_path, segments, output_path):
    """
    Creates the final video by combining background video, audio, and word captions.
    Groups words together for more natural reading and centers them on screen.
    """
    print(f"\n--- Starting Video Generation ---")
    print(f"Using background: {background_video_path}")
    print(f"Using audio: {audio_path}")
    print(f"Saving to: {output_path}")

    # Basic checks
    if not os.path.exists(background_video_path): return False
    if not os.path.exists(audio_path): return False
    if not segments: return False

    video_clip = None
    audio_clip = None
    final_clip = None
    caption_clips = []

    try:
        # Load clips
        print("Loading video and audio clips...")
        video_clip = VideoFileClip(background_video_path)
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        print(f"Audio duration: {audio_duration:.2f}s")

        # Trim video to audio duration
        if video_clip.duration > audio_duration:
            print(f"Trimming video from {video_clip.duration:.2f}s to {audio_duration:.2f}s")
            video_clip = video_clip.subclip(0, audio_duration)
        elif video_clip.duration < audio_duration:
             print(f"Warning: Background video ({video_clip.duration:.2f}s) is shorter than audio ({audio_duration:.2f}s). Video will end early.")
             audio_clip = audio_clip.subclip(0, video_clip.duration)
             audio_duration = video_clip.duration

        print("Assigning audio to video...")
        video_clip = video_clip.set_audio(audio_clip)

        # Create grouped TextClips (2-3 words at a time)
        print("Generating caption clips with word grouping...")
        
        # Constants for grouping
        GROUP_SIZE = 3  # Number of words per group
        MIN_DURATION = 0.5  # Minimum duration for any caption (in seconds)
        
        processed_words = 0
        total_words = sum(len(s.get('words', [])) for s in segments)
        textclip_creation_errors = 0

        for segment in segments:
            if 'words' not in segment: continue
            
            # Process each segment's words in groups
            word_group = []
            group_start_time = None
            group_end_time = None
            
            for i, word_info in enumerate(segment['words']):
                word_text = word_info.get('text', '').strip()
                start_time = word_info.get('start')
                end_time = word_info.get('end')
                
                # Skip words outside the audio duration
                if start_time is not None and start_time >= audio_duration: continue
                if end_time is not None and end_time > audio_duration: end_time = audio_duration

                # Valid word to add to group
                if word_text and start_time is not None and end_time is not None and end_time > start_time:
                    # First word in group - set the starting time
                    if len(word_group) == 0:
                        group_start_time = start_time
                    
                    # Add word to group
                    word_group.append(word_text)
                    group_end_time = end_time
                    processed_words += 1
                    
                    # Create caption when group is full or segment ends
                    if len(word_group) >= GROUP_SIZE or i == len(segment['words']) - 1:
                        # Only create caption if we have words and timing
                        if word_group and group_start_time is not None and group_end_time is not None:
                            # Create caption for the word group
                            group_text = " ".join(word_group)
                            duration = group_end_time - group_start_time
                            
                            # Ensure minimum duration
                            if duration < MIN_DURATION:
                                duration = MIN_DURATION
                            
                            try:
                                txt_clip = TextClip(
                                    group_text,
                                    fontsize=CAPTION_FONTSIZE,
                                    font=CAPTION_FONT,
                                    color=CAPTION_COLOR,
                                    stroke_color=CAPTION_STROKE_COLOR,
                                    stroke_width=CAPTION_STROKE_WIDTH,
                                    method='label',  # 'label' for single line without background
                                    align='center'   # Center-align the text
                                )
                                # Center text both horizontally and vertically
                                txt_clip = txt_clip.set_position('center').set_start(group_start_time).set_duration(duration)
                                caption_clips.append(txt_clip)
                            except Exception as e:
                                print(f"Failed to create TextClip for '{group_text}'")
                                print(f"Error: {e}")
                                textclip_creation_errors += 1
                                
                            # Reset for next group
                            word_group = []
                            group_start_time = None

                # Print progress periodically
                if processed_words % 50 == 0 and processed_words > 0:
                    print(f"  Processed {processed_words}/{total_words} words...")

        print(f"Created {len(caption_clips)} caption groups from {processed_words} words.")
        if textclip_creation_errors > 0: print(f"Encountered {textclip_creation_errors} errors during TextClip creation.")

        # Composite clips
        print("Compositing video and captions...")
        final_clip = CompositeVideoClip([video_clip] + caption_clips)

        # Write final video
        print(f"Writing final video to {output_path} (this can take a significant amount of time)...")
        final_clip.write_videofile(
            output_path, codec='libx264', audio_codec='aac',
            temp_audiofile='temp-audio.m4a', remove_temp=True,
            threads=4, preset='medium', logger='bar'
        )
        print(f"--- Video Generation Finished Successfully ---")
        return True

    except Exception as e:
        print(f"An error occurred during video generation: {e}")
        if "ImageMagick" in str(e):
             print("Hint: This might be an ImageMagick issue.")
        print(f"--- Video Generation Failed ---")
        return False

    finally:
        # Close clips
        print("Closing video/audio clips...")
        try:
            if audio_clip: audio_clip.close()
            if video_clip: video_clip.close()
            for tc in caption_clips: tc.close()
            if final_clip: final_clip.close()
            print("Clips closed.")
        except Exception as e:
            print(f"Warning: Error closing clips: {e}")

    # --- Main Execution Logic ---
if __name__ == "__main__":
    print("Starting Insta Brain Rot Bot Script...")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_VIDEO_DIR):
        os.makedirs(OUTPUT_VIDEO_DIR)
    if not os.path.exists(BACKGROUND_VIDEO_DIR):
         print(f"Warning: Background video directory '{BACKGROUND_VIDEO_DIR}' not found. Please create it and add videos.")
         # Optionally create it: os.makedirs(BACKGROUND_VIDEO_DIR)

    # --- Step 1: Generate Script ---
    #story_idea = input("Enter your story idea: ")
    story_idea = "My neighbor keeps leaving creepy, anonymous 'gifts' on my doorstep late at night."# Example idea
    generated_script = None

    print(f"\n--- Step 1: Generating Script ---")
    print(f"Using local LLM provider: {LOCAL_LLM_PROVIDER}")
    # ... (Your existing Ollama/LM Studio script generation logic) ...
    if LOCAL_LLM_PROVIDER == "ollama":
        generated_script = generate_script_ollama(story_idea, model_name=OLLAMA_MODEL)
    elif LOCAL_LLM_PROVIDER == "lmstudio":
        #generated_script = generate_script_lmstudio(story_idea, model_identifier=LMSTUDIO_MODEL_ID)
        print(f"Failed to get local LLM provider")
        pass
    # ... (Error handling) ...

    # --- Step 2: Generate TTS Audio ---
    audio_generated = False
    timestamp_segments = None # Initialize variable for timestamps
    
    if generated_script:
        print(f"\n--- Step 2: Generating TTS Audio ---")
        print("\nScript generated successfully! Proceeding to TTS...")
        
        # Save the script to a text file
        script_path = os.path.join(".", "script.txt")
        with open(script_path, "w", encoding="utf-8") as file:
            file.write(generated_script)
        print(f"Script saved to {script_path}")
        
        # Define the output path for the temporary audio file
        temp_audio_path = os.path.join(".", TEMP_AUDIO_FILENAME) # Save in root project dir for now

        # Choose TTS provider (can add logic later for ElevenLabs)
        audio_generated = generate_audio_openai(generated_script, temp_audio_path)

    else:
        print("\nFailed to generate script. Skipping TTS.")

    # --- Step 3: Generate Word Timestamps ---
    if audio_generated:
        print(f"\n--- Step 3: Generating Word Timestamps ---")
        # Call the word timestamp function
        timestamp_segments = get_word_timestamps(temp_audio_path)

        if timestamp_segments is not None:
             # Optional: Print first few words for verification
             if timestamp_segments and len(timestamp_segments) > 0 and 'words' in timestamp_segments[0] and timestamp_segments[0]['words']:
                  print("\nFirst few words with timestamps:")
                  for i, word_info in enumerate(timestamp_segments[0]['words'][:5]):
                       print(f"  '{word_info['text']}' - Start: {word_info['start']:.2f}s, End: {word_info['end']:.2f}s")
             else:
                  print("\nNo words found in the first segment to display timestamps for.")
             
             # Save the word timestamps to a separate file for easy access
             timestamps_txt_path = os.path.join(".", "word_timestamps.txt")
             try:
                 with open(timestamps_txt_path, "w", encoding="utf-8") as f:
                     for segment in timestamp_segments:
                         # Handle potential missing keys gracefully
                         seg_id = segment.get('id', 'N/A')
                         seg_start = segment.get('start', 0)
                         seg_end = segment.get('end', 0)
                         seg_text = segment.get('text', '').strip()
                         f.write(f"Segment {seg_id} [{seg_start:.2f}s - {seg_end:.2f}s]: {seg_text}\n")
                         if 'words' in segment:
                             for word in segment['words']:
                                 word_text = word.get('text', '')
                                 word_start = word.get('start', 0)
                                 word_end = word.get('end', 0)
                                 f.write(f"  '{word_text}' [{word_start:.2f}s - {word_end:.2f}s]\n")
                 print(f"Word timestamps saved to {timestamps_txt_path}")
             except Exception as e:
                 print(f"Error saving timestamps to file: {e}")
        else:
             print("\nFailed to generate word timestamps.")
    else:
        print("\nAudio generation failed or was skipped. Skipping Whisper Timestamps.")

    # --- Step 4: Video Generation ---
    print(f"\n--- Step 4: Generating Final Video ---")
    video_generated = False
    if timestamp_segments: # Only proceed if timestamps exist
        # Define final output path
        output_video_path = os.path.join(OUTPUT_VIDEO_DIR, OUTPUT_VIDEO_FILENAME)
        # Ensure background video exists before calling
        if os.path.exists(BACKGROUND_VIDEO_PATH):
             video_generated = create_video(
                 background_video_path=BACKGROUND_VIDEO_PATH,
                 audio_path=temp_audio_path,
                 segments=timestamp_segments,
                 output_path=output_video_path
             )
        else:
             print(f"Error: Background video not found at '{BACKGROUND_VIDEO_PATH}'. Cannot create video.")
             print(f"Please place your background video in the '{BACKGROUND_VIDEO_DIR}' folder and name it '{BACKGROUND_VIDEO_FILENAME}'.")

    else:
        print("Timestamp generation failed or was skipped. Cannot proceed to Video Generation.")

    # --- Final Summary ---
    print("\n--- Script Summary ---")
    print(f"Script Generated: {'Yes' if generated_script else 'No'}")
    print(f"Audio Generated: {'Yes' if audio_generated else 'No'}")
    print(f"Timestamps Generated: {'Yes' if timestamp_segments is not None else 'No'}") # Check if None
    print(f"Final Video Generated: {'Yes' if video_generated else 'No'}")
    if video_generated:
        print(f"Output video saved to: {os.path.join(OUTPUT_VIDEO_DIR, OUTPUT_VIDEO_FILENAME)}")

    print("\nScript finished.")