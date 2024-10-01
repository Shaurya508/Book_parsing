import streamlit as st
import pandas as pd
from main import user_input1, user_input2 , user_input3, user_input4
from io import BytesIO
from PIL import Image , UnidentifiedImageError
import requests
# from trial import translate
import re
# from Levenshtein import distance as levenshtein_distance
import os
import Levenshtein
# Define the maximum number of free queries
QUERY_LIMIT = 100

# Initialize session state for tracking the number of queries, conversation history, suggested questions, and authentication
if 'query_count' not in st.session_state:
    st.session_state.query_count = 0

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'suggested_question' not in st.session_state:
    st.session_state.suggested_question = ""

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'generate_response' not in st.session_state:
    st.session_state.generate_response = False

if 'chat' not in st.session_state:
    st.session_state.chat = ""


def extract_book_name_from_text(docs):
    """
    Extracts the book name from the given text in the format 'Book: <Book Name>, Page Number - X'.
    
    Args:
        text (str): The text containing the book name and page number.
        
    Returns:
        str: The extracted book name if found, otherwise None.
    """
    text = docs[0].page_content
    # Regular expression pattern to match "Book: <Book Name>," where <Book Name> is the book name
    pattern = r"Book:\s*(.+?)\s*,\s*Page Number"
    
    # Search for the pattern in the text
    match = re.search(pattern, text)
    
    # If a match is found, return the book name
    if match:
        return match.group(1).strip()  # Strip to remove any leading/trailing whitespace
    
    # If no match is found, return None
    return None

def extract_page_number_from_document(doc):
    # Access the page content from the Document object
    text = doc[0].page_content
    
    # Regular expression pattern to match "Page Number - X" where X is one or more digits
    pattern = r"Page Number\s*-\s*(\d+)"
    
    # Search for the pattern in the text
    match = re.search(pattern, text)
    
    # If a match is found, return the page number as an integer
    if match:
        return int(match.group(1))
    
    # If no match is found, return None or any other indication of no match
    return None

def extract_relevant_page_number(question, excel_sheet):
    """
    Extracts the most relevant page number from the Excel sheet based on the similarity 
    between the user's question and the text entries in the sheet using Levenshtein distance.

    Parameters:
    - question (str): The user's question.
    - excel_sheet (str): Path to the Excel sheet (e.g., 'Image_links.xlsx').

    Returns:
    - most_relevant_page (int or None): The page number with the highest similarity. 
      Returns None if no match is found.
    """
    try:
        # Load the Excel sheet into a DataFrame
        # If your Excel sheet has headers, pandas will automatically detect them.
        # If not, set header=None and assign column names manually.
        df = pd.read_excel(excel_sheet)
        
        # Check if the DataFrame has headers 'Text' and 'Page Number'
        if 'Text' in df.columns and 'Page Number' in df.columns:
            text_column = 'Text'
            page_number_column = 'Page Number'
        else:
            # If there are no headers, assume first column is text and second is page number
            df = pd.read_excel(excel_sheet, header=None)
            df.columns = ['Text', 'Page Number']
            text_column = 'Text'
            page_number_column = 'Page Number'
        
        # Initialize variables to keep track of the best match
        most_relevant_page = None
        highest_similarity = -1  # Initialize to -1 since similarity ranges from 0 to 1

        # Normalize the question for better comparison
        normalized_question = question.strip().lower()

        # Iterate through each row in the Excel sheet
        for index, row in df.iterrows():
            text = str(row[text_column]).strip().lower()  # Ensure text is string and normalized
            page_number = row[page_number_column]

            # Compute the Levenshtein distance
            distance = Levenshtein.distance(normalized_question, text)
            
            # Compute similarity as 1 / (1 + distance) to convert distance to similarity score between 0 and 1
            similarity = 1 / (1 + distance)

            # Update the most relevant page if this similarity is higher than previous ones
            if similarity > highest_similarity:
                highest_similarity = similarity
                most_relevant_page = page_number

        return most_relevant_page

    except FileNotFoundError:
        print(f"Error: The file '{excel_sheet}' was not found.")
        return None
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{excel_sheet}' is empty.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def clean_text(text):
    # Remove asterisks used for bold formatting
    text = re.sub(r'\*+', '', text)
    # Remove text starting from "For more details"
    text = re.sub(r'For more details.*$', '', text, flags=re.IGNORECASE)
    return text

