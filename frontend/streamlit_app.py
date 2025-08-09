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

