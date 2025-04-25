# Automated Story Video Generator

## Features

- **AI Story Generation:** Uses Ollama (locally) to generate short, viral-style stories with twists based on a user-provided idea.
- **Text-to-Speech (TTS):** Converts the generated script into an audio file using OpenAI's TTS API.
- **Word-Level Timestamps:** Transcribes the audio using `whisper-timestamped` to get precise timings for each word.
- **Video Creation:** Combines a background video clip with the generated audio and synchronized captions using `moviepy`.
- **Customizable Captions:** Offers options for caption styling (font, size, color, stroke) and display mode (word grouping or one word at a time).

## Requirements

- **Python 3.12**
- **Ollama:** Must be installed and running locally. Ensure the desired model (e.g., `mistral`) is pulled (`ollama pull mistral`).
- **OpenAI API Key:** Required for the Text-to-Speech functionality.
- **FFmpeg:** Must be installed and available in the system's PATH. Used by `whisper-timestamped` and `moviepy`.
  - macOS (Homebrew): `brew install ffmpeg`
  - Debian/Ubuntu: `sudo apt update && sudo apt install ffmpeg`
- **ImageMagick:** Required by `moviepy` for creating text captions. Ensure the path is correctly set in `main.py` if necessary.
  - macOS (Homebrew): `brew install imagemagick`
  - Debian/Ubuntu: `sudo apt update && sudo apt install imagemagick`
- **Python Libraries:** Install using the provided `requirements.txt` file, preferably with `uv`.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd SocialPosting
    ```
2.  **Install Python dependencies (using `uv`):**
    ```bash
    uv pip install -r requirements.txt
    ```
3.  **Install FFmpeg and ImageMagick:** Follow the instructions in the [Requirements](#requirements) section for your operating system.
4.  **Set up Environment Variables:**
    - Create a file named `.env` in the project root directory.
    - Add your OpenAI API key to the `.env` file:
      ```
      OPENAI_API_KEY="your_openai_api_key_here"
      ```
5.  **Configure ImageMagick Path (if needed):**
    - If `moviepy` cannot find ImageMagick, you might need to explicitly set the path within `main.py`. Locate the following line and adjust the path according to your installation:
      ```python
      change_settings({"IMAGEMAGICK_BINARY": r"/path/to/your/magick"})
      ```
      (The current example path `/opt/homebrew/bin/magick` is common for Homebrew on Apple Silicon).

## Configuration (in `main.py`)

Adjust the following constants at the top of `main.py` to customize the script's behavior:

- `LOCAL_LLM_PROVIDER`: Set to `"ollama"`.
- `OLLAMA_MODEL`: Specify the Ollama model to use (e.g., `"mistral"`).
- `TEMP_AUDIO_FILENAME`: Name for the temporary audio file.
- `WHISPER_MODEL_SIZE`: Choose the Whisper model size (`"tiny"`, `"base"`, `"small"`, `"medium"`, `"large"`). Larger models are more accurate but require more resources.
- `WHISPER_DEVICE`: Set to `"cpu"` or `"cuda"`/`"mps"` (GPU). `"cpu"` is generally more reliable.
- `BACKGROUND_VIDEO_DIR`: Folder containing background videos.
- `BACKGROUND_VIDEO_FILENAME`: The specific background video file to use.
- `OUTPUT_VIDEO_DIR`: Folder where the final video will be saved.
- `OUTPUT_VIDEO_FILENAME`: Name for the generated video file.
- `CAPTION_FONT`, `SINGLE_CAPTION_FONTSIZE`, `MULTI_CAPTION_FONTSIZE`, `CAPTION_COLOR`, `CAPTION_STROKE_COLOR`, `CAPTION_STROKE_WIDTH`: Customize the appearance of captions.
- `ENABLE_WORD_GROUPING`: Set to `True` for grouped captions, `False` for word-by-word.

## Usage

1.  **Add Background Video:** Place video file(s) into the `background_videos` directory (create it if needed). Ensure `BACKGROUND_VIDEO_FILENAME` in `main.py` matches the desired video.
2.  **Run the script:**
    ```bash
    python main.py
    ```
3.  **Modify Story Idea (Optional):** Change the `story_idea` variable in `main.py` or uncomment the `input()` line.
4.  **Check Output:** Files generated include:
    - `script.txt`
    - `temp_story_audio.mp3`
    - `temp_story_audio_timestamps.json` (debug info)
    - `word_timestamps.txt`
    - `output_videos/final_story_video.mp4` (final video)

## Troubleshooting

- **Ollama Connection Error:** Ensure the Ollama server is running.
- **OpenAI Authentication Error:** Check your `.env` file and API key.
- **`ffmpeg` Not Found:** Verify FFmpeg installation and PATH.
- **ImageMagick Error:** Check installation and `main.py` path setting.
- **Whisper Errors:** Ensure `ffmpeg` is installed. Try `"cpu"` device for stability.
