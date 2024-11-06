import faiss
import tiktoken
import requests
import io
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
import fitz  # PyMuPDF
import json

OPENAI_API_KEY = "your_api_key"

client = OpenAI(api_key=OPENAI_API_KEY)

def save_json(data, filename):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def extract_contents_from_pdf(pdf_path):
    # Open the PDF file
    document = fitz.open(pdf_path)
    total_contents = ""

    # Loop through each page in the PDF
    for page_num in range(len(document)):
        page = document.load_page(page_num)  # Load a page
        text = page.get_text()  # Extract text
        total_contents += text + "\n"  # Append text to total_contents

    document.close()
    return total_contents  # Return total contents

def clean_text(text):
    return text.replace('\n', ' ').replace('\r', ' ').strip()

def num_tokens_from_string(string: str, encoding_name: str) -> int:
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def split_text_into_token_chunks(text, max_tokens, encoding_name="cl100k_base"):
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i+max_tokens]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
    return chunks

def index_embeddings(embeddings):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

def retrieve_similar_chunks(index, query_embedding, texts, top_k=10):
    distances, indices = index.search(np.array([query_embedding]), top_k)
    return [texts[i] for i in indices[0]]
def generate_embeddings(texts):
    embeddings = []
    max_token_length = 8191
    for text in texts:
        num_tokens = num_tokens_from_string(text, "cl100k_base")
        if num_tokens > max_token_length:
            sub_texts = split_text_into_token_chunks(text, max_token_length)
            for sub_text in sub_texts:
                response = client.embeddings.create(input=sub_text, model="text-embedding-3-large").data[0].embedding
                embeddings.append(response)
        else:
            response = client.embeddings.create(input=text, model="text-embedding-3-large").data[0].embedding
            embeddings.append(response)
    return np.array(embeddings)

def generate_structured_outputs(chunks):
    # Combine all chunks to ensure all details are included
    combined_text = ' '.join(chunks)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an intelligent assistant that understands human medical form inputs. Given the following transcript of patient details:"},
            {"role": "user", "content": combined_text},
            {"role": "user", "content": """
                Guidelines:
                1) Answer format must be json format only.
                2) Fill the json format according to the description.
                3) Don't include the description in final output json. Description is for reference only.
                4) Write "null" if there's no information or you are confused.
                5) Include every detail. Don't skip anything.
                6) Recheck if everything is correctly retrieved. Every ingredient, notes, procedure is mentioned.

                Response format:
                {
                    "type": "object",
                    "properties": {
                    "Name": {
                        "type": "string",
                        "description": "The name of the final product, indicating its purpose or function."
                    },
                    "Formula": {
                        "type": "array",
                        "items": {
                        "type": "object",
                        "properties": {
                            "IngredientName": {
                            "type": "string",
                            "description": "The specific name of each ingredient used in the formulation."
                            },
                            "Amount": {
                            "type": "string",
                            "description": "The precise quantity of the ingredient required, expressed in appropriate units (e.g., grams, milliliters)."
                            }
                        },
                        "required": ["IngredientName", "Amount"]
                        },
                        "description": "A list of ingredients along with their corresponding amounts needed to create the final product."
                    },
                    "Procedure": {
                        "type": "array",
                        "items": {
                        "type": "object",
                        "properties": {
                            "Step": {
                            "type": "integer",
                            "description": "The sequential number indicating the order of steps in the preparation process."
                            },
                            "Instruction": {
                            "type": "string",
                            "description": "A detailed description of the actions to be performed at this step, including any specific techniques or precautions."
                            }
                        },
                        "required": ["Step", "Instruction"]
                        },
                        "description": "A step-by-step guide outlining the process to prepare the final product, ensuring clarity and ease of understanding."
                    },
                    "Notes": {
                        "type": "array",
                        "items": {
                        "type": "string",
                        "description": "Supplementary information, tips, or considerations related to the formulation or procedure that may enhance understanding or effectiveness."
                        },
                        "description": "Additional notes that provide context, clarification, or helpful hints regarding the product or its preparation."
                    },
                    "Literature": {
                        "type": "array",
                        "items": {
                        "type": "string",
                        "description": "References related to the formulation, use, or effectiveness of the product."
                        },
                        "description": "A list of references providing background or evidence for the formulation."
                    }
                    },
                    "required": ["Name", "Formula", "Procedure"]
                }
                
            """}
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    pdf_path = 'ABHR CREAM.pdf'
    text = extract_contents_from_pdf(pdf_path)

    cleaned_text = clean_text(text)
    chunks = split_text_into_token_chunks(cleaned_text, 4000)

    embeddings = generate_embeddings(chunks)
    index = index_embeddings(embeddings)

    query_embedding = generate_embeddings([cleaned_text[:8191]])[0]  
    similar_chunks = retrieve_similar_chunks(index, query_embedding, chunks)

    # Generate structured output from all similar chunks
    structured_output = generate_structured_outputs(similar_chunks)
    print(structured_output)
