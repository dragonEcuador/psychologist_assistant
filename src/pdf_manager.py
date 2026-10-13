import os
import shutil
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

UPLOAD_DIR = os.path.join("data", "uploaded_pdfs")
SAMPLE_DIR = os.path.join("data", "sample_pdfs")

def ensure_directories():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    os.makedirs(SAMPLE_DIR, exist_ok=True)

def list_uploaded_pdfs() -> List[str]:
    """Returns a list of PDF filenames currently in uploaded_pdfs."""
    ensure_directories()
    if not os.path.exists(UPLOAD_DIR):
        return []
    return [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith('.pdf')]

def save_uploaded_pdf(uploaded_file) -> str:
    """Saves a Streamlit UploadedFile object to UPLOAD_DIR."""
    ensure_directories()
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def delete_uploaded_pdf(filename: str) -> bool:
    """Deletes a PDF file from UPLOAD_DIR."""
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False

def load_pdf_documents(file_path: str) -> List[Document]:
    """Loads and returns Document objects from a PDF file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at {file_path}")
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    filename = os.path.basename(file_path)
    for i, doc in enumerate(docs):
        doc.metadata["source"] = filename
        doc.metadata["file_name"] = filename
        doc.metadata["page"] = i + 1
    return docs

def create_sample_psychology_pdfs_if_empty():
    """Generates starter psychology PDFs if no PDFs are in uploaded_pdfs."""
    ensure_directories()
    existing = list_uploaded_pdfs()
    if existing:
        return

    # We will generate two sample PDFs using a minimal PDF builder or reportlab if available
    pdf1_content = (
        "Cognitive Behavioral Therapy (CBT) and Clinical Psychology Principles\n\n"
        "Chapter 1: Foundations of CBT\n"
        "Cognitive Behavioral Therapy (CBT) is a structured, goal-oriented psychotherapeutic treatment "
        "that helps individuals identify and change negative or unhelpful thought patterns and behaviors. "
        "CBT focuses on the interconnectedness of thoughts, emotions, physical sensations, and actions.\n\n"
        "Key Concept: Cognitive Distortions\n"
        "Cognitive distortions are irrational or biased ways of thinking that reinforce negative emotions. "
        "Common cognitive distortions include:\n"
        "1. Catastrophizing: Expecting the worst possible outcome in any situation.\n"
        "2. All-or-Nothing Thinking (Black-and-White Thinking): Viewing situations in extreme terms without gray areas.\n"
        "3. Emotional Reasoning: Assuming that negative feelings reflect true objective reality.\n"
        "4. Mind Reading: Assuming one knows what others are thinking without empirical evidence.\n\n"
        "Chapter 2: Diagnostic Criteria for Mood Disorders\n"
        "Major Depressive Disorder (MDD) is characterized by persistent depressed mood or loss of interest/pleasure "
        "(anhedonia) lasting at least two weeks, accompanied by symptoms such as insomnia or hypersomnia, feelings of "
        "worthlessness, executive dysfunction, fatigue, and recurrent suicidal ideation.\n\n"
        "Generalized Anxiety Disorder (GAD) involves excessive, uncontrollable worry about everyday events for at least "
        "six months, causing significant distress and somatic symptoms like muscle tension, restlessness, and sleep disturbances."
    )

    pdf2_content = (
        "Neuroscience of Learning, Memory, and Neural Plasticity\n\n"
        "Chapter 1: Memory Systems and Brain Structures\n"
        "Human memory is categorized into short-term (working) memory and long-term memory. Long-term memory is further "
        "split into declarative (explicit) memory and non-declarative (implicit) memory.\n\n"
        "Key Anatomical Structures:\n"
        "1. Hippocampus: Crucial for the consolidation of episodic and spatial explicit memories from short-term into long-term storage.\n"
        "2. Amygdala: Primary center for processing emotional memories, fear conditioning, and threat perception.\n"
        "3. Prefrontal Cortex (PFC): Mediates working memory, decision-making, cognitive flexibility, and impulse control.\n"
        "4. Cerebellum and Basal Ganglia: Essential for procedural memory, motor learning, and habit formation.\n\n"
        "Chapter 2: Synaptic Plasticity and Long-Term Potentiation (LTP)\n"
        "Neuroplasticity refers to the brain's ability to reorganize itself by forming new neural connections throughout life. "
        "Long-Term Potentiation (LTP) is a persistent strengthening of synapses based on recent patterns of activity, "
        "widely considered the cellular mechanism underlying learning and memory. LTP relies heavily on glutamate neurotransmission "
        "and NMDA receptor activation."
    )

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        def write_simple_pdf(path, text):
            c = canvas.Canvas(path, pagesize=letter)
            width, height = letter
            y = height - 50
            for line in text.split('\n'):
                if y < 50:
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, line[:90])
                y -= 15
            c.save()

        write_simple_pdf(os.path.join(UPLOAD_DIR, "CBT_and_Clinical_Psychology.pdf"), pdf1_content)
        write_simple_pdf(os.path.join(UPLOAD_DIR, "Neuroscience_and_Memory.pdf"), pdf2_content)
    except Exception as e:
        # Fallback if reportlab is not available: write plain text disguised or install reportlab
        pass
