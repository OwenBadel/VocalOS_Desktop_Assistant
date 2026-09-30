# 🤖 Directiva Agéntica: VocalOS Desktop Assistant

---
project_id: "PROJ-014"
project_name: "VocalOS Desktop Assistant"
absolute_disk_path: "d:/Proyectos/LemonFabrica/Fabrica_Software/projects/PROJ_014_VocalOS_Desktop_Assistant"
okf_project_node: "[[Proyectos/PROJ_014_VocalOS_Desktop_Assistant|VocalOS Desktop Assistant]]"
architecture_node: "[[Decisiones de Arquitectura/ARQ_006_Voice_Biometrics_Autonomous_OS_Agent|ARQ-006 Biometría Vocal y Agente Autónomo de SO]]"
mcp_server_entrypoint: "d:/Proyectos/LemonFabrica/Fabrica_Software/mcp/server.py"
status: "active"
created_at: "2026-09-30T16:55:00-05:00"
---

## 🎯 1. Identidad y Autoría
Este proyecto es diseñado y desarrollado bajo la titularidad y dirección de **Owen Badel Hooker** (Ingeniero de Sistemas).
Directorio local en disco duro:
`d:/Proyectos/LemonFabrica/Fabrica_Software/projects/PROJ_014_VocalOS_Desktop_Assistant`

### Roles Operativos en este Proyecto:
1. **Orquestador (ROL-001):** Supervisa el plan de entrega, dependencias y cumplimiento OKF.
2. **Desarrollador (ROL-004):** Construye la solución modular, tipada y sin código espagueti.
3. **Evaluador / QA (ROL-005):** Audita calidad, estándares y bloquea código roto antes del commit.
4. **Documentador (ROL-006):** Mantiene la bitácora (`README.md`), docstrings y notas OKF en español.
5. **Tester (ROL-007):** Diseña y ejecuta suites de pruebas automatizadas en `tests/`.

---

## 🧭 2. Enrutamiento Determinista al Cerebro OKF (Cero Reinvención)
Antes de proponer o codificar, el agente debe navegar deterministamente hacia el árbol del cerebro:

| Si necesitas... | Acude al Árbol de Conocimiento | Acción Obligatoria |
| :--- | :--- | :--- |
| **Modelos de Diseño y Arquitectura** | `vault/Decisiones de Arquitectura/` | Aplicar patrones canónicos ([[Decisiones de Arquitectura/ARQ_006_Voice_Biometrics_Autonomous_OS_Agent\|ARQ-006]]). |
| **Habilidades y Snippets Probados** | `vault/Técnicas/` | Reutilizar el 80% ya resuelto sin hacer bypass. |
| **Librerías y Dependencias Python** | `vault/Python/` | Validar que exista en el vault antes de instalar. |
| **Librerías y Ecosistema JavaScript/TS** | `vault/Librerías JS/` | Usar versiones curadas de la fábrica. |
| **Resolución de Errores y Bugs** | `vault/Errores y Soluciones/` | Consultar post-mortems previos o registrar uno nuevo. |

---

## 🏛️ 3. Marco Arquitectónico y Estándares
Este proyecto implementa:
* **Arquitectura Canónica:** [[Decisiones de Arquitectura/ARQ_006_Voice_Biometrics_Autonomous_OS_Agent|ARQ-006 Biometría Vocal y Agente Autónomo de SO]]
* **Estándar de Memoria:** [[Plantillas/ESPECIFICACION_OKF|Estándar OKF v1.0.0]]
* **MOC Central de la Fábrica:** [[Indice_Fabrica|MOC Central]]

---

## 📦 4. Librerías y Dependencias Autorizadas
El agente debe ceñirse estrictamente a las librerías asimiladas formalmente:
* `fastapi`, `uvicorn`, `websockets` (Backend REST & WebSocket en tiempo real).
* `numpy`, `scipy` (Procesamiento digital de señales acústicas y cálculo de embeddings vocales).
* `subprocess`, `pathlib`, `os`, `shutil` (Automatización autónoma del sistema operativo Windows).
* `webbrowser` (Integración con el navegador predeterminado para búsquedas).
* Frontend con interfaz web interactiva basada en Google Stitch / Glassmorphism Cyberpunk.

---

## 🛠️ 5. Habilidades Requeridas (Skills)
* `auto_commit_funcional` (Gestión autónoma de commits y repositorio individual en GitHub).

---

## 🚦 6. Protocolo de Ejecución: "¿Qué Quiero Hacer?" vs. "¿Qué Pasa Cuando Falla?"

### A. ¿Qué Quiero Hacer? (Planificación y Bitácora)
1. Desglosar los requerimientos en la bitácora (`README.md`).
2. Mapear cada requerimiento contra las habilidades ya existentes en el cerebro.
3. Ejecutar las tareas paso a paso siguiendo las directivas de las skills sin bypass.

### B. ¿Qué Pasa Cuando Falla? (Contención y Resiliencia)
1. **Bloqueo Inmediato:** Prohibido realizar commits si hay errores de sintaxis o tests en rojo.
2. **Aislamiento:** Extraer el caso mínimo reproducible y revertir cambios desestabilizadores si es necesario.
3. **Diagnóstico y Post-Mortem:** Registrar la causa y solución en `vault/Errores y Soluciones/ERR_XXX.md`.
4. **Verificación TDD:** Confirmar la solución con una prueba unitaria antes de desbloquear el commit.

---

## 🔌 7. Conexión con el Servidor MCP de Conocimiento (OKF)
* **Ruta del Servidor:** `d:/Proyectos/LemonFabrica/Fabrica_Software/mcp/server.py`
* **Herramientas Disponibles:** `search_graph`, `read_node`, `build_context_subgraph`, `reload_graph`.

---

## 🚀 8. Repositorio Git Individual y Commits Autónomos a GitHub
* **Aislamiento Total:** Este proyecto posee su propio repositorio Git con remoto `https://github.com/OwenBadel/VocalOS_Desktop_Assistant.git`.
* **Creación Desatendida con `gh` CLI:** Si el repositorio remoto no existe, el agente utiliza automáticamente `gh repo create VocalOS_Desktop_Assistant --public --source=. --push`.
* **Commits en Español:** Cada funcionalidad operativa verificada debe comitearse con mensajes Conventional Commits en español (`feat:`, `fix:`, `docs:`, `test:`).
