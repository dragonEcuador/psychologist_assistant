# Project Memory & Standards (Psychology Learning Assistant)

## Architectural Decisions
- **Framework:** Streamlit (`st.session_state` management for tab navigation, PDF filter state, score tracking, active game state, quiz history, recommendations, Q&A history).
- **RAG Pipeline:** LangChain (`HuggingFaceEmbeddings` with `all-MiniLM-L6-v2` for 100% offline embeddings, `Chroma` local persistent vector database).
- **Document Processing:** PyPDF / LangChain PyPDFLoader with RecursiveCharacterTextSplitter (chunk size: 800, overlap: 150) preserving PDF document source metadata.
- **Interactive Games Hub:**
  1. *Case Study Detective*: Clinical scenario extraction + authentic syndrome identification + non-repeating tracking (`seen_case_studies`).
  2. *Concept Clash*: Rapid-fire 10 True/False myth vs. fact test with instant feedback and score counters.
  3. *The Synapse Sorter*: Interactive term-matching game linking psychological terms & symptoms to full definition cards.
- **Post-Game Smart Analytics:** Analysis of incorrect questions against source document topics with targeted study recommendations in Spanish.
- **Study & Q&A Assistant:** RAG query system returning documented explanations with source citations and structured actionable study plans.

## Technical & UI Standards
- Modular design:
  - `src/rag_engine.py`: Vector store, embedding creation, retrieval by selected document filter.
  - `src/pdf_manager.py`: PDF upload, file storage, parsing, indexing metadata.
  - `src/game_engine.py`: Dynamic syndrome & concept extractor (`extract_dynamic_pdf_passages`), non-repeating case study generator, 10 True/False item generator, Synapse Sorter term/definition pair generator, and instant post-game recommendation analyzer in Spanish.
  - `src/study_engine.py`: RAG Q&A chain with citation extractor and study plan generator.
  - `app.py`: Streamlit main UI layout with multi-tab structure and session state persistence.
- Session state safety: Always check and initialize keys before render (`st.session_state.get()`).