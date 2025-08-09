import streamlit as st
import requests
import json
import time 
from typing import Optional 

API_BASE_URL = "http://localhost:8000" # Update with your API base URL

class RAGSystemUI:
    def __init__(self):
        self.token = None
        if 'token' in st.session_state:
            self.token = st.session_state.token

    def authenticate(self, username: str, password: str) -> bool:
        try: 
            response = requests.post(
                f"{API_BASE_URL}/auth/token",
                params={"username": username, "password": password}
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                st.session_state.token = self.token
                return True
            return False
        
        except Exception as e:
            st.error(f"Authentication failed: {str(e)}")
            return False
        
    def upload_document(self, file) -> bool:
        if not self.token:
            st.error("You must be authenticated to upload documents.")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            files = {"file": (file.name, file, file.type)}

            with st.spinner("Uploading and processing document..."):
                response = requests.post(
                    f"{API_BASE_URL}/documents/upload",
                    headers=headers,
                    files=files
                )

            if response.status_code == 200:
                st.success("Document uploaded and processed successfully.")
                return True
            else:
                st.error(f"Failed to upload document: {response.text}")
                return False
            
        except Exception as e:
            st.error(f"Error uploading document: {e}")
            return False
        
    def query_documents(self, question: str) -> Optional[dict]:
        if not self.token:
            st.error("You must be authenticated to query documents.")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }

            data = {
                "question": question,
                "max_results": 3
            }

            with st.spinner("Querying documents..."):
                response = requests.post(
                    f"{API_BASE_URL}/query",
                    headers=headers,
                    json=data
                )

            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to query documents: {response.text}")
                return None
            
        except Exception as e:
            st.error(f"Error querying documents: {e}")
            return None
        
    def get_documents_list(self) -> Optional[list]:
        if not self.token:
            return None
        
        try: 
            headers = {"Autorization": f"Bearer {self.token}"}
            response = requests.get(
                f"{API_BASE_URL}/documents",
                headers=headers
            )

            if response.status_code == 200:
                return response.json().get("documents", [])
            return []
        
        except Exception as e:
            st.error(f"Error retrieving documents list: {e}")
            return []
        
def main():
    st.set_page_config(
        page_title = "Enterprise RAG System",
        page_icon = "📄",
        layout = "wide"
    )

    ui = RAGSystemUI()

    st.sidebar.title("Enterprise RAG System")
    st.sidebar.markdown("---")

    if not ui.token:
        st.sidebar.subheader("Authentication")
        username = st.sidebar.text_input("Username", value="demo")
        password = st.sidebar.text_input("Password", type="password", value="demo123")

        if st.sidebar.button("Login"):
            if ui.authenticate(username, password):
                st.success("Login successful!")
            else:
                st.error("Invalid credentials. Please try again.")

        else:
            st.siderbar.success("Authenticated")
            if st.sidebar.button("Logout"):
                del st.session_state.token
                st.rerun()

        if ui.token:
            st.header("Document Management")
            col1, col2 = st.columns([2, 1])

            with col1:
                uploaded_file=st.file_uploader(
                    "Upload documents (PDF, DOCX, TXT)",
                    type=["pdf", "docx", "txt"],
                    help = "Upload your documents for processing and to be added into the knowledge base"
                )

                if uploaded_file and st.button("Process Document"):
                    if ui.upload_document(uploaded_file):
                        st.success(f"Document '{uploaded_file.name}' uploaded successfully.")
                        time.sleep(1)
                        st.rerun()

            with col2:
                st.subheader("Document Statistics")
                docs = ui.get_documents_list()
                if docs:
                    st.metric("Total Documents", len(docs))
                    with st.expander("View Documents"):
                        for doc in docs[:10]: # Display only first 10 documents, you can edit this
                            st.text(f"- {doc['name']} (ID: {doc['id']})")
                else:
                    st.metric("No documents found. Please upload some documents to get started.")

            st.markdown("---")

            st.header("Ask Questions")

            if "message" not in st.session_state:
                st.session_state.message = []

                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
                        if message["role"] == "assistant" and "sources" in message:
                            with st.expander("Sources"):
                                for i, source in enumerate(message["sources"], 1):
                                    st.text(f"{i}. {source['content'][:200]}...")
                
                if prompt := st.chat_input("Ask a question about your documents..."):
                    st.session_state.message.append({"role": "user", "content": prompt})

                    with st.chat_message("user"):
                        st.markdown(prompt)

                    with st.chat_message("assistant"):
                        result=ui.query_documents(prompt)

                        if result:
                            response = result["answer"]
                            confidence = result["confidence"]
                            sources = result["sources"]

                            st.markdown(f"**Answer (Confidence: {confidence:.2%}):**")
                            st.markdown(response)

                            if sources:
                                with st.expander("Sources"):
                                    for i, source in enumerate(sources, 1):
                                        st.text(f"{i}. {source['content'][:200]}...")

                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response,
                                "sources": sources
                            })

                        else:
                            error_msg = "Sorry, I couldn't process your question. Please try again."
                            st.error(error_msg)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": error_msg
                            })
                
                st.sidebar.markdown("---")
                st.sidebar.subheader("System Status")

                try:
                    response = requests.get(f"{API_BASE_URL}/health")
                    if response.status_code == 200:
                        health = response.json()
                        st.sidebar.success("System is running smoothly!")

                        aws_status = health.get("services", {}).get("aws", {})
                        s3_status = "✅" if aws_status.get("s3") else "❌"
                        lambda_status = "✅" if aws_status.get("lambda") else "❌"

                        st.sidebar.text(f"S3 Status: {s3_status}")
                        st.sidebar.text(f"Lambda Status: {lambda_status}")
                    else:
                        st.sidebar.error("System health check failed.")
                except:
                    st.sidebar.error("API Unreachable")

            else:
                st.title("🤖 Enterprise RAG System")
                st.markdown("""
                ## Welcome to the Enterprise RAG System
                
                This system demonstrates:
                - **Retrieval-Augmented Generation (RAG)** using LangChain
                - **Document Processing** with multiple formats
                - **AWS Services Integration** (LocalStack simulation)
                - **Secure Authentication** with JWT tokens
                - **Vector Search** with ChromaDB
                - **Microservices Architecture** with FastAPI
                
                **Demo Credentials:**
                - Username: `demo`
                - Password: `demo123`
                
                Please authenticate in the sidebar to get started.
                """)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.subheader("RAG Technology")
                    st.markdown("""
                        - Document chunking and embedding
                        - Semantic search with vector database
                        - Context-aware answer generation
                        - Source attribution and confidence scoring
                        """)
                    
                with col2:
                    st.subheader("AWS Integration")
                    st.markdown("""
                    - S3 for document storage
                    - Lambda for processing
                    - LocalStack for development
                    - Scalable microservices architecture
                    """)

                with col3:
                    st.subheader("Security Features")
                    st.markdown("""
                    - JWT authentication
                    - Rate limiting
                    - Input validation and sanitization
                    - Secure file handling
                    """)

if __name__ == "__main__":
    main()