def authenticate_user(email):
    # Load the Excel file
    df = pd.read_excel('user.xlsx')
    # Convert the input email to lowercase
    email = email.lower()
    # Convert the emails in the dataframe to lowercase
    df['Email'] = df['Email'].str.lower()
    # Check if the email matches any entry in the file
    user = df[df['Email'] == email]
    if not user.empty:
        return True
    return False

# def get_image_link(article_link, file_path='Linkidin_blogs.xlsx'):
#     # Load the Excel file
#     df = pd.read_excel(file_path)

#     # Ensure the columns are named correctly
#     df.columns = ['Article Link', 'Image link']

#     # Create a dictionary mapping article links to image links
#     link_mapping = dict(zip(df['Article Link'], df['Image link']))

#     # Find the most similar article link using Levenshtein distance
#     most_similar_link = min(df['Article Link'], key=lambda x: levenshtein_distance(x, article_link))
#     image_link = link_mapping.get(most_similar_link, "Image link not found")
    
#     if image_link == "Image link not found" or image_link == 0:
#         return None
#     return image_link

def create_ui():
    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    footer:after {content:''; display:block; position:relative; top:2px; color: transparent; background-color: transparent;}
    .viewerBadge_container__1QSob {display: none !important;}
    .stActionButton {display: none !important;}
    ::-webkit-scrollbar {
        width: 12px;  /* Keep the width of the scrollbar */
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    ::-webkit-scrollbar-thumb {
        background: #888;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    .scroll-icon {
        position: fixed;
        bottom: 40px;  /* Adjusted the position upwards */
        right: 150px;
        font-size: 32px;
        cursor: pointer;
        color: #0adbfc;
        z-index: 1000;
    }
    </style>
    <script>
    function scrollToBottom() {
        window.scrollTo(0, 50000);
    }
    </script>
    """

    st.markdown(hide_streamlit_style, unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #0adbfc;'><u> The Smart Branding Book</u></h2>", unsafe_allow_html=True)
    st.sidebar.image("Aryma Labs Logo.jpeg")
    st.sidebar.markdown("<h3 style='color: #08daff;'>The Smart Branding Book</h2>", unsafe_allow_html=True)
    # st.sidebar.write("Ask anything about MMM and get accurate answers.")
    

    if not st.session_state.authenticated:
        st.markdown("<h3 style='color: #4682B4;'>Login</h3>", unsafe_allow_html=True)
        with st.form(key='login_form'):
            email = st.text_input("Email")
            login_button = st.form_submit_button(label='Login')

            if login_button:
                if authenticate_user(email):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid email or password. Please try again.")
        return

    st.sidebar.markdown("<h5 style='color: #08daff;'>Popular Questions</h3>", unsafe_allow_html=True)

    suggested_questions = [
        "What is Branding ?",
        "How does a brand grows ?",
        "Who is responsible for branding ?",
        "What is the impact of brand building on demand curve ?",
        "Explain Brand Value Growth Matrix ."
    ]

    for i, question in enumerate(suggested_questions):
        if st.sidebar.button(question, key=f"button_{i}", use_container_width=True):
            st.session_state.suggested_question = question
            st.session_state.generate_response = True

    # Display the conversation history in reverse order to resemble a chat interface
    chat_container = st.container()
    LANGUAGES = {
    'Arabic': 'ar',
    'Azerbaijani': 'az',
    'Catalan': 'ca',
    'Chinese': 'zh',
    'Czech': 'cs',
    'Danish': 'da',
    'Dutch': 'nl',
    'English': 'en',
    'Esperanto': 'eo',
    'Finnish': 'fi',
    'French': 'fr',
    'German': 'de',
    'Greek': 'el',
    'Hebrew': 'he',
    'Hindi': 'hi',
    'Hungarian': 'hu',
    'Indonesian': 'id',
    'Irish': 'ga',
    'Italian': 'it',
    'Japanese': 'ja',
    'Korean': 'ko',
    'Persian': 'fa',
    'Polish': 'pl',
    'Portuguese': 'pt',
    'Russian': 'ru',
    'Slovak': 'sk',
    'Spanish': 'es',
    'Swedish': 'sv',
    'Turkish': 'tr',
    'Ukrainian': 'uk',
    'bengali' : 'bn'
}
    with chat_container:
        if st.session_state.conversation_history == []:
            col1, col2 = st.columns([1, 8])
            with col1:
                st.image('download.png', width=30)
            with col2:
                
                st.write("Hello, I am Smart Branding GPT . How can I help you?")
    for idx , (q, r ,most_relevant_page,book_name,suggested_questions) in enumerate(st.session_state.conversation_history):
        st.markdown(f"<p style='text-align: right; color: #484f4f;'><b>{q}</b></p>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 8])
        with col1:
            st.image('download.png', width=30)
        with col2:
            st.write(r + "\n\n")
            st.write("for more details , please visit : https://www.amazon.in/Smart-Branding-Book-popular-profitable-ebook/dp/B0BR1JYRNS")
            # target_language = st.selectbox('Select target language', options=list(LANGUAGES.keys()), key=f'target_language_{idx}')
        # if st.button('Translate', key=f'translate_button_{idx}'):
    
            # if target_language:
                # Translation
                # translated_text = translate(clean_text(r), from_lang='en', to_lang=LANGUAGES[target_language])

            # Display the translation
            # st.subheader('Translated Text')
            # st.write( translated_text + "\n\n" + translate("For more details, please visit", from_lang='en', to_lang=LANGUAGES[target_language]) + ": " + post_link)
            if most_relevant_page is not None:
                # Construct the image filename based on the most relevant page number
                image_filename = f"{book_name}_page_{most_relevant_page}_image_1.png"
                # converted_images\The Smart Branding Book_page_1_image_1.png
                # Define the path to the image folder
                image_folder = 'converted_images'

                # Create the full path to the image
                image_path = os.path.join(image_folder, image_filename)

                # Check if the image file exists
                if os.path.exists(image_path):
                    # Open and display the image using PIL
                    image = Image.open(image_path)
                    st.image(image, use_column_width=True)
                else:
                    print(f"Image for page {most_relevant_page} not found at {image_path}")
            else:
                print("Most relevant page not found")
            st.write("Explore Similiar questions :")
            for i, suggested_question in enumerate(suggested_questions):
                # Ensure unique keys for buttons
                if(suggested_question.page_content != q):
                    if st.button(suggested_question.page_content, key=f"suggested_questions_{idx}_{i}", use_container_width=True):
                        st.session_state.suggested_question = suggested_question.page_content
                        st.session_state.generate_response = True

    # Get user input at the bottom
    st.markdown("---")
    instr = "Ask a question:"
    with st.form(key='input_form', clear_on_submit=True):
        col1, col2 = st.columns([8, 1])
        with col1:
            if st.session_state.suggested_question:
                question = st.text_input(instr, value=st.session_state.suggested_question, key="input_question", label_visibility='collapsed')
            else:
                question = st.text_input(instr, key="input_question", placeholder=instr, label_visibility='collapsed')
    
        # Add checkboxes horizontally
        col_checkbox1, col_checkbox2 = st.columns(2)
        with col_checkbox1:
            checkbox1 = st.checkbox(label='Chat with The Smart Branding Book')
            checkbox2 = st.checkbox(label='Chat with The Smart Marketing Book')
        with col_checkbox2:
            checkbox3 = st.checkbox(label='Chat with The Smart Advertising Book')
            checkbox4 = st.checkbox(label='Chat with The Soft Skills Book')
    
        # Submit button
        submit_button = st.form_submit_button(label="Submit")
    
        # Check which checkbox was selected after submission
        if submit_button and question:
            if st.session_state.query_count >= QUERY_LIMIT:
                st.warning("You have reached the limit of free queries. Please consider our pricing options for further use.")
            else:
                with st.spinner("Generating response..."):
                    if checkbox1:
                        response, docs , suggested_questions = user_input1(question)
                    elif checkbox2:
                        response, docs , suggested_questions = user_input2(question)
                    elif checkbox3:
                        response, docs, suggested_questions = user_input3(question)
                    elif checkbox4:
                        response, docs, suggested_questions = user_input4(question)
                    else:
                        response, docs = None, None  # No checkbox selected
    
                    if response:
                        most_relevant_page = extract_page_number_from_document(docs)
                        book_name = extract_book_name_from_text(docs)
                        print(docs)
                        output_text = response.get('output_text', 'No response')  # Extract the 'output_text' from the response
                        st.session_state.chat += str(output_text)
                        st.session_state.conversation_history.append((question, output_text, most_relevant_page, book_name , suggested_questions))
                        st.session_state.suggested_question = ""  # Reset the suggested question after submission
                        st.session_state.query_count += 1  # Increment the query count
                        st.session_state.generate_response = False
                        st.rerun()



    # Scroll to bottom icon
    st.markdown("""
        <div class="scroll-icon">⬇️</div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #A9A9A9;'>Powered by: Aryma Labs</p>", unsafe_allow_html=True)

# Main function to run the app
def main():
    create_ui()

if __name__ == "__main__":
    main()
