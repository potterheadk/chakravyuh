import random
from chatbot.handler import chat_blueprint
from flask import Flask, request, render_template, jsonify, Response
import numpy as np
import pandas as pd
import pickle
from fuzzywuzzy import process
import ast
from symptoms import *
from ollama import chat
from typing import List
import bleach
from flask_socketio import SocketIO, emit
import logging
import os
import time
import csv
from rag1 import summarize_pdfs
from werkzeug.utils import secure_filename
import markdown
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import pdfkit
from datetime import datetime


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = Flask(__name__)

app.secret_key = os.environ.get("SESSION_SECRET", "dev_key_123")  # Fallback for development
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure file upload settings
UPLOAD_FOLDER = 'downloaded_content'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure patient records folder exists
PATIENT_RECORDS_FOLDER = 'patient_records_temp'
os.makedirs(PATIENT_RECORDS_FOLDER, exist_ok=True)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
AUTHOR_EMAIL = "sender email"
AUTHOR_PASSWORD = "sender email secured password"
RECIPIENT_EMAIL = "receiver email"

sym_des = pd.read_csv("kaggle_dataset/symptoms_df.csv")
precautions = pd.read_csv("kaggle_dataset/precautions_df.csv")
workout = pd.read_csv("kaggle_dataset/workout_df.csv")
description = pd.read_csv("kaggle_dataset/description.csv")
medications = pd.read_csv('kaggle_dataset/medications.csv')
diets = pd.read_csv("kaggle_dataset/diets.csv")

Rf = pickle.load(open('model/RandomForest.pkl', 'rb'))

# Here we make a dictionary of symptoms and diseases and preprocess it

symptoms_list = symptoms_list
diseases_list = diseases_list


symptoms_list_processed = {symptom.replace('_', ' ').lower(): value for symptom, value in symptoms_list.items()}


# Here we created a function (information) to extract information from all the datasets

def information(predicted_dis):
    disease_desciption = description[description['Disease'] == predicted_dis]['Description']
    disease_desciption = " ".join([w for w in disease_desciption])

    disease_precautions = precautions[precautions['Disease'] == predicted_dis][
        ['Precaution_1', 'Precaution_2', 'Precaution_3', 'Precaution_4']]
    disease_precautions = [col for col in disease_precautions.values]

    disease_medications = medications[medications['Disease'] == predicted_dis]['Medication']
    disease_medications = [med for med in disease_medications.values]

    disease_diet = diets[diets['Disease'] == predicted_dis]['Diet']
    disease_diet = [die for die in disease_diet.values]

    disease_workout = workout[workout['disease'] == predicted_dis]['workout']

    return disease_desciption, disease_precautions, disease_medications, disease_diet, disease_workout


# This is the function that passes the user input symptoms to our Model
def predicted_value(patient_symptoms):
    i_vector = np.zeros(len(symptoms_list_processed))
    for i in patient_symptoms:
        i_vector[symptoms_list_processed[i]] = 1
    return diseases_list[Rf.predict([i_vector])[0]]


