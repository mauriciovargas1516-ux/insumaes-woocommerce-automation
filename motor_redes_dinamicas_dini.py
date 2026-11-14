# -*- coding: utf-8 -*-
"""
EXTENSIÓN INTERACTIVA: REDES DINÁMICAS (DINI 2010 / 04 SPL), BURBUJAS DE TIPS
Y GRADIENTE DE CONCENTRACIÓN (REDES + ORDENAMIENTO TERRITORIAL)
Asignatura: Desarrollo y Gestión Territorial — Universidad de Los Lagos (Prof. Claudio Mancilla)
Archivo: motor_redes_dinamicas_dini.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ==============================================================================
# 1. COMPONENTE DE BURBUJAS INFORMATIVAS (POPUP / TOOLTIP PEDAGÓGICO)
# ==============================================================================
def renderizar_burbuja_tip(titulo_boton: str, titulo_interno: str, explicacion_md: str, formula_latex: str = None):
    """
    Crea una burbuja interactiva (popover) que al hacer clic despliega la explicación
    conceptual, la fórmula matemática y la regla de interpretación de las cifras.
    """
    contenedor = st.popover(f"💡 {titulo_boton}", use_container_width=True) if hasattr(st, "popover") else st.expander(f"💡 {titulo_boton}")
    with contenedor:
        st.markdown(f"#### {titulo_interno}")
        if formula_latex:
            st.latex(formula_latex)
        st.markdown(explicacion_md)


def inyectar_estilos_burbujas():
    st.markdown(
        """
        <style>
        .tip-badge {
            display: inline-block;
            background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
            color: #1e3a8a;
            border: 1px solid #93c5fd;
            border-radius: 18px;
            padding: 6px 14px;
            font-size: 0.86rem;
            font-weight: 600;
            margin-bottom: 8px;
            box-shadow: 0 1px 3px rgba(30, 58, 138, 0.08);
        }
        .cifra-card {
            background-color: #ffffff;
            border-left: 4px solid #2563eb;
            border-top: 1px solid #e2e8f0;
            border-right: 1px solid #e2e8f0;
            border-bottom: 1px solid #e2e8f0;
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==============================================================================
# 2. GENERADOR DE LAS TOPOLOGÍAS OFICIALES DE CÁTEDRA (DINI, 2010 — 04 SPL.PDF)
# ==============================================================================
def obtener_topologia_dini(tipo_red: str, n_nodos: int = 8):
    """
    Genera las coordenadas (x, y), nombres de nodos y lista ordenada de enlaces (L)
    para las estructuras de Dini (2010) en '04 SPL.pdf' (Diagramas 2, 3 y 4, pág. 14).
    """
    if "1. Red Simétrica" in tipo_red:
        n = n_nodos
        nombres = [f"PyME {i+1}" for i in range(n)]
        roles = ["Socio Horizontal" for _ in range(n)]
        angulos = np.linspace(0, 2 * np.pi, n, endpoint=False)
        xs = np.cos(angulos)
        ys = np.sin(angulos)
        # Anillo completo + diagonales simétricas para que todos tengan el mismo grado
        enlaces = []
        for i in range(n):
            enlaces.append((i, (i + 1) % n))
        for i in range(n):
            j = (i + 2) % n
            if (j, i) not in enlaces and (i, j) not in enlaces:
                enlaces.append((i, j))
        descripcion = (
            "**Red Simétrica (Dini, 2010 — Diagrama 2):** Cooperación horizontal donde todas las empresas "
            "poseen el mismo grado nodal ($k_i$ constante). No existe un líder hegemónico; las decisiones se "
            "toman por consenso y el **Gradiente de Concentración es 0%**."
        )

    elif "2. Red con Liderazgo" in tipo_red:
        n = n_nodos
        nombres = ["Empresa Líder / Articuladora"] + [f"Proveedor / PyME {i}" for i in range(1, n)]
        roles = ["Nodo Líder (Hub Central)"] + ["Socio Articulado" for _ in range(1, n)]
        xs = [0.0]
        ys = [0.0]
        angulos = np.linspace(0, 2 * np.pi, n - 1, endpoint=False)
        for ang in angulos:
            xs.append(float(np.cos(ang)))
            ys.append(float(np.sin(ang)))
        xs = np.array(xs)
        ys = np.array(ys)
        enlaces = [(0, i) for i in range(1, n)]
        descripcion = (
            "**Red con Liderazgo (Dini, 2010 — Diagrama 2):** Estructura radial tipo estrella. "
            "Un actor central (ej. planta procesadora o gremio coordinador) conecta a todas las PyMEs periféricas. "
            "Alcanza el **Gradiente de Concentración máximo (100%)**, pero alta vulnerabilidad si falla el líder."
        )

    elif "3. Red Jerárquica" in tipo_red:
        # Estructura piramidal de 3 niveles (1 Matriz -> 2 Sub-líderes -> Nodos operativos)
        nombres = [
            "1. Empresa Matriz / Ancla",
            "2. Contratista Nivel 1A",
            "3. Contratista Nivel 1B",
            "4. Taller Subcontratista 2A",
            "5. Taller Subcontratista 2B",
            "6. Taller Subcontratista 2C",
            "7. Proveedor Insumos 2D",
        ]
        roles = [
            "Cúpula Jerárquica (Nivel 1)",
            "Mando Intermedio (Nivel 2)",
            "Mando Intermedio (Nivel 2)",
            "Base Operativa (Nivel 3)",
            "Base Operativa (Nivel 3)",
            "Base Operativa (Nivel 3)",
            "Base Operativa (Nivel 3)",
        ]
        xs = np.array([0.0, -0.65, 0.65, -1.0, -0.35, 0.35, 1.0])
        ys = np.array([1.0, 0.2, 0.2, -0.7, -0.7, -0.7, -0.7])
        enlaces = [
            (0, 1), (0, 2),
            (1, 3), (1, 4),
            (2, 5), (2, 6),
        ]
        descripcion = (
            "**Red Jerárquica (Dini, 2010 — Diagrama 2):** Organización vertical piramidal típica de "
            "esquemas de subcontratación escalonada (*Outsourcing*). El flujo productivo y de autoridad "
            "desciende por niveles sin puentes horizontales entre la base."
        )

    elif "4. Red de Redes (Diagrama 3)" in tipo_red:
        # 3 sub-redes (clústeres locales) cuyos nodos negros líderes se conectan entre sí
        nombres = [
            "Líder Clúster A (Osorno)", "PyME A1", "PyME A2", "PyME A3",
            "Líder Clúster B (Puerto Montt)", "PyME B1", "PyME B2", "PyME B3",
            "Líder Clúster C (Valdivia)", "PyME C1", "PyME C2", "PyME C3",
        ]
        roles = [
            "Nodo Puente / Líder Subred", "Miembro Subred A", "Miembro Subred A", "Miembro Subred A",
            "Nodo Puente / Líder Subred", "Miembro Subred B", "Miembro Subred B", "Miembro Subred B",
            "Nodo Puente / Líder Subred", "Miembro Subred C", "Miembro Subred C", "Miembro Subred C",
        ]
        xs = np.array([-1.0, -1.5, -1.4, -0.9,  0.9, 1.4, 1.5, 0.7,  0.1, -0.3, 0.5, 0.1])
        ys = np.array([ 0.5,  0.9,  0.2, -0.1,  0.7, 0.9, 0.3, 0.1, -0.8, -1.2,-1.2,-0.3])
        enlaces = [
            # Puentes entre los 3 líderes negros (Triángulo central del Diagrama 3)
            (0, 4), (4, 8), (0, 8),
            # Subred A (Estrella local)
            (0, 1), (0, 2), (0, 3),
            # Subred B (Con malla parcial)
            (4, 5), (4, 6), (4, 7), (6, 7),
            # Subred C (Con triángulo interno)
            (8, 9), (8, 10), (8, 11), (10, 11),
        ]
        descripcion = (
            "**Red de Redes (Dini, 2010 — Diagrama 3, pág. 14):** Articulación de segundo grado donde tres "
            "redes locales mantienen su cohesión interna, pero sus nodos líderes (nodos puente) se conectan "
            "entre sí para alcanzar escala interregional."
        )

    else:
        # 5. Red de Redes en la Producción de Aviones (Diagrama 4 de Dini, pág. 14)
        nombres = [
            "GRAN ENSAMBLADORA CENTRAL (Hub Global)",
            "Sub-Líder Motores (N1)", "Taller Turbinas A", "Taller Turbinas B", "Taller Turbinas C",
            "Sub-Líder Aviónica (N2)", "Software Vuelo A", "Sensores B", "Radar C",
            "Sub-Líder Fuselaje (N3)", "Aleaciones A", "Tren Aterrizaje B", "Cabina C",
        ]
        roles = [
            "Gran Nodo Integrador Central",
            "Líder Subsistema", "Proveedor Especializado", "Proveedor Especializado", "Proveedor Especializado",
            "Líder Subsistema", "Proveedor Especializado", "Proveedor Especializado", "Proveedor Especializado",
            "Líder Subsistema", "Proveedor Especializado", "Proveedor Especializado", "Proveedor Especializado",
        ]
        xs = np.array([0.0,  -1.1, -1.6, -1.6, -1.0,   1.1, 1.6, 1.5, 0.8,   0.1, -0.4, 0.6, 0.1])
        ys = np.array([0.0,   0.4,  0.8,  0.1, -0.2,   0.6, 0.9, 0.2, 0.0,  -0.9, -1.3,-1.3,-0.4])
        enlaces = [
            # Gran nodo central conecta a los 3 líderes de subsistema
            (0, 1), (0, 5), (0, 9),
            # Subsistema 1
            (1, 2), (1, 3), (1, 4),
            # Subsistema 2
            (5, 6), (5, 7), (5, 8), (7, 8),
            # Subsistema 3
            (9, 10), (9, 11), (9, 12), (10, 12),
        ]
        descripcion = (
            "**Red de Redes en la Producción de Aviones (Dini, 2010 — Diagrama 4, pág. 14):** "
            "Una gran empresa integradora al centro coordina a los líderes de cada subsistema tecnológico, "
            "quienes a su vez articulan sus propios clústeres de proveedores especializados."
        )

    return nombres, roles, xs, ys, enlaces, descripcion


# ==============================================================================
# 3. CÁLCULO MATEMÁTICO DE CIFRAS DE RED EN CADA PASO DE ARMADO
# ==============================================================================
def calcular_metricas_red_en_paso(nombres, roles, enlaces_activos):
    """
    Calcula en vivo:
    - n (número de empresas/nodos)
    - L (número de vínculos activos en el paso actual)
    - Grado nodal k_i de cada empresa
    - Densidad D = 2L / (n*(n-1)) (Fórmula exacta de Dini 2010, pág. 14)
    - Gradiente de Concentración / Centralización de Freeman C_D
    - Cuota de articulación de cada nodo (%)
    """
    n = len(nombres)
    L = len(enlaces_activos)
    A = np.zeros((n, n), dtype=int)
    for u, v in enlaces_activos:
        if 0 <= u < n and 0 <= v < n and u != v:
            A[u, v] = 1
            A[v, u] = 1

    grados = A.sum(axis=1)
    max_enlaces_posibles = (n * (n - 1)) / 2.0 if n > 1 else 1.0
    # Fórmula explícita lámina 14 de 04 SPL.pdf: DENSIDAD = 2L / (n*(n-1))
    densidad = (2.0 * L) / (n * (n - 1.0)) if n > 1 else 0.0

    k_max = int(np.max(grados)) if n > 0 else 0
    k_min = int(np.min(grados)) if n > 0 else 0
    k_prom = float(np.mean(grados)) if n > 0 else 0.0

    # Centralización / Gradiente de Concentración de la Red (Freeman)
    denom_freeman = float((n - 1) * (n - 2)) if n > 2 else 1.0
    gradiente_concentracion = float(np.sum(k_max - grados) / denom_freeman) if n > 2 else 0.0
    gradiente_concentracion = min(max(gradiente_concentracion, 0.0), 1.0)

    suma_grados = max(int(np.sum(grados)), 1)
    cuota_vinculos_pct = (grados / suma_grados) * 100.0
    centralidad_local_pct = (grados / max(n - 1, 1)) * 100.0

    df_nodos = pd.DataFrame({
        "ID_Nodo": [f"N{i+1}" for i in range(n)],
        "Empresa_Actor": nombres,
        "Rol_en_la_Red": roles,
        "Grado_Vinculos_ki": grados,
        "Centralidad_Grado_%": np.round(centralidad_local_pct, 1),
        "Cuota_Concentracion_Red_%": np.round(cuota_vinculos_pct, 1),
        "Brecha_vs_Lider_(kmax-ki)": k_max - grados,
    }).sort_values("Grado_Vinculos_ki", ascending=False).reset_index(drop=True)

    resumen = {
        "n": n,
        "L": L,
        "L_max": int(max_enlaces_posibles),
        "densidad_prop": densidad,
        "densidad_pct": densidad * 100.0,
        "k_max": k_max,
        "k_min": k_min,
        "k_prom": k_prom,
        "gradiente_conc_prop": gradiente_concentracion,
        "gradiente_conc_pct": gradiente_concentracion * 100.0,
        "matriz_A": A,
    }
    return resumen, df_nodos


# ==============================================================================
# 4. CONSTRUCTOR DE GRAFO ANIMADO EN PLOTLY ("VER LA RED ARMARSE EN VIVO")
# ==============================================================================
def construir_figura_red_animada(nombres, roles, xs, ys, todos_enlaces, paso_actual, mostrar_cifras_nodos=True):
    """
    Genera una figura interactiva de Plotly que:
    1. Muestra el estado exacto en `paso_actual` con cifras vivas sobre cada nodo.
    2. Incorpora `frames` de animación y botón Play ▶ para ver la red armarse enlace por enlace.
    """
    n = len(nombres)

    def _trazas_para_k_enlaces(k_step):
        sub_enlaces = todos_enlaces[:k_step]
        res_k, _ = calcular_metricas_red_en_paso(nombres, roles, sub_enlaces)
        A_k = res_k["matriz_A"]
        grados_k = A_k.sum(axis=1)
        cent_k = (grados_k / max(n - 1, 1)) * 100.0

        edge_x, edge_y = [], []
        for u, v in sub_enlaces:
            edge_x.extend([xs[u], xs[v], None])
            edge_y.extend([ys[u], ys[v], None])

        # Si hay un último enlace recién agregado, lo destacamos en dorado/rojo vivo
        ult_x, ult_y = [], []
        if k_step > 0:
            u_last, v_last = sub_enlaces[-1]
            ult_x = [xs[u_last], xs[v_last]]
            ult_y = [ys[u_last], ys[v_last]]

        textos_visibles = []
        textos_hover = []
        for i in range(n):
            if mostrar_cifras_nodos:
                textos_visibles.append(f"<b>{nombres[i]}</b><br>k={grados_k[i]} ({cent_k[i]:.0f}%)")
            else:
                textos_visibles.append(f"<b>{nombres[i]}</b>")

            textos_hover.append(
                f"<b>{nombres[i]}</b><br>"
                f"Rol: {roles[i]}<br>"
                f"Grado actual (k_i): <b>{grados_k[i]} vínculos</b><br>"
                f"Centralidad local: <b>{cent_k[i]:.1f}%</b><br>"
                f"Densidad global en este paso: <b>{res_k['densidad_pct']:.1f}%</b>"
            )

        traza_enlaces = go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=2.6, color="#64748b"),
            hoverinfo="none",
            name="Vínculos consolidados",
        )
        traza_ultimo = go.Scatter(
            x=ult_x,
            y=ult_y,
            mode="lines",
            line=dict(width=4.5, color="#dc2626", dash="solid"),
            hoverinfo="none",
            name="Último vínculo armado",
        )
        traza_nodos = go.Scatter(
            x=xs,
            y=ys,
            mode="markers+text",
            text=textos_visibles,
            textposition="top center",
            hovertext=textos_hover,
            hoverinfo="text",
            marker=dict(
                size=24 + grados_k * 5.5,
                color=cent_k,
                colorscale="YlOrRd",
                cmin=0,
                cmax=100,
                showscale=True,
                colorbar=dict(title="Centralidad (%)"),
                line=dict(width=2.2, color="#0f172a"),
            ),
            name="Empresas / Nodos",
        )
        return [traza_enlaces, traza_ultimo, traza_nodos], res_k

    trazas_actuales, res_actual = _trazas_para_k_enlaces(paso_actual)

    # Construimos los frames de animación desde 0 hasta L enlaces
    frames = []
    for k_f in range(0, len(todos_enlaces) + 1):
        trazas_f, res_f = _trazas_para_k_enlaces(k_f)
        frames.append(
            go.Frame(
                data=trazas_f,
                name=f"Paso_{k_f}",
                layout=go.Layout(
                    title_text=(
                        f"Armando la Red en Vivo — Paso {k_f}/{len(todos_enlaces)} | "
                        f"Vínculos L={res_f['L']} | Densidad D = 2L/[n(n-1)] = {res_f['densidad_pct']:.1f}% | "
                        f"Gradiente Concentración = {res_f['gradiente_conc_pct']:.1f}%"
                    )
                ),
            )
        )

    fig = go.Figure(data=trazas_actuales, frames=frames)
    fig.update_layout(
        title=(
            f"Red en Vivo (Paso {paso_actual}/{len(todos_enlaces)}): "
            f"L = {res_actual['L']} vínculos | Densidad D = {res_actual['densidad_pct']:.1f}% "
            f"({res_actual['densidad_prop']:.3f}) | Gradiente Concentración = {res_actual['gradiente_conc_pct']:.1f}%"
        ),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-2.0, 2.0]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1.7, 1.5]),
        height=560,
        margin=dict(l=20, r=20, t=65, b=85),
        plot_bgcolor="#f8fafc",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                x=0.0,
                y=-0.12,
                xanchor="left",
                yanchor="top",
                buttons=[
                    dict(
                        label="▶ Play (Ver Armarse la Red Paso a Paso)",
                        method="animate",
                        args=[
                            None,
                            dict(
                                frame=dict(duration=650, redraw=True),
                                transition=dict(duration=250),
                                fromcurrent=False,
                                mode="immediate",
                            ),
                        ],
                    ),
                    dict(
                        label="⏸ Pausar",
                        method="animate",
                        args=[
                            [None],
                            dict(
                                frame=dict(duration=0, redraw=False),
                                mode="immediate",
                                transition=dict(duration=0),
                            ),
                        ],
                    ),
                ],
            )
        ],
    )
    return fig


