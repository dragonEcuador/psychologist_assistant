import sys
import os

print("--- Testing PDF Manager & Sample Creation ---")
from src.pdf_manager import create_sample_psychology_pdfs_if_empty, list_uploaded_pdfs
create_sample_psychology_pdfs_if_empty()
pdfs = list_uploaded_pdfs()
print(f"Found PDFs: {pdfs}")
assert len(pdfs) > 0, "PDF list should not be empty"

print("\n--- Testing RAG Vector Engine & Chroma Persistent Store ---")
from src.rag_engine import reindex_all_pdfs, search_docs, get_indexed_stats
reindex_res = reindex_all_pdfs()
print(f"Re-indexed files: {reindex_res}")
stats = get_indexed_stats()
print(f"Total vector chunks: {stats}")
assert stats["total_chunks"] > 0, "Chroma vector store should contain chunk embeddings"

docs = search_docs("cognitive distortions CBT", selected_filenames=[pdfs[0]])
print(f"Search results for PDF {pdfs[0]}: {len(docs)} chunks retrieved.")
assert len(docs) > 0, "Retrieved docs should not be empty"

print("\n--- Testing Ollama Local LLM Connectivity ---")
from src.llm_utils import check_ollama_status, get_available_model_name
status = check_ollama_status()
print(f"Ollama status: {status}")
model = get_available_model_name()
print(f"Selected Ollama model: {model}")

print("\n--- Testing Game Generators ---")
from src.game_engine import (
    generate_case_study_detective,
    generate_concept_clash,
    generate_synapse_sorter,
    generate_post_game_recommendations
)

case_study = generate_case_study_detective(selected_filenames=[pdfs[0]], model_name=model)
print(f"Case Study Detective generated successfully: {case_study.get('title')}")

concept_clash = generate_concept_clash(selected_filenames=[pdfs[0]], count=3, model_name=model)
print(f"Concept Clash generated successfully: {len(concept_clash)} items")

synapse_sorter = generate_synapse_sorter(selected_filenames=[pdfs[0]], model_name=model)
print(f"Synapse Sorter generated successfully: {synapse_sorter.get('title')}")

failed_sample = [
    {
        "question": "What is catastrophizing?",
        "user_answer": "Somatic symptom",
        "correct_answer": "Expecting worst possible outcome",
        "explanation": "Catastrophizing is a cognitive distortion."
    }
]
recs = generate_post_game_recommendations(failed_sample, selected_filenames=[pdfs[0]], model_name=model)
print(f"Post-game recommendations generated successfully:\n{recs[:200]}...")

print("\n--- Testing Study & Q&A Assistant ---")
from src.study_engine import query_study_assistant
qa_res = query_study_assistant("Explain CBT and cognitive distortions", selected_filenames=[pdfs[0]], model_name=model)
print(f"QA Answer generated successfully: {qa_res.get('answer')[:150]}...")
print(f"Citations count: {len(qa_res.get('citations', []))}")
print(f"Study Plan: {qa_res.get('study_plan')[:150]}...")

print("\n✅ ALL BACKEND TESTS PASSED SUCCESSFULLY!")
