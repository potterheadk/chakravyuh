# Chakravyuh Medical System 🏥

[![GitHub license](https://github.com/potterheadk/chakravyuh/blob/Master/LICENSE)](https://github.com/potterheadk/chakravyuh/blob/Master/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask Version](https://img.shields.io/badge/flask-2.0%2B-lightgrey.svg)](https://flask.palletsprojects.com/)

An advanced AI-powered medical diagnosis and health management system that combines machine learning with large language models for comprehensive health analytics.

## 🔍 Features

- **Symptom-Based Disease Prediction** - Input symptoms and receive predicted diagnoses with information about medications, diet, and precautions
- **Interactive Chatbot** - Communicate with an AI assistant about medical concerns
- **Advanced Health Analytics** - Get personalized risk assessments for diabetes, heart disease, and more
- **BMI Calculator** - Calculate and track your Body Mass Index
- **Health Data Correlation** - Analyze relationships between medications, allergies, and genetic history
- **Medical Document Analysis** - Upload and summarize medical PDFs with AI-generated insights
- **Doctor Communication** - Send medical summaries directly to healthcare providers
- **Hospital Locator** - Find nearby medical facilities

## 🛠️ Technical Architecture

Chakravyuh leverages a robust tech stack:

- **Backend**: Flask web framework with WebSockets
- **Machine Learning**: Random Forest model for disease prediction
- **Deep Learning**: LLaMA3.2 (via Ollama) for natural language understanding and generation
- **Frontend**: HTML, CSS, JavaScript with responsive design
- **Data Processing**: NumPy, Pandas, FuzzyWuzzy for text matching
- **PDF Processing**: PDFKit for document creation and parsing

## 📋 Prerequisites

- Python 3.8+
- Ollama (for running LLM locally)
- NGrok (for tunneling, if running on Colab)
- 16GB+ RAM recommended for LLM operations

## 🚀 Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/chakravyuh-medical-system.git
   cd chakravyuh-medical-system
   ```

2. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Ollama by following instructions at [ollama.ai](https://ollama.ai)

4. Pull the LLaMA3.2 model:
   ```bash
   ollama pull llama3.2
   ```

5. Start the Ollama server:
   ```bash
   ollama serve
   ```

6. Run the Flask application:
   ```bash
   python app.py
   ```

7. Access the web interface at `http://localhost:5050`

## 🌐 Running Ollama on Google Colab

To leverage more powerful computing resources, you can run Ollama on Google Colab and tunnel it to your local machine:

1. Create a new Colab notebook and run:
   ```python
   !curl -fsSL https://ollama.ai/install.sh | sh
   !ollama serve &
   ```

2. Install NGrok:
   ```python
   !pip install pyngrok
   from pyngrok import ngrok
   
   # Set your authtoken (sign up at ngrok.com)
   ngrok.set_auth_token("your_ngrok_auth_token")
   
   # Open a tunnel to port 11434 (Ollama's default port)
   ollama_tunnel = ngrok.connect(11434, "http")
   print(f"Ollama tunnel URL: {ollama_tunnel.public_url}")
   ```

3. Update your local application to use the NGrok URL:
   ```python
   # Change in your app.py or configuration
   OLLAMA_API_BASE = "https://xxxx-xxxx-xxxx.ngrok.io"  # Replace with your tunnel URL
   ```

This setup allows you to harness Google Colab's GPU resources for faster LLM inference while running your application locally.

## 📊 Dataset Sources

The system uses multiple datasets:
- Symptom-disease mappings
- Precautions and workout recommendations
- Medical descriptions and medication information
- Diet recommendations for various conditions

Datasets are stored in CSV format in the `kaggle_dataset` directory.

## 🔄 Workflow

1. **Disease Prediction Pipeline**:
   - User inputs symptoms → Symptom spelling correction → Vector representation → Random Forest prediction → Information retrieval

2. **LLM Integration Flow**:
   - User query → Input sanitization → Context formation → LLaMA3.2 inference → Response formatting → User display

3. **Document Processing**:
   - PDF upload → Text extraction → AI summarization → PDF report generation → Email delivery

## 📁 Project Structure

```
chakravyuh-medical-system/
├── app.py                  # Main application file
├── chatbot/                # Chatbot module
│   └── handler.py          # Chatbot request handling
├── model/                  # Machine learning models
│   ├── RandomForest.pkl    # Disease prediction model
│   └── heart_disease_model.pkl  # Heart disease model
├── kaggle_dataset/         # Health datasets
├── static/                 # Static assets
│   ├── css/                # Stylesheets
│   ├── images/             # Image assets
│   └── js/                 # JavaScript files
├── templates/              # HTML templates
├── symptoms.py             # Symptom data
├── rag1.py                 # Retrieval-Augmented Generation for PDF analysis
└── requirements.txt        # Package dependencies
```

## 📧 Email Configuration

The system can send reports via email:
1. Configure SMTP settings in app.py:
   ```python
   SMTP_SERVER = "smtp.gmail.com"
   SMTP_PORT = 465
   AUTHOR_EMAIL = "your-email@gmail.com"
   AUTHOR_PASSWORD = "your-app-password"
   ```

2. For Gmail, use an App Password instead of your account password

## 🧠 LLM Integration

The system leverages Ollama to run the LLaMA3.2 model:

```python
stream = chat(
    model='llama3.2',
    messages=[{'role': 'user', 'content': prompt}],
    stream=True
)
```

Prompt engineering techniques are used to optimize model responses for medical contexts.

## 🔒 Security Features

- Input sanitization with Bleach
- Secure filename handling with Werkzeug
- File upload restrictions and size limits
- Content filtering and validation

## 🤝 Contribution

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under Apache License 2.0 - see the LICENSE for more details.

## 🙏 Acknowledgements

- The LLaMA team at Meta AI Research
- The Ollama project for local LLM hosting
- Flask and SocketIO developers
- Medical dataset contributors

---

💡 **Tech Note**: When running on Colab, the NGrok tunnel allows you to bypass resource limitations on your local machine while maintaining a responsive interface. The LLM runs on Colab's powerful instances while the Flask app can be hosted on lighter hardware. This hybrid architecture provides the best of both worlds - powerful inference with minimal local requirements.
