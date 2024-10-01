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

import fitz  # PyMuPDF

def extract_pdf_text(pdf_path):
    """
    Extracts text from a PDF file and returns it as a list with the book name and page numbers.
    
    Args:
        pdf_path (str): The path to the PDF file.
        
    Returns:
        list: A list of formatted strings containing the book name, page number, and text.
    """
    # Extract the book name from the PDF file path (removing the '.pdf' extension)
    book_name = pdf_path.replace('.pdf', '')
    
    # Open the PDF file
    pdf_document = fitz.open(pdf_path)
    extracted_text = []

    # Iterate through each page in the PDF
    for page_num in range(len(pdf_document)):
        # Load the page
        page = pdf_document.load_page(page_num)

        # Extract text from the page
        text = page.get_text("text")

        # Format the extracted text with page number and book name
        formatted_text = f"""Book: {book_name}, Page Number - {page_num + 1}, {text.strip()}"""
        extracted_text.append(formatted_text)

    return extracted_text



def create_question_embeddings_from_excel(excel_path, sheet_name='Sheet1'):
    """
    Reads an Excel file, creates embeddings of each question from the 2nd row onwards,
    and saves the embeddings in a FAISS vector database.

    Args:
        excel_path (str): Path to the Excel file.
        sheet_name (str): The name of the sheet in the Excel file to read. Default is 'Sheet1'.

    Returns:
        FAISS: The FAISS vector store with question embeddings.
    """
    # Load the Excel file
    df = pd.read_excel(excel_path, sheet_name=sheet_name)

    # Assuming the first column contains the questions
    questions = df.iloc[1:, 0].tolist()  # Skip the first row (header) and get questions from the first column

    # Initialize the embeddings model
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    # Create embeddings for each question in batches
    question_embeddings = []
    batch_size = 100
    for i in range(0, len(questions), batch_size):
        batch = questions[i:i + batch_size]
        batch_embeddings = embeddings.embed_documents(batch)
        question_embeddings.extend(zip(batch, batch_embeddings))

    # Save the embeddings to a FAISS vector store
    vector_store = FAISS.from_embeddings(question_embeddings, embedding=embeddings)
    vector_store.save_local("FAISS_INDEX_Questions")

    return vector_store

# Example usage:
# extracted_text_list = []
# pdf_files = ["The Smart Branding Book.pdf" ,"The Smart Advertising Book FINAL v2 PDF.pdf" , "The Smart Marketing Book v24 PDF.pdf","The Soft Skills Book PDF.pdf" ]  # Specify your PDF file path
# for pdf_file in pdf_files :
#     extracted_text_list.extend(extract_pdf_text(pdf_file))
# extracted_text_list = extract_pdf_text('The Soft Skills Book PDF.pdf')

# # Print or process the extracted text
# for page_text in extracted_text_list:
#     print(page_text)
#     print("\n" + "-" * 50 + "\n")  # Just for separation between pages

# print(len(extracted_text_list))
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
# text_embeddings = []
# batch_size = 100 
# text_chunks = extracted_text_list
# for i in range(0, len(text_chunks), batch_size):
#     batch = text_chunks[i:i + batch_size]
#     batch_embeddings = embeddings.embed_documents(batch)
#     text_embeddings.extend(zip(batch, batch_embeddings))

# vector_store = FAISS.from_embeddings(text_embeddings, embedding=embeddings)
# vector_store.save_local("FAISS_INDEX_The_Soft_Skills_Book")
create_question_embeddings_from_excel('Questions_Dan_White.xlsx')