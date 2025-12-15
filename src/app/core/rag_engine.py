import uuid
import chromadb
from chromadb.utils import embedding_functions
from app.config import CHROMA_PATH

# 初始化
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
collection = chroma_client.get_or_create_collection(
    name="root_library",
    embedding_function=emb_fn
)

def add_text_to_rag(filename: str, text: str):
    chunk_size = 500
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    if not chunks: return 0

    ids = [f"{filename}_{i}_{uuid.uuid4().hex[:4]}" for i in range(len(chunks))]
    metadatas = [{"source": filename} for _ in range(len(chunks))]

    collection.add(documents=chunks, metadatas=metadatas, ids=ids)
    return len(chunks)

def query_rag_with_filter(query: str, allowed_files: list, n_results: int = 3):
    if not allowed_files: return ""
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"source": {"$in": allowed_files}}
    )
    docs = results['documents'][0]
    return "\n---\n".join(docs) if docs else ""

def delete_from_rag(filename: str):
    collection.delete(where={"source": filename})

def rename_in_rag(old_name: str, new_name: str):
    existing_records = collection.get(where={"source": old_name})
    if existing_records['ids']:
        ids_to_update = existing_records['ids']
        new_metadatas = [{"source": new_name} for _ in ids_to_update]
        collection.update(ids=ids_to_update, metadatas=new_metadatas)