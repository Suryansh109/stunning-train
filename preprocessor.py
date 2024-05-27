import PyPDF2
from flask import Flask, request, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
import pysolr
from gemini_pro import response

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='')

# Set up file upload directory
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize Solr client
SOLR_URL = 'http://localhost:8984/solr/query_engine'
solr = pysolr.Solr(SOLR_URL, always_commit=True)

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_path):
    file_extension = file_path.rsplit('.', 1)[1].lower()
    if file_extension == 'pdf':
        return extract_text_from_pdf(file_path)
    
    elif file_extension == 'txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    return ''

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
    return text

def search_documents(query):
    response = solr.search('id:' + query)
    return response

def generate_response(prompt):
    return response(prompt)

@app.route('/')
def serve_html():
    return send_from_directory('.', 'index.html')

@app.route('/query', methods=['POST'])
def query():
    user_query = request.form.get('query')
    file = request.files.get('file')

    file_text = ""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_text = extract_text_from_file(file_path)
    
    documents = search_documents(user_query)
    doc_contents = ' '.join([doc['content'][0] for doc in documents])

    combined_prompt = f"Based on the following documents: {doc_contents} \n"
    if file_text:
        combined_prompt += f"And based on the uploaded file content: {file_text} \n"
    combined_prompt += f"Answer the query: {user_query}"

    ai_response = generate_response(combined_prompt)
    return jsonify( ai_response)

if __name__ == '__main__':
    app.run(debug=True)
