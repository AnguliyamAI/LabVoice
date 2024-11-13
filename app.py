import os
import wave
import pyaudio
import argparse
import torch
from openai import OpenAI
from faster_whisper import WhisperModel
from sentence_transformers import SentenceTransformer,util
import soundfile as sf
import numpy as np
import torch


from nix.models.TTS import NixTTSInference
import json
nix = NixTTSInference(model_dir="nix-ljspeech-deterministic-v0.1")


## ANSI escape codes for colors
PINK='\033[95m'
CYAN='\033[96m'
YELLOW='\033[93m'
NEON_GREEN='\033[92m'
RESET_COLOR='\033[0m'


## set up faster-whisper model
model_size="medium.en"
device='cuda' if torch.cuda.is_available() else 'cpu'
whisper_model=WhisperModel(model_size,device=device,compute_type="float16")

with open('Lorazepam.json', 'r') as file:
    data = json.load(file)

def open_file(filepath):
    """
    Opens and reads the content of a file.
    """
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()

client = OpenAI(api_key="         ")

def play_audio(filepath):
    try:
        wf = wave.open(filepath, 'rb')
    except wave.Error as e:
        print(f"Error opening WAV file: {e}")
        return

    p = pyaudio.PyAudio()

    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    data = wf.readframes(1024)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(1024)

    stream.stop_stream()
    stream.close()
    p.terminate()
    wf.close()

parser=argparse.ArgumentParser()
parser.add_argument("--share",action="store_true",default=False,help="make link public")
args=parser.parse_args()

device='cuda' if torch.cuda.is_available() else 'cpu'
output_dir='outputs'
os.makedirs(output_dir,exist_ok=True)

def process_and_play(prompt,audio_file_path):
    try:
        text=prompt
        max_length = 100
        text_chunks = [text[i:i + max_length] for i in range(0, len(text), max_length)]

        all_audio_chunks = []

        for chunk in text_chunks:
            c, c_length, phoneme = nix.tokenize(chunk)

            xw = nix.vocalize(c, c_length)

            all_audio_chunks.append(xw[0, 0])

        combined_audio = np.concatenate(all_audio_chunks)

        src_path=f'{output_dir}/output1.wav'

        sf.write(src_path,combined_audio, 22050)

        print("Audio Generated successfully")
        play_audio(src_path)
    except Exception as e:
        print(f"Error occurred: {e}")

def get_relevant_context(user_input,vault_embeddings,vault_content,model,top_k=3):
    """
    Extracts relevant context from the user's input based on the provided mode and vault content.
    """
    if vault_embeddings.nelement()==0:
        return []
    input_embeddings =model.encode([user_input])
    cos_scores=util.cos_sim(input_embeddings,vault_embeddings)[0]
    top_k=min(top_k,len(cos_scores))
    top_indices=torch.topk(cos_scores,k=top_k)[1].tolist()

    relevant_content=[vault_content[idx].strip() for idx in top_indices]

    return relevant_content

def chatgpt_streamed(user_input,system_message,conversation_history,bot_name,vault_embeddings,vault_content,model):
    """
    Performs a chatbot conversation with the user, incorporating the provided system message, conversation history,
    bot name, and relevant context.
    """

    streamed_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"system","content":system_message}]+conversation_history+[{"role":"user","content":f"Given the following context: {data}, answer the following question: {user_input}."}],
        temperature=0.9,
        max_tokens=1024,
    )
    full_response=streamed_completion.choices[0].message.content

    print(NEON_GREEN+full_response+RESET_COLOR)
    return full_response

def transcribe_with_whisper(audio_file):
    segments,info=whisper_model.transcribe(audio_file,beam_size=5)
    transcription=""
    for segment in segments:
        transcription+=segment.text+" "
    return transcription.strip()

def record_audio(file_path):
    p=pyaudio.PyAudio()
    stream=p.open(format=pyaudio.paInt16,channels=1,rate=16000,input=True,frames_per_buffer=1024)
    frames=[]
    print("Recording ...")
    try:
        while True:
            data=stream.read(1024)
            if not data:
                break
            frames.append(data)
    except KeyboardInterrupt:
        pass
    print("Recording stopped")
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf=wave.open(file_path,"wb")
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()
    print("Audio saved to",file_path)


def user_chatbot_conversation():
    """
    Main function to handle the user-chatbot conversation.
    """
    print("processing conversation ... ")
    conversation_history=[]
    system_message=open_file("chatbot2.txt")
    model=SentenceTransformer("all-MiniLM-L6-v2")
    vault_content=[]
    if os.path.exists("vault.txt"):
        with open("vault.txt","r",encoding="utf-8") as vault_file:
            vault_content=vault_file.readlines()
    vault_embeddings=model.encode(vault_content) if vault_content else []
    vault_embeddings_tensor=torch.tensor(vault_embeddings)
    start=input(CYAN+"Enter START :"+RESET_COLOR)
    while True:
        audio_file="temp_recording.wav"
        record_audio(audio_file)
        user_input=transcribe_with_whisper(audio_file)
        os.remove(audio_file)
        if user_input.lower().startswith(("exit")):
            break
        print(CYAN+"You: ",user_input+RESET_COLOR)
        conversation_history.append({"role":"user","content":user_input})
        print(PINK+"Emma: "+RESET_COLOR)
        chatbot_response=chatgpt_streamed(user_input,system_message,conversation_history,"Chatbot",vault_embeddings_tensor,vault_content,model)
        conversation_history.append({"role":"assistant","content":chatbot_response})
        prompt2=chatbot_response
        audio_file_pth2="emm2.wav"
        process_and_play(prompt2,audio_file_pth2)
        if len(conversation_history)>20:
            conversation_history=conversation_history[-20:]

if __name__=="__main__":
    user_chatbot_conversation()

