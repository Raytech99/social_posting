import ollama

def generate_script_ollama(idea, model_name="mistral"): # Or specify a more precise model like "mistral:7b"
    print(f"Generating script with Ollama ({model_name})...")
    try:
        # Make sure Ollama server is running and the model is pulled/available
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": "You write very short, engaging stories under 400 words."},
                {"role": "user", "content": f"Write a story based on this idea: {idea}"}
            ]
        )
        script = response['message']['content']
        print(f"Script: {script}")
        return script
    except Exception as e:
        print(f"Error connecting to Ollama or generating script: {e}")
        print("Make sure the Ollama server is running and the model is available.")
        return None # Handle error appropriately
    
idea = "A suspenseful story about a woman who wakes up in a room with no memory of how she got there."
generate_script_ollama(idea)
