# Coach Spark – AI Learning & Development Assistant

Coach Spark is an AI-powered Learning & Development assistant developed as part of an internship project. It helps manufacturing employees quickly access training information from company manuals using Retrieval-Augmented Generation (RAG).

## Features

- AI-powered question answering
- Searches across multiple training manuals
- Retrieves relevant manual content
- Source attribution for every response
- Employee personalization
- Training recommendations
- Machine troubleshooting support
- Practice quizzes
- Hallucination prevention using document retrieval

## Technologies Used

- Python
- Django
- Groq API
- HTML
- CSS
- JavaScript

## Project Structure

```
AIAgent_django/
│
├── assistant/
│   ├── views.py
│   ├── rag.py
│   ├── personalize.py
│   ├── recommender.py
│   ├── templates/
│   ├── static/
│   └── knowledge_base/
│
├── manage.py
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
```

### 2. Open the project

```bash
cd AIAgent_django
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

Create a file named `.env` in the project root.

Add your Groq API key:

```text
GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run the Django server

```bash
python manage.py runserver
```

### 6. Open in your browser

```
http://127.0.0.1:8000/
```

## Note

The `.env` file is intentionally excluded from GitHub for security reasons.

Create your own `.env` file before running the project.
