# 📄 Research Paper Chatbot

A **Retrieval-Augmented Generation (RAG) based chatbot** that allows users to upload research papers and ask questions about them. The system extracts content from documents, stores them with unique document IDs, and retrieves relevant information to generate accurate answers.

---

## 🚀 Features

- 📑 Upload research papers (PDF)
- 🆔 Automatic document ID generation for each file
- 📊 Extracts and stores document content
- 🔍 Context-aware search from uploaded papers
- 💬 Ask questions about specific research papers
- 📌 Fetch paper title and details from selected document
- ⚡ Fast retrieval using vector search
- 🤖 AI-powered response generation

---

## 🛠️ Tech Stack

- Python
- LangChain
- Retrieval-Augmented Generation (RAG)
- Vector Database / Embeddings
- Large Language Model (LLM)

---

## 📂 Project Structure

```
research-paper-chatbot/
│
├── rag.py                 # RAG pipeline
├── ingest.py              # Document ingestion & doc ID generation
├── main.py                # Entry point
├── data/                  # Uploaded documents
├── vector_store/          # Stored embeddings
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/research-paper-chatbot.git
cd research-paper-chatbot
```

### 2. Create virtual environment
```bash
python -m venv .venv
```

Activate environment:

**Windows**
```bash
.venv\Scripts\activate
```

**Mac/Linux**
```bash
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

Run the chatbot:

```bash
python main.py
```

### Steps
1. Upload a research paper (PDF).
2. System generates a unique document ID.
3. Ask questions related to the paper.
4. Chatbot retrieves and answers from the uploaded document.

---

## 💡 How It Works

1. User uploads a research paper.
2. Text is extracted and converted into embeddings.
3. Document is stored with a unique ID.
4. User queries trigger similarity search.
5. Relevant context is passed to the language model for response generation.

---

## 🎯 Future Improvements

- Web interface (Streamlit / React)
- Multi-document comparison
- Better citation support
- Improved document indexing
- Conversation memory
- Deployment support

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request.

---

## 📜 License

This project is for academic and educational purposes.
