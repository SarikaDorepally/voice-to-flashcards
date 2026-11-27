# 🎓 VoiceToFlashcards AI – Multimodal Study Assistant

An AI-powered learning assistant that transforms lecture audio into structured study materials, including study guides, flashcards, quizzes and performance analytics.

Built using Python, Streamlit and Google Gemini, VoiceToFlashcards helps students turn lengthy lectures into interactive and organized learning experiences.

## 🚀 Overview

Students often spend significant time converting lecture recordings into notes, preparing flashcards and creating practice questions.

**VoiceToFlashcards AI** simplifies this process by using AI to transform lecture audio into structured learning resources.

The application provides an interactive learning workflow where students can generate study materials, practice through quizzes, track their progress and review their learning history.

## ✨ Key Features

### 🎙️ Audio-to-Study Materials
- Process lecture audio and extract meaningful learning content.
- Generate structured study guides from lecture content.
- Organize important concepts into easy-to-understand sections.

### 🃏 AI Flashcard Generation
- Automatically generate flashcards from lecture content.
- Convert important concepts into question-and-answer pairs.
- Support active recall and revision.

### 📝 AI Quiz Generation
- Generate quizzes based on processed lecture content.
- Allow students to test their understanding.
- Provide automated grading and performance feedback.

### 📊 Learning Analytics
- Track quiz performance and learning progress.
- Maintain session history.
- View study activity and performance insights through analytics.

### 📁 Export Functionality
- Export generated learning materials in CSV format.
- Download structured study content in Markdown format.
- Keep generated materials for future revision.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core application development |
| Streamlit | Interactive web interface |
| Google Gemini API | AI-powered content generation |
| Pandas | Data processing and management |
| Plotly | Interactive analytics and visualizations |

## 🏗️ Application Workflow

1. **Audio Input:** Provide lecture audio to the application.
2. **Content Processing:** Extract and organize meaningful lecture content.
3. **AI Processing:** Use Google Gemini to generate structured learning materials.
4. **Flashcard Generation:** Create question-and-answer flashcards.
5. **Quiz Generation:** Generate practice questions based on lecture content.
6. **Automatic Evaluation:** Grade quiz responses and provide feedback.
7. **Progress Tracking:** Maintain session history and learning analytics.
8. **Export:** Download study materials in CSV and Markdown formats.

## 📂 Project Structure

```text
VoiceToFlashcards-AI/
│
├── app.py
├── requirements.txt
├── .env
├── README.md
│
├── assets/
│   └── images/
│
├── modules/
│   ├── audio_processing.py
│   ├── flashcard_generation.py
│   ├── quiz_generation.py
│   └── analytics.py
│
└── exports/
```

*Note: Update this structure to match your actual repository files.*

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

```bash
cd VoiceToFlashcards-AI
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux / macOS:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_gemini_api_key
```

Never commit your API key or other sensitive credentials to GitHub.

### 5. Run the Application

```bash
streamlit run app.py
```

Open the local URL displayed in your terminal to access the application.

## 🎯 Use Cases

- Students converting recorded lectures into revision notes.
- Learners preparing flashcards for active recall.
- Students practicing concepts through AI-generated quizzes.
- Tracking learning progress and quiz performance.
- Organizing lecture content for exam preparation.

## 🔮 Future Enhancements

- Support for additional audio and video formats.
- Personalized learning recommendations.
- Spaced repetition-based flashcard revision.
- Multi-language lecture processing.
- Cloud-based storage and synchronization.
- Advanced learning performance dashboards.

## 👩‍💻 Developed By

**Sarika Dorepally**

B.Tech – Computer Science and Engineering (AI & ML)

- GitHub: https://github.com/SarikaDorepally
- LinkedIn: https://www.linkedin.com/in/dorepally-sarika/

## 💡 Project Motivation

The goal of VoiceToFlashcards AI is to make learning more efficient by reducing the manual effort involved in creating study materials.

By combining AI-powered content generation with interactive learning tools, the project aims to turn passive lecture consumption into an engaging and measurable learning experience.

---

⭐ If you find this project interesting, consider giving the repository a star!
