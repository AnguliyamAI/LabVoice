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
                    "Title": {
                        "type": "string",
                        "description": "The title of the SOP document."
                    },
                    "SOPNumber": {
                        "type": "string",
                        "description": "The unique identification number for the SOP."
                    },
                    "VersionNumber": {
                        "type": "string",
                        "description": "The version number of the SOP document."
                    },
                    "PURPOSE": {
                        "type": "object",
                        "properties": {
                        "Description": {
                            "type": "string",
                            "description": "The purpose or objective of the procedure."
                        }
                        },
                        "required": ["Description"]
                    },
                    "RESPONSIBILITY": {
                        "type": "object",
                        "properties": {
                        "Supervision": {
                            "type": "string",
                            "description": "The role(s) responsible for supervising the procedure."
                        },
                        "Personnel": {
                            "type": "string",
                            "description": "The staff responsible for performing the tasks outlined."
                        }
                        },
                        "required": ["Supervision", "Personnel"]
                    },
                    "REFERENCES": {
                        "type": "array",
                        "items": {
                        "type": "string",
                        "description": "Any SOPs or documents referenced for the procedure."
                        },
                        "description": "References for supporting documentation."
                    },
                    "DEFINITIONS": {
                        "type": "array",
                        "items": {
                        "type": "object",
                        "properties": {
                            "Term": {
                            "type": "string",
                            "description": "The term being defined."
                            },
                            "Definition": {
                            "type": "string",
                            "description": "The explanation or meaning of the term."
                            }
                        },
                        "required": ["Term", "Definition"]
                        },
                        "description": "Definitions of terms used within the procedure."
                    },
                    "FREQUENCY": {
                        "type": "object",
                        "properties": {
                        "Occurrence": {
                            "type": "string",
                            "description": "How often the procedure should be performed."
                        }
                        },
                        "required": ["Occurrence"]
                    },
                    "EQUIPMENT_SUPPLIES": {
                        "type": "array",
                        "items": {
                        "type": "string",
                        "description": "Equipment or supplies required to perform the procedure."
                        },
                        "description": "List of equipment and supplies necessary for the procedure."
                    },
                    "PROCEDURE": {
                        "type": "array",
                        "items": {
                        "type": "object",
                        "properties": {
                            "Section": {
                            "type": "string",
                            "description": "The title or topic of the section (e.g., Measurement System, Mixing)."
                            },
                            "Steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                "Subsection": {
                                    "type": "string",
                                    "description": "Subsection number (e.g., 7.1, 7.2)."
                                },
                                "Heading": {
                                    "type": "string",
                                    "description": "The heading of the subsection that describes its focus."
                                },
                                "Step": {
                                    "type": "string",
                                    "description": "The main description of the step within this subsection."
                                },
                                "Substeps": {
                                    "type": "array",
                                    "items": {
                                    "type": "object",
                                    "properties": {
                                        "SubstepNumber": {
                                        "type": "string",
                                        "description": "The substep number for detailed instruction (e.g., 7.1.1, 7.2.2.1)."
                                        },
                                        "Substep": {
                                        "type": "string",
                                        "description": "A detailed description of the substep."
                                        }
                                    },
                                    "required": ["SubstepNumber", "Substep"]
                                    },
                                    "description": "List of substeps associated with a particular step."
                                },
                                "AdditionalInfo": {
                                    "type": "array",
                                    "items": {
                                    "type": "object",
                                    "properties": {
                                        "InfoType": {
                                        "type": "string",
                                        "description": "The type of additional information (e.g., 'Note', 'Warning', 'Tip')."
                                        },
                                        "InfoContent": {
                                        "type": "string",
                                        "description": "The actual content of the additional information."
                                        }
                                    },
                                    "required": ["InfoType", "InfoContent"]
                                    },
                                    "description": "Additional information, notes, or warnings related to this step."
                                }
                                },
                                "required": ["Subsection", "Heading", "Step"]
                            }
                            }
                        },
                        "required": ["Section", "Steps"]
                        }
                    },
                    "ATTACHMENTS": {
                        "type": "array",
                        "items": {
                        "type": "string",
                        "description": "List of any attachments or supporting documents related to the procedure."
                        },
                        "description": "Attachments that provide additional information or details."
                    },
                    "HISTORY": {
                        "type": "object",
                        "properties": {
                        "Changes": {
                            "type": "array",
                            "items": {
                            "type": "object",
                            "properties": {
                                "Version": {
                                "type": "string",
                                "description": "Version number of the SOP."
                                },
                                "EffectiveDate": {
                                "type": "string",
                                "description": "Date when the SOP became effective."
                                },
                                "ChangeDescription": {
                                "type": "string",
                                "description": "Description of changes made in this version."
                                }
                            },
                            "required": ["Version", "EffectiveDate", "ChangeDescription"]
                            },
                            "description": "A history of changes to the SOP."
                        }
                        },
                        "required": ["Changes"]
                    }
                    }

                
            """}
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    pdf_path = 'CVLTC CMPD SAMPLE SOP 2.4 Measuring and Mixing.pdf'
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
