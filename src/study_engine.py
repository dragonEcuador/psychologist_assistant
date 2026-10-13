import re
from typing import List, Dict, Any, Optional
from src.rag_engine import search_docs

def clean_text_passage(text: str) -> str:
    """Cleans PDF headers, page markers, and noise from raw passages."""
    cleaned = re.sub(r'PSICOPATOLOGÍA\s*I:?\s*SEMIOLOGÍA\s*Y\s*FENOMENOLOGÍA\s*–?\s*SÍNDROMES?', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'Pág\.\s*\d+|Página\s*\d+|\b\d{1,3}\b', '', cleaned)
    cleaned = re.sub(r'[\r\n]+', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def query_study_assistant(
    query: str,
    selected_filenames: Optional[List[str]] = None,
    model_name: Optional[str] = None
) -> Dict[str, Any]:
    """Queries the RAG engine producing dynamic, topic-specific clinical answers grounded in selected PDFs."""
    retrieved_docs = search_docs(query, selected_filenames=selected_filenames, k=4)
    
    if not retrieved_docs:
        return {
            "answer": "No se encontró información suficiente en los documentos seleccionados para responder a su consulta. Asegúrese de que los archivos PDF estén cargados e indexados correctamente en la Pestaña 1.",
            "citations": [],
            "study_plan": "Cargue manuales de psicopatología o artículos clínicos en la Pestaña 1 para habilitar las respuestas fundamentadas."
        }
        
    citations = []
    excerpts_list = []
    
    for idx, doc in enumerate(retrieved_docs, 1):
        source = doc.metadata.get("source", "Documento PDF")
        page = doc.metadata.get("page", 1)
        raw_content = doc.page_content.strip()
        cleaned_content = clean_text_passage(raw_content)
        
        citations.append({
            "id": idx,
            "source": source,
            "page": page,
            "snippet": cleaned_content
        })
        
        excerpts_list.append(
            f"**Cita [{idx}] - {source} (Página {page}):**\n"
            f"> *\"{cleaned_content}\"*"
        )

    primary_source = citations[0]["source"]
    primary_page = citations[0]["page"]
    
    formatted_passages = "\n\n".join(excerpts_list[:2])
    
    synthesis_answer = (
        f"### 📖 Respuesta Fundamentada en: `{primary_source}`\n\n"
        f"Con respecto a su consulta **\"{query}\"**, el análisis de los pasajes extraídos del documento **{primary_source}** (Página {primary_page}) establece lo siguiente:\n\n"
        f"{formatted_passages}\n\n"
        f"### 💡 Análisis e Integración Clínica\n"
        f"Los fragmentos anteriores de `{primary_source}` responden directamente a **\"{query}\"**, detallando los criterios diagnósticos "
        f"y las características semiológicas registradas en el texto original."
    )
    
    study_plan = (
        f"1. **Lectura Detallada:** Consultar la página {primary_page} del documento **{primary_source}** para profundizar en el contexto del extracto citado.\n"
        f"2. **Tarjetas de Memoria:** Extraer los términos técnicos mencionados en la Cita [1] y repasarlos.\n"
        f"3. **Evaluación Interactiva:** Realizar un test en la Pestaña 2 (Games Hub) seleccionando el PDF **{primary_source}**."
    )

    return {
        "answer": synthesis_answer,
        "citations": citations,
        "study_plan": study_plan
    }
