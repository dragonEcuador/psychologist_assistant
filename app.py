import os
import streamlit as st
from typing import List

from src.pdf_manager import (
    list_uploaded_pdfs,
    save_uploaded_pdf,
    delete_uploaded_pdf,
    create_sample_psychology_pdfs_if_empty,
    UPLOAD_DIR
)
from src.rag_engine import (
    index_pdf_file,
    remove_pdf_from_index,
    reindex_all_pdfs,
    get_indexed_stats
)
from src.llm_utils import check_ollama_status, DEFAULT_MODEL
from src.game_engine import (
    generate_case_study_detective,
    generate_concept_clash,
    generate_synapse_sorter,
    generate_post_game_recommendations
)
from src.study_engine import query_study_assistant

# Page Config
st.set_page_config(
    page_title="Asistente de Aprendizaje Psicológico y Hub de Juegos",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        border-left: 4px solid #3B82F6;
    }
    .game-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    .citation-box {
        background-color: #EFF6FF;
        border-left: 3px solid #2563EB;
        padding: 10px 14px;
        border-radius: 6px;
        font-size: 0.9rem;
        margin-top: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
def init_session_state():
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "correct_count" not in st.session_state:
        st.session_state.correct_count = 0
    if "failed_count" not in st.session_state:
        st.session_state.failed_count = 0
    if "failed_questions_history" not in st.session_state:
        st.session_state.failed_questions_history = []
    if "active_game" not in st.session_state:
        st.session_state.active_game = None
    if "game_data" not in st.session_state:
        st.session_state.game_data = None
    if "game_step" not in st.session_state:
        st.session_state.game_step = 0
    if "user_selected_pdfs" not in st.session_state:
        st.session_state.user_selected_pdfs = []
    if "recommendation_text" not in st.session_state:
        st.session_state.recommendation_text = None
    if "indexed_files_set" not in st.session_state:
        st.session_state.indexed_files_set = set(list_uploaded_pdfs())
    if "seen_case_studies" not in st.session_state:
        st.session_state.seen_case_studies = []
    if "current_qa_query" not in st.session_state:
        st.session_state.current_qa_query = None
    if "current_qa_result" not in st.session_state:
        st.session_state.current_qa_result = None

init_session_state()

# Auto-create sample PDFs on first launch if list is empty
uploaded_files_list = list_uploaded_pdfs()
if not uploaded_files_list:
    create_sample_psychology_pdfs_if_empty()
    reindex_all_pdfs()
    uploaded_files_list = list_uploaded_pdfs()
    st.session_state.indexed_files_set = set(uploaded_files_list)

# Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/illustrations/100/brain.png", width=70)
    st.title("Configuración y Estado")
    
    # Check Ollama status
    ollama_status = check_ollama_status()
    if ollama_status["online"]:
        st.success("🟢 LLM Local Ollama: En Línea")
        available_models = ollama_status["models"]
        if not available_models:
            available_models = [DEFAULT_MODEL]
        selected_model = st.selectbox("Modelo Local Activo", available_models, index=0)
    else:
        st.warning("🟡 Modo Rápido Integrado Activo")
        selected_model = DEFAULT_MODEL
        
    st.markdown("---")
    
    # Score metrics in sidebar
    st.markdown("### 🏆 Progreso de la Sesión")
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Puntos", st.session_state.score)
    col_s2.metric("Aciertos", st.session_state.correct_count)
    col_s3.metric("Fallos", st.session_state.failed_count)
    
    if st.button("Reiniciar Estadísticas"):
        st.session_state.score = 0
        st.session_state.correct_count = 0
        st.session_state.failed_count = 0
        st.session_state.failed_questions_history = []
        st.session_state.seen_case_studies = []
        st.success("¡Estadísticas reiniciadas!")
        st.rerun()

    st.markdown("---")
    st.markdown("🔒 **100% Gratuito y Fuera de Línea**")
    st.caption("Desarrollado con Streamlit, LangChain, Chroma y Ollama.")

# App Header
st.markdown('<div class="main-header">🧠 Asistente de Aprendizaje Psicológico y Games Hub</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Aprende psicología, evalúa tus conocimientos con juegos interactivos y obtén recomendaciones de estudio en español basadas en tus documentos PDF.</div>', unsafe_allow_html=True)

# Main Navigation Tabs
tab_docs, tab_games, tab_study = st.tabs([
    "📄 Pestaña 1: Gestor de Documentos PDF",
    "🎮 Pestaña 2: Games Hub (Evaluaciones)",
    "📚 Pestaña 3: Asistente de Estudio y Consultas"
])

# ==========================================
# PESTAÑA 1: GESTOR DE DOCUMENTOS PDF
# ==========================================
with tab_docs:
    st.header("📄 Gestor de Documentos PDF")
    st.markdown("Cargue, administre e indexe literatura y libros de psicología. El motor RAG fragmenta e indexa el texto localmente.")
    
    col_up1, col_up2 = st.columns([2, 1])
    
    with col_up1:
        uploaded_files = st.file_uploader(
            "Cargar PDFs de Psicología",
            type=["pdf"],
            accept_multiple_files=True,
            help="Suba manuales de psicopatología, guías clínicas o artículos."
        )
        if uploaded_files:
            unindexed_files = [f for f in uploaded_files if f.name not in st.session_state.indexed_files_set]
            if unindexed_files:
                with st.spinner("Indexando nuevo documento PDF en la base vectorial..."):
                    for up_file in unindexed_files:
                        file_path = save_uploaded_pdf(up_file)
                        chunks_count = index_pdf_file(file_path)
                        st.session_state.indexed_files_set.add(up_file.name)
                        st.success(f"¡Documento `{up_file.name}` indexado exitosamente! ({chunks_count} fragmentos creados).")
                    st.rerun()

    with col_up2:
        st.subheader("Acciones Rápidas")
        if st.button("✨ Cargar PDFs de Ejemplo en Español", use_container_width=True):
            create_sample_psychology_pdfs_if_empty()
            indexed_res = reindex_all_pdfs()
            st.session_state.indexed_files_set = set(list_uploaded_pdfs())
            st.success(f"PDFs de ejemplo indexados: {list(indexed_res.keys())}")
            st.rerun()
            
        if st.button("🔄 Reindexar Todos los Documentos PDF", use_container_width=True):
            with st.spinner("Reindexando base de datos vectorial..."):
                res = reindex_all_pdfs()
                st.session_state.indexed_files_set = set(list_uploaded_pdfs())
                st.success(f"Se reindexaron {len(res)} documentos correctamente.")
            st.rerun()

    st.markdown("---")
    st.subheader("📚 Biblioteca de Documentos Indexados")
    
    current_pdfs = list_uploaded_pdfs()
    stats = get_indexed_stats()
    st.caption(f"Total de fragmentos vectoriales: **{stats.get('total_chunks', 0)}** en {len(current_pdfs)} documentos.")
    
    if not current_pdfs:
        st.info("No hay archivos PDF cargados. Suba un archivo PDF o haga clic en 'Cargar PDFs de Ejemplo' para comenzar.")
    else:
        for pdf_name in current_pdfs:
            pdf_path = os.path.join(UPLOAD_DIR, pdf_name)
            size_kb = round(os.path.getsize(pdf_path) / 1024, 1) if os.path.exists(pdf_path) else 0
            
            c_name, c_size, c_action = st.columns([3, 1, 1])
            c_name.write(f"📄 **{pdf_name}**")
            c_size.write(f"{size_kb} KB")
            if c_action.button("🗑️ Eliminar", key=f"del_{pdf_name}"):
                delete_uploaded_pdf(pdf_name)
                remove_pdf_from_index(pdf_name)
                if pdf_name in st.session_state.indexed_files_set:
                    st.session_state.indexed_files_set.remove(pdf_name)
                st.success(f"Se eliminó el documento {pdf_name}")
                st.rerun()


# ==========================================
# PESTAÑA 2: GAMES HUB (EVALUACIONES)
# ==========================================
with tab_games:
    st.header("🎮 Games Hub - Evaluaciones Interactivas")
    st.markdown("Ponga a prueba sus conocimientos con juegos generados dinámicamente en español y adaptados a sus PDFs.")
    
    # Step 1: Pre-Game Configuration
    st.subheader("⚙️ Paso 1: Seleccionar PDFs Fuente para la Evaluación")
    available_pdfs = list_uploaded_pdfs()
    
    if not available_pdfs:
        st.warning("⚠️ No hay PDFs subidos. Diríjase a la Pestaña 1 para cargar documentos.")
    else:
        selected_pdfs = st.multiselect(
            "Seleccione los PDFs para evaluar:",
            options=available_pdfs,
            default=available_pdfs if available_pdfs else [],
            help="Las preguntas se generarán exclusivamente a partir de los documentos seleccionados."
        )
        st.session_state.user_selected_pdfs = selected_pdfs

        if not selected_pdfs:
            st.error("Por favor seleccione al menos un documento PDF para iniciar un juego.")
        else:
            st.markdown("---")
            st.subheader("⚙️ Paso 2: Elegir Juego de Evaluación")
            
            col_g1, col_g2, col_g3 = st.columns(3)
            
            with col_g1:
                st.markdown("""
                ### 🔍 Detective de Casos
                Diagnostique escenarios clínicos y casos prácticos únicos sin repetir preguntas.
                """)
                if st.button("Iniciar Detective de Casos", use_container_width=True, type="primary"):
                    st.session_state.seen_case_studies = []
                    game_data = generate_case_study_detective(
                        selected_pdfs,
                        seen_ids=st.session_state.seen_case_studies,
                        model_name=selected_model
                    )
                    st.session_state.seen_case_studies.append(game_data.get("id"))
                    if game_data.get("title"):
                        st.session_state.seen_case_studies.append(game_data.get("title"))
                    st.session_state.active_game = "case_study"
                    st.session_state.game_data = game_data
                    st.session_state.game_step = 0
                    st.rerun()

            with col_g2:
                st.markdown("""
                ### ⚡ Batalla de Conceptos
                Desafío rápido de 10 preguntas de Verdadero o Falso basadas en sus PDFs.
                """)
                if st.button("Iniciar Batalla de Conceptos", use_container_width=True, type="primary"):
                    game_data = generate_concept_clash(selected_pdfs, count=10, model_name=selected_model)
                    st.session_state.active_game = "concept_clash"
                    st.session_state.game_data = game_data
                    st.session_state.game_step = 0
                    st.rerun()

            with col_g3:
                st.markdown("""
                ### 🧠 Clasificador Sináptico
                Empareje y categorice términos psicológicos con sus definiciones completas.
                """)
                if st.button("Iniciar Clasificador Sináptico", use_container_width=True, type="primary"):
                    if "shuffled_defs" in st.session_state:
                        del st.session_state["shuffled_defs"]
                    game_data = generate_synapse_sorter(selected_pdfs, model_name=selected_model)
                    st.session_state.active_game = "synapse_sorter"
                    st.session_state.game_data = game_data
                    st.session_state.synapse_submitted = False
                    st.rerun()

    # Active Game Arena Render
    active_g = st.session_state.active_game
    if active_g:
        st.markdown("---")
        st.subheader("🎯 Arena de Juego Activa")
        
        # 1. CASE STUDY DETECTIVE GAME (NON-REPEATING)
        if active_g == "case_study" and st.session_state.game_data:
            gdata = st.session_state.game_data
            st.markdown(f"#### 🔍 {gdata.get('title', 'Detective de Casos')}")
            st.info(f"**Escenario Clínico:**\n{gdata.get('scenario')}")
            
            with st.form("case_study_form"):
                user_choice = st.radio(
                    f"**Pregunta:** {gdata.get('question')}",
                    options=gdata.get("options", []),
                    index=0
                )
                submitted = st.form_submit_button("Enviar Diagnóstico")
                
                if submitted:
                    correct_idx = gdata.get("correct_index", 0)
                    correct_opt = gdata.get("options")[correct_idx]
                    
                    if user_choice == correct_opt:
                        st.success("🎉 **¡Diagnóstico Correcto!** +10 Puntos")
                        st.session_state.score += 10
                        st.session_state.correct_count += 1
                    else:
                        st.error(f"❌ **Diagnóstico Incorrecto.** La respuesta correcta era: **{correct_opt}**")
                        st.session_state.failed_count += 1
                        st.session_state.failed_questions_history.append({
                            "question": gdata.get("question"),
                            "user_answer": user_choice,
                            "correct_answer": correct_opt,
                            "explanation": gdata.get("explanation")
                        })
                    st.info(f"**Explicación:** {gdata.get('explanation')}")
            
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("Siguiente Caso Clínico (Nuevo)"):
                game_data = generate_case_study_detective(
                    st.session_state.user_selected_pdfs,
                    seen_ids=st.session_state.seen_case_studies,
                    model_name=selected_model
                )
                st.session_state.seen_case_studies.append(game_data.get("id"))
                if game_data.get("title"):
                    st.session_state.seen_case_studies.append(game_data.get("title"))
                st.session_state.game_data = game_data
                st.rerun()
            if col_b2.button("Finalizar y Ver Análisis Inteligente"):
                st.session_state.active_game = "summary"
                st.rerun()

        # 2. CONCEPT CLASH GAME (10 QUESTIONS)
        elif active_g == "concept_clash" and st.session_state.game_data:
            items = st.session_state.game_data
            step = st.session_state.game_step
            
            if step < len(items):
                item = items[step]
                st.markdown(f"#### ⚡ Pregunta {step + 1} de {len(items)}")
                st.warning(f"**Afirmación:**\n*\"{item.get('statement')}\"*")
                
                col_t, col_f = st.columns(2)
                user_ans = None
                if col_t.button("VERDADERO", use_container_width=True, key=f"t_{step}"):
                    user_ans = True
                if col_f.button("FALSO", use_container_width=True, key=f"f_{step}"):
                    user_ans = False

                if user_ans is not None:
                    is_correct = (user_ans == item.get("is_true"))
                    if is_correct:
                        st.success("🎉 **¡Correcto!** +5 Puntos")
                        st.session_state.score += 5
                        st.session_state.correct_count += 1
                    else:
                        st.error("❌ **Incorrecto.**")
                        st.session_state.failed_count += 1
                        st.session_state.failed_questions_history.append({
                            "statement": item.get("statement"),
                            "user_answer": "Verdadero" if user_ans else "Falso",
                            "correct_answer": "Verdadero" if item.get("is_true") else "Falso",
                            "explanation": item.get("explanation")
                        })
                    st.info(f"**Explicación:** {item.get('explanation')}")
                    st.session_state.game_step += 1
                    if st.button("Continuar a la siguiente pregunta"):
                        st.rerun()
            else:
                st.success("🏁 ¡Has completado las 10 preguntas de la Batalla de Conceptos!")
                if st.button("Ver Recomendaciones de Estudio"):
                    st.session_state.active_game = "summary"
                    st.rerun()

        # 3. THE SYNAPSE SORTER GAME (FULL DEFINITIONS PREVIEW CARDS)
        elif active_g == "synapse_sorter" and st.session_state.game_data:
            gdata = st.session_state.game_data
            pairs = gdata.get("pairs", [])
            st.markdown(f"#### 🧠 {gdata.get('title', 'Clasificador Sináptico')}")
            st.markdown("Lea las definiciones completas a continuación y empareje cada término con su definición correspondiente:")
            
            terms = [p["term"] for p in pairs]
            all_defs = [p["definition"] for p in pairs]
            if "shuffled_defs" not in st.session_state:
                import random
                shuffled = list(all_defs)
                random.seed(42)
                random.shuffle(shuffled)
                st.session_state.shuffled_defs = shuffled
            else:
                shuffled = st.session_state.shuffled_defs

            # Render Full Definition Cards
            st.markdown("##### 📖 Tarjetas de Definiciones Completas:")
            col_d1, col_d2 = st.columns(2)
            for idx_d, def_text in enumerate(shuffled, 1):
                target_col = col_d1 if idx_d % 2 != 0 else col_d2
                target_col.markdown(f"""
                <div style="background-color: #F8FAFC; border-left: 4px solid #3B82F6; padding: 10px 14px; border-radius: 8px; margin-bottom: 10px;">
                    <strong>Definición {idx_d}:</strong><br>
                    <em>"{def_text}"</em>
                </div>
                """, unsafe_allow_html=True)

            # Build dropdown options referencing the cards
            def_options = ["-- Seleccionar Definición --"]
            def_map = {}
            for idx_d, def_text in enumerate(shuffled, 1):
                lbl = f"Definición {idx_d}"
                def_options.append(lbl)
                def_map[lbl] = def_text

            user_matches = {}
            with st.form("synapse_form"):
                st.markdown("##### 🎯 Empareje cada Término:")
                for idx, term in enumerate(terms):
                    sel_lbl = st.selectbox(
                        f"**Término {idx+1}: {term}**",
                        options=def_options,
                        key=f"match_{idx}"
                    )
                    user_matches[term] = def_map.get(sel_lbl, "")
                    
                submitted_sort = st.form_submit_button("Enviar Emparejamientos")
                if submitted_sort:
                    st.session_state.synapse_submitted = True
                    st.session_state.synapse_user_matches = user_matches

            if st.session_state.get("synapse_submitted", False):
                user_m = st.session_state.get("synapse_user_matches", {})
                correct_round = 0
                for p in pairs:
                    t = p["term"]
                    correct_d = p["definition"]
                    chosen_d = user_m.get(t)
                    if chosen_d == correct_d:
                        correct_round += 1
                    else:
                        st.session_state.failed_questions_history.append({
                            "term": t,
                            "user_answer": chosen_d,
                            "correct_answer": correct_d,
                            "explanation": f"La definición exacta para {t} es: {correct_d}"
                        })
                st.session_state.score += (correct_round * 5)
                st.session_state.correct_count += correct_round
                st.session_state.failed_count += (len(pairs) - correct_round)
                
                st.success(f"🎉 ¡Emparejaste correctamente {correct_round} de {len(pairs)} términos!")
                
                if st.button(" Ver Análisis Inteligente y Recomendaciones", type="primary"):
                    st.session_state.active_game = "summary"
                    st.session_state.synapse_submitted = False
                    if "shuffled_defs" in st.session_state:
                        del st.session_state["shuffled_defs"]
                    st.rerun()

        # 4. POST-GAME SUMMARY & SMART RECOMMENDATIONS
        elif active_g == "summary":
            st.markdown("### 🏆 Resumen de la Sesión de Evaluación")
            c_sc1, c_sc2, c_sc3 = st.columns(3)
            c_sc1.metric("Puntuación Total", st.session_state.score)
            c_sc2.metric("Total Aciertos", st.session_state.correct_count)
            c_sc3.metric("Total Fallos", st.session_state.failed_count)
            
            st.markdown("---")
            st.markdown("### 🤖 Recomendaciones de Estudio Inteligentes (IA)")
            st.caption("Análisis automático en español de sus puntos débiles respecto a sus documentos PDF:")
            
            if st.session_state.recommendation_text is None:
                rec = generate_post_game_recommendations(
                    st.session_state.failed_questions_history,
                    st.session_state.user_selected_pdfs,
                    model_name=selected_model
                )
                st.session_state.recommendation_text = rec
            
            st.markdown(st.session_state.recommendation_text)
            
            col_rs1, col_rs2 = st.columns(2)
            if col_rs1.button("🎮 Jugar Otra Evaluación", use_container_width=True):
                st.session_state.active_game = None
                st.session_state.recommendation_text = None
                st.rerun()
            if col_rs2.button("📚 Consultar al Asistente sobre Mis Puntos Débiles", use_container_width=True):
                st.session_state.active_game = None
                st.rerun()

# ==========================================
# PESTAÑA 3: ASISTENTE DE ESTUDIO Y CONSULTAS
# ==========================================
with tab_study:
    st.header("📚 Asistente de Estudio y Consultas en Español")
    st.markdown("Realice preguntas conceptuales profundas fundamentadas estrictamente en sus documentos de psicología en español.")
    
    col_q1, col_q2 = st.columns([3, 1])
    
    with col_q2:
        st.subheader("Filtrar Documento PDF")
        all_pdfs = list_uploaded_pdfs()
        
        # Enhanced PDF Selector Combobox
        combobox_options = ["📄 Todos los Documentos PDF Indexados"] + all_pdfs
        chosen_pdf_combo = st.selectbox(
            "📖 Seleccionar Documento PDF de Consulta:",
            options=combobox_options,
            index=0,
            help="Elija un documento específico o busque en todos los PDFs indexados."
        )
        
        if chosen_pdf_combo == "📄 Todos los Documentos PDF Indexados":
            study_selected_pdfs = all_pdfs
            st.caption(f"Buscando en **todos** los {len(all_pdfs)} documentos.")
        else:
            study_selected_pdfs = [chosen_pdf_combo]
            st.caption(f"Filtro activo: **{chosen_pdf_combo}**")
        
        st.markdown("#### Consultas de Ejemplo")
        if st.button("¿Qué es la TCC y las distorsiones cognitivas?"):
            st.session_state.user_q_input = "¿Qué es la Terapia Cognitivo-Conductual y cuáles son las principales distorsiones cognitivas?"
            st.rerun()
        if st.button("Diferencia entre hipocampo y amígdala"):
            st.session_state.user_q_input = "Explique la diferencia de funciones entre el hipocampo y la amígdala en el procesamiento de la memoria."
            st.rerun()
        if st.button("Criterios del Trastorno de Ansiedad"):
            st.session_state.user_q_input = "¿Cuáles son los criterios diagnósticos principales para el Trastorno de Ansiedad Generalizada?"
            st.rerun()

    with col_q1:
        query_input = st.text_input("Ingrese su pregunta conceptual en español:", key="user_q_input")
        
        col_btn1, col_btn2 = st.columns([2, 1])
        with col_btn1:
            if st.button("Consultar al Asistente", type="primary", use_container_width=True):
                query_val = st.session_state.get("user_q_input", "").strip()
                if not query_val:
                    st.warning("Por favor ingrese una pregunta.")
                else:
                    with st.spinner("Buscando en el documento PDF seleccionado..."):
                        result = query_study_assistant(
                            query=query_val,
                            selected_filenames=study_selected_pdfs,
                            model_name=selected_model
                        )
                        st.session_state.current_qa_query = query_val
                        st.session_state.current_qa_result = result
                            
        with col_btn2:
            if st.button("🧹 Limpiar Respuesta", use_container_width=True):
                st.session_state.user_q_input = ""
                st.session_state.current_qa_query = None
                st.session_state.current_qa_result = None
                st.rerun()

        st.markdown("---")
        
        # Display ONLY the CURRENT response card (clean dedicated view)
        if st.session_state.get("current_qa_result") and st.session_state.get("current_qa_query"):
            res = st.session_state.current_qa_result
            query_title = st.session_state.current_qa_query
            
            st.markdown(f"### ❓ Consulta Actual: *\"{query_title}\"*")
            st.markdown(res.get("answer"))
            
            st.success(f"**🎯 Plan de Estudio Personalizado:**\n\n{res.get('study_plan')}")
            
            citations = res.get("citations", [])
            if citations:
                st.markdown("### 📖 Citas del Documento PDF Seleccionado")
                for cite in citations:
                    st.markdown(f"""
                    <div class="citation-box">
                        <strong>[{cite['id']}] Fuente:</strong> {cite['source']} (Página {cite['page']})<br>
                        <em>"{cite['snippet']}"</em>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Escriba una pregunta conceptual arriba o haga clic en un ejemplo para consultar el documento PDF seleccionado.")