# Function to correct the spellings of the symptom (if any)
def correct_spelling(symptom):
    closest_match, score = process.extractOne(symptom, symptoms_list_processed.keys())
    # If the similarity score is above a certain threshold, consider it a match
    if score >= 80:
        return closest_match
    else:
        return None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def send_email(subject, body_html, attachment_path=None):
    """Send an email with optional attachment"""
    try:
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['From'] = AUTHOR_EMAIL
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = subject

        # Create the HTML part
        html_part = MIMEText(body_html, 'html')
        msg.attach(html_part)

        # Attach PDF if provided
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                pdf_part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                pdf_part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(pdf_part)

        # Connect to SMTP server and send email
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(AUTHOR_EMAIL, AUTHOR_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent successfully to {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False


def create_pdf_summary(summary_text, title="Medical Document Summary"):
    """Create a PDF file from the summary text"""
    try:
        # Convert the summary to HTML with better formatting
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 40px;
                    color: #333;
                }}
                h1 {{
                    color: #0066cc;
                    border-bottom: 2px solid #0066cc;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #0066cc;
                    margin-top: 20px;
                }}
                .summary {{
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #f9f9f9;
                    border-left: 4px solid #0066cc;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 12px;
                    color: #666;
                    text-align: center;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                    margin: 20px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                    text-align: left;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="summary">
                {markdown.markdown(summary_text)}
            </div>
            <div class="footer">
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Chakravyuh Medical System</p>
            </div>
        </body>
        </html>
        """

        # Generate a unique filename
        timestamp = int(time.time())
        pdf_filename = f"medical_summary_{timestamp}.pdf"
        pdf_path = os.path.join(PATIENT_RECORDS_FOLDER, pdf_filename)

        # Convert HTML to PDF
        pdfkit.from_string(html_content, pdf_path)

        return pdf_path
    except Exception as e:
        logger.error(f"Failed to create PDF: {str(e)}")
        return None


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        symptoms = request.form.get('symptoms')
        if symptoms == "Symptoms":
            message = "Please either write symptoms or you have written misspelled symptoms"
            return render_template('Symptome.html', message=message)
        else:
            # Split the user's input into a list of symptoms (assuming they are comma-separated)
            patient_symptoms = [s.strip() for s in symptoms.split(',')]
            # Remove any extra characters, if any
            patient_symptoms = [symptom.strip("[]' ") for symptom in patient_symptoms]

            # Correct the spelling of symptoms
            corrected_symptoms = []
            for symptom in patient_symptoms:
                corrected_symptom = correct_spelling(symptom)
                if corrected_symptom:
                    corrected_symptoms.append(corrected_symptom)
                else:
                    message = f"Symptom '{symptom}' not found in the database."
                    return render_template('Symptome.html', message=message)

            # Predict the disease using corrected symptoms
            predicted_disease = predicted_value(corrected_symptoms)
            dis_des, precautions, medications, rec_diet, workout = information(predicted_disease)

            my_precautions = []
            for i in precautions[0]:
                my_precautions.append(i)

            # converting the string into a list format before returning to the frontend
            medication_list = ast.literal_eval(medications[0])
            medications = []
            for item in medication_list:
                medications.append(item)

            diet_list = ast.literal_eval(rec_diet[0])
            rec_diet = []
            for item in diet_list:
                rec_diet.append(item)
            return render_template('Symptome.html', symptoms=corrected_symptoms, predicted_disease=predicted_disease,
                                   dis_des=dis_des,
                                   my_precautions=my_precautions, medications=medications, my_diet=rec_diet,
                                   workout=workout)

    return render_template('Symptome.html')


@app.route('/services')
def services():
    return render_template('Symptome.html')


@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analytic')
def analytics():
    return render_template('analytics.html')


# Route for predicting diabetes risk with LLM integration
@app.route('/predict_diabetes', methods=['POST'])
def predict_diabetes():
    data = request.json
    # Fetch parameters from the request
    pregnancies = data['pregnancies']
    glucose = data['glucose']
    blood_pressure = data['blood_pressure']
    skin_thickness = data['skin_thickness']
    insulin = data['insulin']
    bmi = data['bmi']
    diabetes_pedigree = data['diabetes_pedigree']
    age = data['age']

    # Prepare prompt for the model
    prompt = f"""
    Given the following health data:
    - Pregnancies: {pregnancies}
    - Glucose: {glucose}
    - Blood Pressure: {blood_pressure}
    - Skin Thickness: {skin_thickness}
    - Insulin: {insulin}
    - BMI: {bmi}
    - Diabetes Pedigree: {diabetes_pedigree}
    - Age: {age}

    Predict the risk of diabetes (Low, Moderate, or High) and give a confidence percentage.
    answer in 40-50 words
    """

    # Make the request to the model
    prediction = ""
    try:
        stream = chat(
            model='llama3.2',
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        )

        # Collect all chunks of the response
        for chunk in stream:
            if isinstance(chunk, tuple):
                # If chunk is a tuple, get the first element
                chunk_content = chunk[0]
            else:
                # If chunk is a dict, get the message content
                chunk_content = chunk.get('message', {}).get('content', '')

            prediction += str(chunk_content)

    except Exception as e:
        print(f"Error in model prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500

    # Return prediction
    return jsonify({
        'prediction': prediction
    })


# Route for calculating BMI
@app.route('/calculate_bmi', methods=['POST'])
def calculate_bmi():
    weight = float(request.json['weight'])
    height = float(request.json['height'])
    bmi = weight / (height ** 2)
    return jsonify({'bmi': f"BMI: {bmi:.2f}"})


# Route for predicting heart disease risk with LLM integration
@app.route('/predict_heart_disease', methods=['POST'])
def predict_heart_disease():
    data = request.json
    # Extract parameters for prediction
    age = data['age']
    cholesterol = data['cholesterol']
    blood_pressure = data['blood_pressure']
    exercise = data['exercise']

    # Prepare the prompt for the model
    prompt = f"""
    Given the following health data:
    - Age: {age}
    - Cholesterol: {cholesterol}
    - Blood Pressure: {blood_pressure}
    - Exercise: {exercise}

    Predict the risk of heart disease (Low, Moderate, or High) and provide reasoning.
    Be consice and answer in 20-30 words
    """

    # Make the request to the model
    prediction = ""
    try:
        stream = chat(
            model='llama3.2',
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        )

        # Collect all chunks of the response
        for chunk in stream:
            if isinstance(chunk, tuple):
                # If chunk is a tuple, get the first element
                chunk_content = chunk[0]
            else:
                # If chunk is a dict, get the message content
                chunk_content = chunk.get('message', {}).get('content', '')

            prediction += str(chunk_content)

    except Exception as e:
        print(f"Error in model prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500

    return jsonify({'prediction': prediction})


@app.route('/dashboard')
def dashboard():
    # Sample data for dashboard
    # You can replace these values with real data from your form submissions or predictions
    diabetes_data = {
        'pregnancies': 2,
        'glucose': 140,
        'blood_pressure': 80,
        'skin_thickness': 20,
        'insulin': 90,
        'bmi': 29.4,
        'diabetes_pedigree': 0.5,
        'age': 45,
        'prediction': "High risk (Confidence: 85%)"
    }

    heart_disease_data = {
        'age': 55,
        'cholesterol': 230,
        'blood_pressure': 140,
        'exercise': "No",
        'prediction': "Moderate risk (Confidence: 75%)"
    }

    bmi_data = {
        'weight': 70,
        'height': 1.75,
        'bmi': 22.9  # Calculated BMI
    }

    return render_template(
        'dashboard.html',
        diabetes_data=diabetes_data,
        heart_disease_data=heart_disease_data,
        bmi_data=bmi_data
    )


def sanitize_input(text: str) -> str:
    """Basic input sanitization"""
    return bleach.clean(text, tags=[], strip=True)


@app.route('/Health')
def Health():
    return render_template('Health.html')


@app.route('/correlate_health', methods=['POST'])
def correlate_health():
    try:
        data = request.json

        # Sanitize inputs
        medications = [sanitize_input(med) for med in data.get('medications', [])]
        allergies = [sanitize_input(allergy) for allergy in data.get('allergies', [])]
        genetic_history = sanitize_input(data.get('genetic_history', ""))

        # Create prompt for LLaMA
        prompt = f"""
        A patient has provided the following health data:
        - Current Medications: {', '.join(medications)}
        - Known Allergies: {', '.join(allergies)}
        - Genetic Disease History: {genetic_history}

        Correlate the medications, allergies, and genetic history to identify potential risks,
        drug interactions, and hereditary concerns. Provide a summary of potential health risks
        and suggest precautions. Answer in 300-400 words.Mention genetic history and create important
        tables.
        """

        # Get response from LLaMA
        correlation_analysis = ""
        try:
            stream = chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': prompt}],
                stream=True
            )

            for chunk in stream:
                if isinstance(chunk, tuple):
                    chunk_content = chunk[0]
                else:
                    chunk_content = chunk.get('message', {}).get('content', '')
                correlation_analysis += str(chunk_content)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

        return jsonify({"correlation_analysis": correlation_analysis})

    except Exception as e:
        return jsonify({"error": "Invalid request"}), 400


@app.route('/locator')
def locator():
    return render_template('locator.html')


@app.route('/send-to-doctor', methods=['POST'])
def send_to_doctor():
    try:
        if 'text_content' in request.files:
            text_file = request.files['text_content']
            if text_file:
                # Generate a unique filename
                timestamp = int(time.time())
                text_filename = f"medical_summary_{timestamp}.txt"
                file_path = os.path.join(PATIENT_RECORDS_FOLDER, text_filename)

                # Save the text file
                text_file.save(file_path)

                # Send email with the text file attachment
                email_html = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                        h1 {{ color: #0066cc; }}
                        .container {{ padding: 20px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Medical Document for Doctor</h1>
                        <p>Please find attached a medical document for your review.</p>
                        <p>This document contains a summary of the patient's medical records in text format.</p>
                        <p>This is an automated message from Chakravyuh Medical System.</p>
                    </div>
                </body>
                </html>
                """

                email_sent = send_email(
                    subject="Medical Document for Doctor Review",
                    body_html=email_html,
                    attachment_path=file_path
                )

                if email_sent:
                    return jsonify({"message": "Document sent to doctor successfully"})
                else:
                    return jsonify({"error": "Failed to send email"}), 500

        return jsonify({"error": "No valid text content provided"}), 400

    except Exception as e:
        logger.error(f"Error in send-to-doctor: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/upload-pdfs', methods=['GET', 'POST'])
def upload_pdfs():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'pdfs[]' not in request.files:
            return jsonify({"error": "No files provided"}), 400

        files = request.files.getlist('pdfs[]')

        # If no file is selected
        if not files or all(file.filename == '' for file in files):
            return jsonify({"error": "No files selected"}), 400

        saved_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                saved_files.append(file_path)

        if not saved_files:
            return jsonify({"error": "No valid PDF files uploaded"}), 400

        # Process and summarize the PDFs
        summary = summarize_pdfs()

        # Convert summary to markdown for better formatting
        formatted_summary = summary

        # Create a PDF of the summary
        pdf_path = create_pdf_summary(formatted_summary, "Medical Document Analysis")

        # Send the summary via email
        if pdf_path:
            email_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    h1 {{ color: #0066cc; }}
                    .container {{ padding: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Medical Document Analysis Summary</h1>
                    <p>Please find attached a summary of the medical documents analyzed by Chakravyuh Medical System.</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </body>
            </html>
            """

            send_email(
                subject="Medical Document Analysis Summary",
                body_html=email_html,
                attachment_path=pdf_path
            )

        return jsonify({
            "message": f"Successfully uploaded {len(saved_files)} files",
            "summary": formatted_summary,
            "pdf_generated": pdf_path is not None,
            "pdf_path": pdf_path
        })

    # For GET requests, return the uploader page
    return render_template('pdf_uploader.html')


@app.route('/pdf-uploader')
def pdf_uploader():
    return render_template('pdf_uploader.html')



heart_disease_model = pickle.load(open('model/heart_disease_model.pkl', 'rb'))

@app.route('/heart_disease_check', methods=['GET', 'POST'])
def heart_disease_check():
    if request.method == 'POST':
        try:
            # Get values from the form
            age = float(request.form['age'])
            bp = float(request.form['trestbps'])  # Blood pressure
            chol = float(request.form['chol'])    # Cholesterol

            # Make prediction
            features = np.array([[age, bp, chol]])
            prediction = heart_disease_model.predict(features)

            result = "High Risk of Heart Disease" if prediction[0] == 1 else "Low Risk of Heart Disease"

            return render_template('heart_disease.html', prediction=result)

        except Exception as e:
            return render_template('heart_disease.html', error=str(e))

    return render_template('heart_disease.html')

@app.route('/heart-disease')
def heart_disease():
    return render_template('heart_disease.html')

# Register blueprint
app.register_blueprint(chat_blueprint)

if __name__ == '__main__':
    app.run(debug=True, port=5050)
