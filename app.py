from flask import Flask, request, jsonify, render_template
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
from pymongo import MongoClient

app = Flask(__name__)

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['candidate_db']
candidates_collection = db['candidates']

def load_candidates_from_excel(file_path):
    # Read the Excel file
    df = pd.read_excel(file_path)
    
    print("Excel file columns:")
    print(df.columns)
    
    # No need to rename columns as they are already in a good format
    
    # Convert DataFrame to list of dictionaries
    candidates = df.to_dict('records')
    
    print("Sample candidate data:")
    print(candidates[0] if candidates else "No data")
    
    # Insert candidates into MongoDB
    candidates_collection.delete_many({})  # Clear existing data
    candidates_collection.insert_many(candidates)
def preprocess_text(text):
    # Tokenize and remove stopwords
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(str(text).lower())
    return ' '.join([w for w in word_tokens if w not in stop_words])

def get_matching_candidates(job_description):
    # Preprocess job description
    processed_job_description = preprocess_text(job_description)
    
    # Prepare candidate documents
    candidates = list(candidates_collection.find())
    
    if not candidates:
        print("No candidates found in the database.")
        return []
    
    print("Sample candidate document structure:")
    print(candidates[0])
    
    # Use the correct field names
    candidate_docs = [f"{c.get('Job Skills', '')} {c.get('Experience', '')} {c.get('Projects', '')}" for c in candidates]
    
    processed_candidate_docs = [preprocess_text(doc) for doc in candidate_docs]
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([processed_job_description] + processed_candidate_docs)
    
    # Compute cosine similarity
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    
    # Get top 5 matching candidates
    top_indices = cosine_similarities.argsort()[-5:][::-1]
    
    # Prepare results
    results = []
    for idx in top_indices:
        candidate = candidates[idx]
        similarity_score = cosine_similarities[idx]
        results.append({
            "id": str(candidate["_id"]),  # Convert ObjectId to string
            "name": candidate["Name"],
            "contact": candidate["Contact Details"],
            "location": candidate["Location"],
            "skills": candidate["Job Skills"],
            "experience": candidate["Experience"],
            "projects": candidate["Projects"],
            "comments": candidate.get("Comments", ""),  # Include Comments if available
            "similarity_score": float(similarity_score)
        })
    
    return results
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file and file.filename.endswith('.xlsx'):
        file_path = os.path.join('uploads', file.filename)
        file.save(file_path)
        load_candidates_from_excel(file_path)
        return jsonify({'message': 'File uploaded successfully and data stored in MongoDB'})
    return jsonify({'error': 'Invalid file type'})

@app.route('/match', methods=['POST'])
def match_candidates():
    job_description = request.json['job_description']
    matching_candidates = get_matching_candidates(job_description)
    return jsonify(matching_candidates)

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    
    app.run(debug=True)