# ==============================================================================
# 5. INTERFAZ PRINCIPAL DEL MÓDULO DE EXTENSIÓN EN STREAMLIT
# ==============================================================================
def renderizar_extension_redes_y_gradientes():
    inyectar_estilos_burbujas()

    st.header("8. Extensión Interactiva: Redes Empresariales (Dini) y Gradientes de Concentración")
    st.markdown(
        '<span class="tip-badge">✨ Modo Pedagógico Activo: Haz clic en las burbujas 💡 para descubrir qué significa cada concepto y cada cifra</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "Módulo interactivo que integra las **3 Estructuras de Redes Empresariales de Dini (2010, CEPAL)** y las "
        "**3 Visiones de Articulación Productiva (`04 SPL.pdf`)** con el **Simulador de Gradiente de Concentración "
        "(Red + Primacía Urbana + Complejidad de Guttman + Renta de von Thünen)**."
    )

    tabs = st.tabs([
        "1. Constructor Animado de Redes en Vivo (Dini 2010 — 04 SPL)",
        "2. Gradiente de Concentración: Primacía, Guttman y von Thünen",
        "3. Comparador Interactivo:Las 3 Visiones (Red, Clúster y SPL)",
    ])

    # ==========================================================================
    # PESTAÑA 1: CONSTRUCTOR Y ANIMADOR DE REDES EN VIVO (DINI 2010)
    # ==========================================================================
    with tabs[0]:
        st.subheader("Simulador Visual: Mira la Red Armarse Frente a tus Ojos con sus Cifras")

        col_sel1, col_sel2, col_sel3 = st.columns([2.2, 1.1, 1.2])
        with col_sel1:
            tipo_red_sel = st.selectbox(
                "Seleccione Estructura de Red de Cátedra (`04 SPL.pdf`, pág. 14):",
                [
                    "1. Red Simétrica (Cooperación Horizontal Pares — Diagrama 2)",
                    "2. Red con Liderazgo (Empresa Líder / Estrella — Diagrama 2)",
                    "3. Red Jerárquica (Piramidal por Niveles — Diagrama 2)",
                    "4. Red de Redes (Articulación entre Clústeres — Diagrama 3)",
                    "5. Red de Redes en la Producción de Aviones (Hub Central — Diagrama 4)",
                ],
            )
        with col_sel2:
            n_nodos_sim = st.slider(
                "Número de empresas (n):",
                min_value=5,
                max_value=12,
                value=8,
                disabled=("3." in tipo_red_sel or "4." in tipo_red_sel or "5." in tipo_red_sel),
                help="Para Red Simétrica y Red con Liderazgo puedes variar n libremente entre 5 y 12 empresas.",
            )
        with col_sel3:
            mostrar_cifras = st.checkbox("Mostrar cifras (k y %) sobre cada nodo", value=True)

        nombres, roles, xs, ys, enlaces_totales, desc_topologia = obtener_topologia_dini(tipo_red_sel, n_nodos_sim)
        max_pasos = len(enlaces_totales)

        st.info(desc_topologia)

        # Slider para armar/desarmar la red paso a paso manualmente (además del botón Play)
        paso_actual = st.slider(
            "🔧 Desliza para armar la red vínculo por vínculo (o presiona ▶ Play debajo del gráfico):",
            min_value=0,
            max_value=max_pasos,
            value=max_pasos,
            step=1,
        )

        enlaces_activos = enlaces_totales[:paso_actual]
        res_red, df_nodos_vivo = calcular_metricas_red_en_paso(nombres, roles, enlaces_activos)

        # Fila de KPIs con sus respectivas Burbujas de Tips Informativos
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric(
                "1. Empresas (n) y Vínculos (L)",
                f"n = {res_red['n']} | L = {res_red['L']}",
                f"Máx posible: {res_red['L_max']} vínculos",
            )
            renderizar_burbuja_tip(
                titulo_boton="¿Qué son n y L?",
                titulo_interno="Nodos (n) y Vínculos Activos (L)",
                formula_latex=r"L_{\max} = \frac{n(n-1)}{2}",
                explicacion_md=(
                    "- **$n$ (Nodos):** Cantidad de empresas, productores o instituciones que integran la red.\n"
                    "- **$L$ (Vínculos / Líneas):** Acuerdos reales de cooperación, compraventa o transferencia de información activos en este paso.\n"
                    f"- **Lectura de tu cifra actual:** De los **{res_red['L_max']}** vínculos bilaterales posibles entre estas {res_red['n']} empresas, actualmente existen **{res_red['L']}** activos."
                ),
            )

        with k2:
            st.metric(
                "2. Densidad de la Red (Dini)",
                f"{res_red['densidad_pct']:.1f}%",
                f"D = {res_red['densidad_prop']:.3f} (0 a 1)",
            )
            renderizar_burbuja_tip(
                titulo_boton="Fórmula de Densidad D",
                titulo_interno="Densidad de la Red (Dini 2010 / 04 SPL pág. 14)",
                formula_latex=r"D = \frac{2L}{n(n-1)}",
                explicacion_md=(
                    "- **Concepto:** Mide qué proporción de todos los vínculos teóricamente posibles entre las empresas se encuentran efectivamente activos.\n"
                    f"- **Cálculo en vivo:** $D = \\frac{{2 \\times {res_red['L']}}}{{{res_red['n']} \\times ({res_red['n']}-1)}} = {res_red['densidad_prop']:.4f}$ (**{res_red['densidad_pct']:.1f}%**).\n"
                    "- **¿Qué significa la cifra?:**\n"
                    "  - **$D > 50\\%$:** Alta cohesión horizontal y confianza mutua (rápida difusión de aprendizaje).\n"
                    "  - **$D < 30\\%$:** Red dispersa o altamente dependiente de un único nodo articulador."
                ),
            )

        with k3:
            st.metric(
                "3. Grado Nodal Máximo y Medio",
                f"k_máx = {res_red['k_max']}",
                f"Promedio k̄ = {res_red['k_prom']:.2f} vínculos/empresa",
            )
            renderizar_burbuja_tip(
                titulo_boton="¿Qué es el Grado Nodal?",
                titulo_interno="Grado de una Empresa en la Red (k_i)",
                formula_latex=r"k_i = \sum_{j=1}^{n} a_{ij}",
                explicacion_md=(
                    "- **Definición (`04 SPL.pdf`, pág. 14):** *'Grado = Número de vínculos de una empresa con las otras'*.\n"
                    f"- **Lectura de tu cifra actual:** El actor más conectado tiene **{res_red['k_max']} vínculos directos**, mientras que el actor menos conectado tiene **{res_red['k_min']}**.\n"
                    "- Una empresa con alto grado actúa como **articulador o gobernanza de la red**."
                ),
            )

        with k4:
            st.metric(
                "4. Gradiente de Concentración",
                f"{res_red['gradiente_conc_pct']:.1f}%",
                "Simétrica (0%) ↔ Líder (100%)",
            )
            renderizar_burbuja_tip(
                titulo_boton="¿Qué es el Gradiente?",
                titulo_interno="Gradiente de Concentración / Centralización de la Red",
                formula_latex=r"GC_{red} = \frac{\sum_{i=1}^{n} (k_{\max} - k_i)}{(n-1)(n-2)}",
                explicacion_md=(
                    "- **Concepto:** Mide qué tan empinada es la jerarquía de poder entre el nodo líder ($k_{\\max}$) y el resto de las empresas.\n"
                    "- **Cómo leer esta cifra en tu informe:**\n"
                    "  - **$0\\%$ a $15\\%$:** **Red Simétrica** (ningún actor monopoliza la intermediación).\n"
                    "  - **$25\\%$ a $65\\%$:** **Red Jerárquica o Policéntrica** (existen mandos medios o sub-líderes).\n"
                    "  - **$70\\%$ a $100\\%$:** **Red con Liderazgo Fuerte** (toda la coordinación pasa por un único centro)."
                ),
            )

        # Renderizado del Grafo Animado y Curva de Gradiente lado a lado
        col_grafo, col_grad = st.columns([1.45, 1.0])
        with col_grafo:
            fig_anim = construir_figura_red_animada(
                nombres=nombres,
                roles=roles,
                xs=xs,
                ys=ys,
                todos_enlaces=enlaces_totales,
                paso_actual=paso_actual,
                mostrar_cifras_nodos=mostrar_cifras,
            )
            st.plotly_chart(fig_anim, use_container_width=True)

        with col_grad:
            st.markdown("##### Curva de Gradiente de Concentración Nodal ($k_i$ ordenado)")
            fig_grad_red = go.Figure()
            fig_grad_red.add_trace(
                go.Bar(
                    x=df_nodos_vivo["Empresa_Actor"],
                    y=df_nodos_vivo["Grado_Vinculos_ki"],
                    marker_color="#2563eb",
                    name="Grado Nodal (k_i)",
                    text=df_nodos_vivo["Grado_Vinculos_ki"],
                    textposition="outside",
                )
            )
            fig_grad_red.add_trace(
                go.Scatter(
                    x=df_nodos_vivo["Empresa_Actor"],
                    y=df_nodos_vivo["Grado_Vinculos_ki"],
                    mode="lines+markers",
                    line=dict(color="#dc2626", width=3, dash="dot"),
                    name="Pendiente / Gradiente Jerárquico",
                )
            )
            fig_grad_red.update_layout(
                height=310,
                margin=dict(l=10, r=10, t=25, b=40),
                yaxis_title="N° de Vínculos (Grado k_i)",
                xaxis_title="Empresas ordenadas de Mayor a Menor Jerarquía",
                showlegend=True,
                legend=dict(orientation="h", y=1.12),
            )
            st.plotly_chart(fig_grad_red, use_container_width=True)

            st.markdown("##### Tabla de Cifras por Empresa en Tiempo Real")
            st.dataframe(df_nodos_vivo, use_container_width=True, hide_index=True, height=215)

    # ==========================================================================
    # PESTAÑA 2: GRADIENTE DE CONCENTRACIÓN TERRITORIAL (PRIMACÍA, GUTTMAN Y VON THÜNEN)
    # ==========================================================================
    with tabs[1]:
        st.subheader("Fórmulas de Concentración Territorial y Gradientes Espaciales (`06 OT 2024.pdf`)")
        st.markdown(
            "Conecta la concentración de redes con los **3 indicadores de jerarquía y gradiente espacial** vistos en clases: "
            "**1) Índice de Primacía Urbana**, **2) Gradiente Funcional de Guttman / Rondinelli** y "
            "**3) Gradiente de Renta y Distancia de von Thünen**."
        )

        c_ot1, c_ot2 = st.columns(2)

        with c_ot1:
            st.markdown("#### A. Calculadora Interactiva de Índice de Primacía ($IP_4$) con Estandarización (0 a 3)")
            renderizar_burbuja_tip(
                titulo_boton="Ver Fórmula y Escala de Primacía (0 a 3)",
                titulo_interno="Índice de Primacía Urbana (`06 OT 2024.pdf`, láminas 11 y 12)",
                formula_latex=r"IP_4 = \frac{P_1}{P_2 + P_3 + P_4}",
                explicacion_md=(
                    "- **¿Qué mide?:** El peso relativo del principal centro poblado ($P_1$) respecto a la suma de los tres asentamientos que le siguen ($P_2 + P_3 + P_4$).\n"
                    "- **Ejemplo de lámina 12 del Prof. Mancilla:** Villa Esperanza ($5.520$) vs. El Rincón ($4.541$), Pueblo Nuevo ($122$) y El Quebradero ($50$) $\\rightarrow IP_4 = 5520 / (4541+122+50) = 1,171$.\n"
                    "- **Tabla Orientadora de Estandarización en Cátedra:**\n"
                    "  - **Valor 3 (Altamente Concentrada):** $IP_4 \\ge 1,50$ (Macrocefalia urbana).\n"
                    "  - **Valor 2 (Concentrada):** $1,00 \\le IP_4 < 1,50$.\n"
                    "  - **Valor 1 (Dispersa / Equilibrada):** $0,65 \\le IP_4 < 1,00$.\n"
                    "  - **Valor 0 (Muy Dispersa):** $IP_4 < 0,65$."
                ),
            )

            caso_prim = st.selectbox(
                "Cargar caso de estudio para Primacía:",
                [
                    "Región de Los Lagos — Censo 2024 (Puerto Montt, Osorno, Puerto Varas, Castro)",
                    "Región del Biobío — Censo 2024 (Concepción, Los Ángeles, Talcahuano, San Pedro)",
                    "Ejemplo Lámina 12 Prof. Mancilla (Villa Esperanza, El Rincón, Pueblo Nuevo, El Quebradero)",
                ],
            )
            if "Los Lagos" in caso_prim:
                noms_p = ["Puerto Montt (P1)", "Osorno (P2)", "Puerto Varas (P3)", "Castro (P4)"]
                vals_p = [275473, 174998, 50010, 48632]
            elif "Biobío" in caso_prim:
                noms_p = ["Concepción (P1)", "Los Ángeles (P2)", "Talcahuano (P3)", "San Pedro de la Paz (P4)"]
                vals_p = [238092, 218515, 158345, 148250]
            else:
                noms_p = ["Villa Esperanza (P1)", "El Rincón (P2)", "Pueblo Nuevo (P3)", "El Quebradero (P4)"]
                vals_p = [5520, 4541, 122, 50]

            p1 = st.number_input(f"Población {noms_p[0]}:", min_value=1, value=vals_p[0], step=500)
            p2 = st.number_input(f"Población {noms_p[1]}:", min_value=1, value=vals_p[1], step=500)
            p3 = st.number_input(f"Población {noms_p[2]}:", min_value=1, value=vals_p[2], step=100)
            p4 = st.number_input(f"Población {noms_p[3]}:", min_value=1, value=vals_p[3], step=100)

            suma_2_4 = p2 + p3 + p4
            ip_4 = p1 / max(suma_2_4, 1)
            ip_2 = p1 / max(p2, 1)

            if ip_4 >= 1.50:
                cat_prim, cod_prim = "Altamente Concentrada", 3
            elif ip_4 >= 1.00:
                cat_prim, cod_prim = "Concentrada", 2
            elif ip_4 >= 0.65:
                cat_prim, cod_prim = "Dispersa (Equilibrio Red Urbana)", 1
            else:
                cat_prim, cod_prim = "Muy Dispersa", 0

            st.success(
                f"**Resultado Índice de Primacía ($IP_4$):** `{ip_4:.4f}` | "
                f"**Primacía 2 Ciudades ($P_1/P_2$):** `{ip_2:.4f}`\n\n"
                f"**Clasificación Estandarizada (Lámina 11–12):** **{cat_prim} (Valor asignado = {cod_prim})**"
            )

        with c_ot2:
            st.markdown("#### B. Simulador de Gradiente Espacial de Renta y Concentración (von Thünen)")
            renderizar_burbuja_tip(
                titulo_boton="Fórmula de Gradiente de von Thünen",
                titulo_interno="Gradiente de Renta Locacional (`La_teoria_de_la_localizacion.pdf`, pág. 7)",
                formula_latex=r"LR(d) = Y(m - c) - Y \cdot t \cdot d",
                explicacion_md=(
                    "- **$LR(d)$:** Renta económica por unidad de suelo a una distancia $d$ del centro urbano.\n"
                    "- **$Y$:** Rendimiento o intensidad productiva por unidad de superficie.\n"
                    "- **$m - c$:** Margen neto unitario (precio de mercado $m$ menos costo de producción $c$).\n"
                    "- **$-Y \\cdot t \\cdot d$ (Gradiente de distancia):** Pendiente negativa que explica por qué las actividades más intensivas se concentran en el núcleo y forman anillos concéntricos."
                ),
            )

            dist_max = st.slider("Distancia máxima desde el centro urbano (km):", 10, 100, 50)
            d_vec = np.linspace(0, dist_max, 100)

            # 3 Actividades con distinto gradiente de concentración espacial
            lr_intensiva = np.maximum(0, 120 - 4.5 * d_vec)   # Lechería intensiva / Hortalizas / Comercio
            lr_intermedia = np.maximum(0, 85 - 2.0 * d_vec)   # Cultivos / Industria agroalimentaria
            lr_extensiva = np.maximum(0, 50 - 0.8 * d_vec)    # Ganadería extensiva / Forestal

            fig_thunen = go.Figure()
            fig_thunen.add_trace(go.Scatter(x=d_vec, y=lr_intensiva, mode="lines", name="1. Actividad Intensiva / Hortalizas-Lechería (Alto Gradiente)", line=dict(width=3, color="#dc2626")))
            fig_thunen.add_trace(go.Scatter(x=d_vec, y=lr_intermedia, mode="lines", name="2. Agroindustria / Cultivos (Gradiente Medio)", line=dict(width=3, color="#2563eb")))
            fig_thunen.add_trace(go.Scatter(x=d_vec, y=lr_extensiva, mode="lines", name="3. Forestal / Extensiva (Bajo Gradiente)", line=dict(width=3, color="#059669")))
            fig_thunen.update_layout(
                title="Curvas de Gradiente de Renta y Anillos Concéntricos de von Thünen",
                xaxis_title="Distancia al Centro Urbano / Mercado Principal (d en km)",
                yaxis_title="Renta Locacional LR(d)",
                height=360,
                margin=dict(l=10, r=10, t=40, b=20),
                legend=dict(orientation="h", y=-0.25),
            )
            st.plotly_chart(fig_thunen, use_container_width=True)

    # ==========================================================================
    # PESTAÑA 3: LAS 3 VISIONES DE ARTICULACIÓN PRODUCTIVA (04 SPL.PDF PÁGS. 5-7)
    # ==========================================================================
    with tabs[2]:
        st.subheader("Las 3 Estrategias de Articulación Productiva (`04 SPL.pdf`, págs. 5 a 7)")
        st.markdown(
            "En la cátedra se distinguen **3 niveles concéntricos de articulación territorial** "
            "(Diagrama de círculos concéntricos de la página 6 de `04 SPL.pdf`):"
        )

        c_v1, c_v2, c_v3 = st.columns(3)
        with c_v1:
            st.markdown(
                """
                <div class="cifra-card">
                <h4>1. Red Empresarial (Núcleo)</h4>
                <p><b>Definición:</b> Conjunto de empresas independientes de un mismo sector y localidad que deciden colaborar voluntariamente sin perder su independencia para alcanzar objetivos comunes que no lograrían aisladas.</p>
                <p><b>¿Qué se hace en América Latina?:</b></p>
                <ul>
                    <li>Compra conjunta de insumos para reducir costos.</li>
                    <li>Contratación compartida de consultorías.</li>
                    <li>Venta conjunta de productos similares (economías de escala).</li>
                    <li>Instalación de maquinarias compartidas.</li>
                </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_v2:
            st.markdown(
                """
                <div class="cifra-card" style="border-left-color: #d97706;">
                <h4>2. Clúster Productivo (Anillo Intermedio)</h4>
                <p><b>Definición:</b> "Masa crítica de empresas", generalmente pequeñas y medianas, especializadas en un mismo sector o en actividades productivas relacionadas, localizadas en un área geográfica determinada y reducida.</p>
                <p><b>¿Qué se hace en América Latina?:</b></p>
                <ul>
                    <li>Generación de servicios tecnológicos especializados.</li>
                    <li>Creación de laboratorios de prueba o medición.</li>
                    <li>Creación de centros de formación e investigación aplicada.</li>
                    <li>Establecimiento de normas de producto y promoción de "producto típico".</li>
                </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c_v3:
            st.markdown(
                """
                <div class="cifra-card" style="border-left-color: #059669;">
                <h4>3. Sistema Productivo Local — SPL (Anillo Exterior)</h4>
                <p><b>Definición:</b> Conjunto de los actores productivos e instituciones que pertenecen a una localidad histórica y geográfica determinada y que participan en los procesos de desarrollo económico de la misma.</p>
                <p><b>¿Qué se hace en América Latina?:</b></p>
                <ul>
                    <li>Acciones para apoyar a la comunidad sin distinguir "sector".</li>
                    <li>Acciones con impacto público mayor.</li>
                    <li>Planificación del uso del territorio (OT / PLADECO / PROT).</li>
                    <li>Desarrollo de escuelas y mejoramiento de infraestructura.</li>
                </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
