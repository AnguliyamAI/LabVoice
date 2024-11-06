## VoiceBot with Speech Recognition, TTS, and Contextual Memory


This chatbot application allows users to interact with a conversational AI that utilizes speech recognition, text-to-speech (TTS), and contextual memory. Using advanced AI models for natural language processing, speech-to-text, and contextual responses, the bot creates an engaging and personalized experience for users. This application supports recording and transcribing audio input, retrieving relevant information, streaming responses, and generating and playing synthesized speech.

### Features
Speech Recognition: Converts user audio input into text using Whisper.
Text-to-Speech (TTS): Generates spoken responses using the Nix TTS model, making the chatbot more interactive.
Contextual Memory: Stores and retrieves information from a "vault" to provide more relevant responses based on past user inputs.
Streaming Responses: Streams responses from the OpenAI model for real-time interaction.
ANSI Coloring for Console: Highlights user and chatbot responses in different colors for better readability.
Requirements
To run this application, ensure you have the following libraries installed:

```bash
pip install torch pyaudio wave speechrecognition faster-whisper sentence-transformers openai numpy soundfile transformers
```

Additionally, make sure you have a CUDA-compatible GPU for optimal performance, as this application utilizes GPU acceleration.

### File Descriptions
xtalk.py: Main file to run the chatbot application.
vault.txt: Stores relevant information retrieved from past interactions, used for contextual responses.
chatbot2.txt: Contains the system message or instructions that define the chatbot's behavior.


### Setup
Install Required Libraries: Use the command above to install the necessary libraries.

- Set OpenAI API Key: Insert your OpenAI API key in the client = OpenAI(api_key="") line.
- make sure you have a CUDA-compatible GPU for optimal performance, as this application utilizes GPU acceleration.
- Install Espeak
   - Make sure you have cuda installed. [Guide](https://youtu.be/nATRPPZ5dGE?si=rlO_a1ETe5AyXWQg)
        - Install Espeak 
            - Go to [espeak-ng](https://github.com/espeak-ng/espeak-ng/releases)
            - Scroll down to assets
            - Do the Setup
            - Make sure you add paths to environment variablles
                ```bash
                PHONEMIZER_ESPEAK_PATH: c:\Program Files\eSpeak NG
                PHONEMIZER_ESPEAK_LIBRARY: c:\Program Files\eSpeak NG\libespeak-ng.dll
                ```
            - install Pytorch
                ```bash
                pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
                ```


### Usage

To start the voicebot, run the following command:

```bash

python xtalk.py
```


### Audio Recording:

record_audio(file_path): Records audio input and saves it as a WAV file.
Speech Recognition:

transcribe_with_whisper(audio_file): Transcribes recorded audio to text using the Whisper model.
Contextual Retrieval:

get_relevant_context(user_input, vault_embeddings, vault_content, model): Searches for relevant content based on user input.
Response Streaming:

chatgpt_streamed(): Streams responses from the chatbot using OpenAI's model.
Text-to-Speech (TTS):

process_and_play(prompt, audio_file_path): Converts chatbot responses into spoken audio.


### Troubleshooting
Audio Errors: Ensure pyaudio is installed and compatible with your system.
Model Loading Errors: Check your GPU compatibility and CUDA installation for Whisper and Nix models.
API Key: Make sure to include your OpenAI API key.
Credits
Developed using the following technologies:

OpenAI API for chatbot responses.
Faster Whisper for efficient speech-to-text.
Nix TTS for synthesized speech responses.
License
This project is for educational purposes. All model and API usage should comply with their respective licenses.
