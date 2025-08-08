import os
from typing import List, Optional
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFacePipeline
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch
from app.core.config import settings
from app.core.security import SecurityService

class RAGService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
        model_name=settings.model_name,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
    )

        self.chroma_client = chromadb.PersistentClient(
        path=settings.chroma_persist_directory
    )

        self.vector_store = None
        self._initialize_vector_store()

        self.llm = self._initialize_llm()

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, #Keeping this small because I have a basic system but you can edit this to increase the chunk size
            chunk_overlap=50,
            length_function=len
        )

    def _initialize_vector_store(self):
        try:
            self.vector_store = Chroma(
                client=self.chroma_client,
                collection_name="documents",
                embedding_function=self.embeddings
            )
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            self.vector_store = Chroma(
                client=self.chroma_client,
                collection_name="documents",
                embedding_function=self.embeddings
            )        

    def _initialize_llm(self):
        try:
            model_name = "distilbert-base-uncased-distilled-squad"
            tokenizer = AutoTokenizer.from_pretrained(model_name)

            pipe = pipeline(
                "question-answering",
                model=model_name,
                tokenizer=tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )

            return pipe
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            return None
        
    async def add_documents(self, documents: List[str], metadata: List[dict] = None) -> bool:
        try:
            all_texts = []
            all_metadata = []

            for i, doc in enumerate(documents):
                doc = SecurityService.sanitize_input(doc)

                chunks = self.text_splitter.split_text(doc)
                all_texts.extend(chunks)

                doc_metadata = metadata[i] if i < len(metadata) else {}
                all_metadata.extend([{**doc_metadata, "chunk_id": j} for j in range(len(chunks))])

            self.vector_store.add_texts(
                texts=all_texts,
                metadatas=all_metadata
            )

            return True
        
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False

    async def query_documents(self, question: str, k: int = 3) -> List[dict]:
        try:
            question = SecurityService.sanitize_input(question)

            retriver = self.vector_store.as_retriever(search_kwargs={"k": k})
            relevant_docs = retriver.get_relevant_documents(question)

            if not relevant_docs:
                return {
                    "answer": "No relevant documents found.",
                    "sources": [],
                    "confidence": 0.0
                }
            
            context = "\n".join([doc.page_content for doc in relevant_docs])

            if self.llm:
                result = self.llm(question=question, context=context)
                answer = result['answer']
                confidence = result.get('score', 0.5)

            else:
                # Fallback to extractive QA if LLM is not available
                answer = self._extractive_answer(question, context)
                confidence = 0.5

            return {
                "answer": answer,
                "sources": [{"content": doc.page_content, "metadata": doc.metadata} 
                            for doc in relevant_docs],
                "confidence": confidence
            }

        except Exception as e:
            print(f"Error querying documents: {e}")
            return{
                "answer": "Error processing query.",
                "sources": [],
                "confidence": 0.0
            }
    
    def _extractive_answer(self, question: str, context: str) -> str:
        question_words = question.lower().split()
        context_sentences = context.split('. ')

        best_sentence = ""
        max_matches = 0

        for sentence in context_sentences:
            sentence_words = sentence.lower().split()
            matches = sum(1 for word in question_words if word in sentence_words)

            if matches > max_matches:
                max_matches = matches
                best_sentence = sentence.strip()

        return best_sentence if best_sentence else "No answer found in the context."
    

    async def get_document_stats(self) -> dict:
        try:
            collection = self.chroma_client.get_collection("documents")
            count = collection.count()

            return {
                "total_documents": count,
                "collection_name": "documents",
            }
        except Exception as e:
            print(f"Error getting document stats: {e}")
            return {
                "total_documents": 0,
                "collection_name": "documents",
            }