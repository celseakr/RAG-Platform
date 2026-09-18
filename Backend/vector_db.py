import chromadb
from chromadb.utils import embedding_functions
from pypdf import PdfReader
import nltk
nltk.download ('punkt_tab') #a pretrained model that knows how to split text into sentences
from nltk.tokenize import  sent_tokenize
import os
import uuid


# 1. Initialise local persistent databse storage
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# 2. Configure ChromaDB to use your local Ollama embedding engine
ollame_ef = embedding_functions.OllamaEmbeddingFunction(
    model_name="nomic-embed-text"
)

# 3. Create or load a vector Collection
collection = chroma_client.get_or_create_collection(
    name="my_first_collection",
    embedding_function=ollame_ef
)

#ingestion
def index_pdf(file_path):

    #Tags the data by file
    file_name = os.path.basename(file_path)

    #1. loading pdf
    pdf_pages =load_pdf(file_path) 

    #2. chunking text
    sample_documents, metadata = prepare_chunks_with_metadata(pdf_pages,file_name) 

    print(f"Total chunks created: {len(sample_documents)}")

    #3. Create unique IDs for each text snippet
    document_ids = [
        f"{file_name}_{uuid.uuid4()}_{i}"
        for i in range(len(sample_documents))] # now this becomes file1.pdf_chunk_0, file1.pdf_chunk_1, file2.pdf_chunk_0

    # 5. Convert text to vectors and save to database; Generating vector embeddings and saving to chromaDB
    collection.add(
        documents =sample_documents,
        ids = document_ids,
        metadatas=metadata
    )
    return


#Delete PDF
def delete_pdf(file_name):
    collection.delete(
        where ={"file":file_name}
    )


# Read pdf
def load_pdf(file_name):
    reader = PdfReader(file_name) #uses PDFreader from pydf to open the PDF
    pages = []

    for page_num, page in enumerate(reader.pages): #PDf alrdy knows what its pages are, Python isnt inventing them, PyPDF stores them in reader.pages
        page_text = page.extract_text() #extract text from each page

        if page_text:
            pages.append({
                "page": page_num + 1,
                "text": page_text 
                })
        
    return pages


# Chunk texts by sentences
def chunk_text(text, max_char=500): #input:big text, output: smaller texts, each chunk is a max of 500 characters
    sentences=sent_tokenize(text)
    chunks = []
    current_chunk = ""  #temporary storage while working, add chunks here until they get to 500 max chars and then save it to chunks

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= max_char: #if adding the sentence doesnt exceed 500 characters
            current_chunk+= " " + sentence #keep adding to it, append sentence into current chunk
        else:
            chunks.append(current_chunk.strip()) #if it doesnt fit, save current chunk
            current_chunk = sentence #start new chunk with this sentence

    if current_chunk: #if there's still a last chunk after the loop ends, save that chunk
        chunks.append(current_chunk.strip())

    return chunks
    
#Add Metadata to chunks, so you know which page each chunk comes from
def prepare_chunks_with_metadata(pdf_pages,file_name): 

    all_chunks = []
    all_metadata = []

    for page_data in pdf_pages: #it's labeled pdf_pages bcs pdf_pages is the processed pdf defined at the bottom of the page

        page_chunks = chunk_text(page_data["text"])

        for chunk in page_chunks:
            all_chunks.append(chunk)

            all_metadata.append({
                "page": page_data["page"],
                "file": file_name,
                "file_id": file_name
            })

    return all_chunks, all_metadata

#Retrieval
def search_query(query, file_name, n_results=2):
    if not query:
        return {"documents": [[]], "distances": [[]], "metadatas": [[]]}

    return collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"file": file_name},
        include=["documents", "distances", "metadatas"]
    )

#helper for LLM
def retrieve_context(query, file_name):
    results = search_query(query, file_name)

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    return list(zip(docs, metas))


import ollama

def rag_answer(query, file_name):
    docs = retrieve_context(query, file_name)
    context = "\n\n".join(
        f"Page {m.get('page')}: {d}"
        for d, m in docs
    )
    
    prompt = f"""
You are a document assistant.

Use ONLY the supplied context.

If the answer cannot be found in the context,
respond with:

"I could not find this information in the document."

Always cite the page number when possible.

Context:
{context}

Question:
{query}

Answer:
"""

    #Call the model
    response = ollama.chat(
        model="llama3",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    #answer
    return response["message"]["content"]