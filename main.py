from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
import os
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
import pandas as pd
from langchain.retrievers.multi_query import MultiQueryRetriever
from pdf2image import convert_from_path
import streamlit as st
import pytesseract

genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
def extract_text_from_pdf(pdf_path):
    # Convert PDF to images
    pages = convert_from_path(pdf_path, 300)

    # Iterate through all the pages and extract text
    extracted_text = ''
    for page_number, page_data in enumerate(pages):
        # Perform OCR on the image
        if(page_number >= 5):
            text = pytesseract.image_to_string(page_data)
            extracted_text += f"Page Number : {page_number + 1} \n\n{text}\n"
        if(page_number == 28):
            break
    return extracted_text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=20)
    return text_splitter.split_text(text)

def get_vector_store(text_chunks, batch_size=100):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    text_embeddings = []
    
    for i in range(0, len(text_chunks), batch_size):
        batch = text_chunks[i:i + batch_size]
        batch_embeddings = embeddings.embed_documents(batch)
        text_embeddings.extend(zip(batch, batch_embeddings))
    
    vector_store = FAISS.from_embeddings(text_embeddings, embedding=embeddings)
    vector_store.save_local("Faiss_Index_BOOK1")
    return vector_store

def create_embeddings():
    url_text_chunks = []
    article_text = extract_text_from_pdf('The Smart Branding Book.pdf')
    text_chunks = get_text_chunks(article_text)
    for chunk in text_chunks:
        url_text_chunks.append(f"{chunk}")
    get_vector_store(url_text_chunks)

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    prompt_template = """
    Answer the question from the context provided.Explain in as much details as possible.
    Context:\n{context}?\n
    Question:\n{question} + Explain in detail.\n
    Answer:
    """
    model = ChatGoogleGenerativeAI(model="gemini-1.0-pro", temperature=0.5)
    # repo_id="mistralai/Mistral-7B-Instruct-v0.2"
    # model=HuggingFaceEndpoint(repo_id=repo_id,max_length=128,temperature=0.7,token=sec_key)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
      # Model for creating vector embeddings
    new_db = FAISS.load_local("Faiss_Index_BOOK1", embeddings, allow_dangerous_deserialization=True)  # Load the previously saved vector db
    mq_retriever = MultiQueryRetriever.from_llm(retriever = new_db.as_retriever(search_kwargs={'k': 2}), llm = model )
    docs1 = mq_retriever.get_relevant_documents(query=user_question)
    # docs1 = new_db.similarity_search(user_question)

    response = chain({"input_documents": docs1, "question": user_question}, return_only_outputs=True)
    return response , docs1

def main():
    create_embeddings()

if __name__ == "__main__":
    main()