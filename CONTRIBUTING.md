# 🛠️ Guía para Contribuir (O cómo ganarte un pedacito de cielo)

¡Buenas! Si estás leyendo esto es porque quieres arrimar el hombro, y eso ya te hace ser de mis personas favoritas de internet. 

Este es un proyecto de código abierto, lo que significa que es de todos y para todos. Estamos aquí para cacharrear, aprender y hacer que esto mole cada vez más. Así que sí, ¡necesito tu ayuda! Se aceptan desde correcciones de comas hasta reescrituras épicas en la extracción de textos o mejoras en la interfaz.

## 🚀 ¿Cómo puedes echar un cable?

No hace falta ser un *hacker* de película para contribuir. Puedes ayudar de un montón de maneras, que aquí todo suma:

### 🐛 Cazando Bugs (Reportar errores)
¿Has encontrado algo que explota, da fallos con CUDA o hace cosas raras al convertir un PDF complejo? Abre una *Issue*. Pero ojo, ayúdame a ayudarte. Decir "esto no va" es como llevar el coche al taller y decir "hace ruido". 
Cuéntame qué estabas haciendo, qué sistema usas, y si tienes capturas de pantalla, archivos de ejemplo o un *log* de errores de la consola, ponlos. Cuanta más info, menos tendré que usar la bola de cristal.

### 💡 Proponer locuras (Nuevas ideas)
¿Se te ha ocurrido una función increíble (como nuevos formatos de exportación, integración con bases de datos o asistentes BIM) mientras te tomabas un café, corrías o programabas? Abre una *Issue* y cuéntame tu visión. Lo debatimos y vemos si encaja. ¡Las buenas ideas siempre son bienvenidas! Que no te dé corte proponer cosas.

### 🧪 Haciendo de "Crash Tester"
Bájate el proyecto, ejecútalo a lo bestia, carga PDFs gigantes con cientos de páginas, pulsa todos los botones a la vez y mira a ver si aguanta. Probar las cosas, trastear y dar tu opinión sincera sobre qué mejorar vale su peso en oro.

### 💻 Tirando código (Pull Requests)
¿Has arreglado un fallo de importación o añadido una función tú mismo? ¡Ole tú! Mándame una *Pull Request* (PR). Para que el proceso vaya sobre ruedas, sigue este pequeño ritual:

1. **Haz un *Fork*** de este repositorio a tu cuenta.
2. **Crea una rama** que se entienda. `git checkout -b fix-calculo-datos` es genial. `git checkout -b cositas-mias-2` me hace llorar.
3. **Pica el código** y pásalo bien.
4. **Haz *commits* con sentido.** Si pones `git commit -m "asdasdasd"` o `"arreglado"`, un desarrollador en algún lugar del mundo pierde sus alas. Explica de forma breve qué has hecho.
5. **Sube tus cambios** a tu *Fork* y **abre la PR** hacia la rama `main` de este repositorio. ¡Acuérdate de explicar en la PR de qué va el tema!

## 📜 Reglas de la casa

- **Sentido común y buen rollo:** Intenta seguir el estilo de código (Streamlit + PyTorch) que ya hay.
- **No rompas los cimientos:** Si tocas algo gordo en el procesamiento de modelos, asegúrate de que el resto del chiringuito local sigue en pie.
- **Documenta un poquito:** Si añades una función nueva o un filtro de procesamiento, explica cómo se usa. Un código nuevo sin documentación es como un juego de Mega Drive sin caja ni instrucciones: se puede jugar, pero a veces no sabes ni con qué botón se salta.

¡Y ya estaría! Anímate a trastear, proponer y equivocarte, que para eso estamos. ¡Gracias por pasarte por aquí y aportar tu talento!
