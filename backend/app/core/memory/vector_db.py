import logging
import chromadb
from pathlib import Path
from chromadb.utils import embedding_functions
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class VectorDB:
    def __init__(self, collection_name: str = "japanese_audio_memory"):
        self.settings = get_settings()
        
        # Ensure absolute path to backend/storage/vector_db
        base_dir = Path(__file__).parent.parent.parent.parent
        db_path = base_dir / "storage" / "vector_db"
        db_path.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(db_path))
        
        # Use Google Generative AI for embeddings
        if self.settings.GOOGLE_API_KEY:
            self.embedding_fn = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
                api_key=self.settings.GOOGLE_API_KEY
            )
        else:
            logger.warning("GOOGLE_API_KEY not found. Falling back to default embeddings.")
            self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn
        )

    async def add_documents(self, ids: list[str], documents: list[str], metadatas: list[dict] = None):
        """Add documents to the vector database."""
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    async def query(self, query_texts: list[str], n_results: int = 5, where: dict = None):
        """Query the vector database for similar documents."""
        return self.collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where
        )

    async def delete(self, ids: list[str]):
        """Delete documents by ID."""
        self.collection.delete(ids=ids)
