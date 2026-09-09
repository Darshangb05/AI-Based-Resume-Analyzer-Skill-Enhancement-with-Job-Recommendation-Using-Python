from flask import Flask, request, render_template, jsonify
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx
import re
import nltk
from textblob import TextBlob
import os
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Load job skills data


# Load your CSV file
import pandas as pd

def load_job_data():

    file_path = r"C:\Users\HP\Desktop\project 1\resume  analyzer\job_skills.csv"

    df = pd.read_csv(
        file_path,
        encoding='utf-8',
        on_bad_lines='skip'
    )

    print(df.head())

    jobs_data = {}

    for _, row in df.iterrows():

        job_role = str(row['Job Title']).strip()

        skills = str(row['Skills']) if pd.notna(row['Skills']) else ""

        skill_list = [
            skill.strip()
            for skill in skills.split(',')
            if skill.strip()
        ]

        jobs_data[job_role] = skill_list

    all_skills = sorted(set(
        skill
        for skills in jobs_data.values()
        for skill in skills
    ))

    return jobs_data, all_skills
class ResumeAnalyzer:
    def __init__(self):
        self.jobs_data, self.all_skills = load_job_data()
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
    def extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"Error reading PDF: {e}")
        return text
    
    def extract_text_from_docx(self, file_path):
        """Extract text from DOCX file"""
        text = ""
        try:
            doc = docx.Document(file_path)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        except Exception as e:
            print(f"Error reading DOCX: {e}")
        return text
    
    def extract_contact_info(self, text):
        """Extract name and email from resume text"""
        # Email extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        email = emails[0] if emails else "Email not found"
        
        # Name extraction (simple approach - first few words that look like names)
        lines = text.split('\n')
        name = "Name not found"
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line.split()) <= 4 and not '@' in line:
                if not any(char.isdigit() for char in line):
                    name = line
                    break
        
        return name, email
    
    def extract_skills(self, text):
        """Extract skills from resume text"""
        text_lower = text.lower()
        found_skills = []
        
        for skill in self.all_skills:
            # Check for exact match and variations
            skill_variations = [
                skill.lower(),
                skill.lower().replace(' ', ''),
                skill.lower().replace('.', ''),
            ]
            
            for variation in skill_variations:
                if variation in text_lower:
                    if skill not in found_skills:
                        found_skills.append(skill)
                    break
        
        return found_skills
    
    def calculate_ats_score(self, resume_skills, job_title):
        """Calculate ATS score based on job requirements"""
        if job_title not in self.jobs_data:
            return 0
        
        required_skills = self.jobs_data[job_title]
        if not required_skills or not resume_skills:
            return 0
        
        # Calculate skill match percentage
        matched_skills = set(resume_skills) & set(required_skills)
        score = (len(matched_skills) / len(required_skills)) * 100
        
        # Bonus for extra relevant skills
        bonus_skills = len(set(resume_skills) - set(required_skills)) * 2
        score = min(100, score + bonus_skills)
        
        return round(score, 1)
    
    def recommend_jobs(self, resume_skills, top_n=5):
        """Recommend jobs based on skills"""
        job_scores = []
        
        for job_title, required_skills in self.jobs_data.items():
            if not required_skills:
                continue
                
            matched_skills = set(resume_skills) & set(required_skills)
            match_percentage = (len(matched_skills) / len(required_skills)) * 100
            
            if match_percentage > 0:
                job_scores.append({
                    'job_title': job_title,
                    'match_percentage': round(match_percentage, 1),
                    'matched_skills': list(matched_skills),
                    'total_required': len(required_skills)
                })
        
        # Sort by match percentage
        job_scores.sort(key=lambda x: x['match_percentage'], reverse=True)
        return job_scores[:top_n]
    
    def get_missing_skills(self, resume_skills, job_title):
        """Get skills missing for a specific job"""
        if job_title not in self.jobs_data:
            return []
        
        required_skills = set(self.jobs_data[job_title])
        resume_skills_set = set(resume_skills)
        missing_skills = list(required_skills - resume_skills_set)
        
        return missing_skills

# Initialize analyzer
analyzer = ResumeAnalyzer()

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', jobs=list(analyzer.jobs_data.keys()))

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    """Analyze uploaded resume"""
    try:
        # Get form data
        job_title = request.form.get('job_title')
        
        if 'resume' not in request.files:
            return jsonify({'error': 'No file uploaded'})
        
        file = request.files['resume']
        if file.filename == '':
            return jsonify({'error': 'No file selected'})
        
        # Save uploaded file
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(file_path)
        
        # Extract text based on file type
        if filename.lower().endswith('.pdf'):
            resume_text = analyzer.extract_text_from_pdf(file_path)
        elif filename.lower().endswith('.docx'):
            resume_text = analyzer.extract_text_from_docx(file_path)
        else:
            return jsonify({'error': 'Unsupported file format'})
        
        # Clean up uploaded file
        os.remove(file_path)
        
        if not resume_text.strip():
            return jsonify({'error': 'Could not extract text from resume'})
        
        # Extract information
        name, email = analyzer.extract_contact_info(resume_text)
        skills = analyzer.extract_skills(resume_text)
        ats_score = analyzer.calculate_ats_score(skills, job_title)
        job_recommendations = analyzer.recommend_jobs(skills)
        missing_skills = analyzer.get_missing_skills(skills, job_title)
        
        # Prepare result data
        result_data = {
            'name': name,
            'email': email,
            'skills': skills,
            'ats_score': ats_score,
            'selected_job': job_title,
            'job_recommendations': job_recommendations,
            'missing_skills': missing_skills,
            'required_skills': analyzer.jobs_data.get(job_title, [])
        }
        
        return render_template('result.html', data=result_data)
        
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True)
