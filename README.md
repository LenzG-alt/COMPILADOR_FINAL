# Compilador Simple para Lenguaje Imperativo

## Descripción

Este proyecto implementa un compilador simple para un lenguaje imperativo de alto nivel. El compilador toma como entrada código fuente escrito en este lenguaje y genera código ensamblador SPIM MIPS como salida. El proceso de compilación incluye análisis léxico, análisis sintáctico (con construcción de Árbol de Sintaxis Abstracta - AST), análisis semántico (incluyendo la gestión de una tabla de símbolos y verificación de tipos) y generación de código intermedio/final.

## Componentes del Compilador

El compilador está estructurado en varios módulos Python, cada uno responsable de una fase específica del proceso de compilación:

-   **`AnalizadorLexico.py`**:
    -   Responsable del análisis léxico.
    -   Utiliza la biblioteca PLY (Python Lex-Yacc) para tokenizar el código fuente de entrada en componentes léxicos (tokens) como identificadores, palabras clave, números, operadores, etc.
    -   Define las expresiones regulares para cada token y maneja errores léxicos básicos.

-   **`ArbolSintactico.py`**:
    -   Contiene la lógica para el análisis sintáctico predictivo LL(1) y la construcción del Árbol de Sintaxis Abstracta (AST).
    -   Define la clase `Node` para representar los nodos del AST.
    -   Incluye funciones para cargar la tabla de análisis sintáctico desde un archivo CSV.
    -   Implementa el algoritmo de análisis sintáctico que consume tokens del analizador léxico y construye el AST si la sintaxis es correcta.
    -   Proporciona funcionalidad para visualizar el AST generado utilizando Graphviz, guardándolo como archivos `.dot` y `.png`.

-   **`AnalizadorSintactico.py`** (Análisis Semántico):
    -   Aunque el nombre puede ser confuso (debería llamarse `AnalizadorSemantico.py`), este módulo realiza el análisis semántico.
    -   Recorre el AST generado por `ArbolSintactico.py`.
    -   Construye y gestiona una `TablaSimbolos` para rastrear declaraciones de variables, funciones, sus tipos y ámbitos.
    -   Realiza verificaciones de tipo (e.g., compatibilidad en asignaciones, operaciones, tipos de retorno de funciones).
    -   Reporta errores semánticos detectados.

-   **`GeneradorSPIM.py`**:
    -   Encargado de la generación de código ensamblador SPIM MIPS.
    -   Toma el AST (validado semánticamente) y la tabla de símbolos como entrada.
    -   Traduce las estructuras del AST (declaraciones, expresiones, estructuras de control, llamadas a funciones) a instrucciones SPIM.
    -   Maneja la asignación de registros temporales y el diseño del layout de memoria para variables globales y locales (stack frame).

-   **`TablaSimbolos.py`**:
    -   Define la clase `SymbolTable` utilizada por el `AnalizadorSintactico.py` (semántico).
    -   Implementa una estructura de datos para almacenar información sobre identificadores (variables, funciones), incluyendo su tipo, ámbito (global, local a una función, parámetros) y línea de declaración.
    -   Proporciona métodos para agregar símbolos, buscar símbolos (considerando el ámbito) y gestionar la entrada/salida de ámbitos.
    -   También almacena los errores semánticos detectados.

-   **`main.py`**:
    -   El punto de entrada principal del compilador.
    -   Orquesta las diferentes fases del proceso de compilación:
        1.  Lee el código fuente desde `codigo.txt`.
        2.  Invoca al analizador léxico (`AnalizadorLexico.py` a través de `ArbolSintactico.ejecutar_lexer`).
        3.  Carga la tabla de análisis sintáctico (`tabla_sintactica.csv`).
        4.  Invoca al analizador sintáctico y constructor del AST (`ArbolSintactico.analizar_cadena`).
        5.  Guarda un registro del análisis sintáctico paso a paso.
        6.  Si el análisis sintáctico es exitoso, visualiza el AST.
        7.  Invoca al analizador semántico (`AnalizadorSintactico.SemanticAnalyzer`).
        8.  Muestra la tabla de símbolos y los errores semánticos.
        9.  Si no hay errores semánticos, invoca al generador de código SPIM (`GeneradorSPIM.py`).
        10. Guarda el código SPIM generado en `salida/codigo_ensamblado.asm`.

## Archivos y Directorios Adicionales

-   **`gramatica.txt`**:
    -   Contiene la definición formal de la gramática del lenguaje fuente que el compilador procesa. Esta gramática es la base para la construcción de la tabla de análisis sintáctico.

-   **`codigo.txt`**:
    -   Archivo de entrada que contiene el código fuente escrito en el lenguaje definido por `gramatica.txt`. Este es el código que el compilador procesará.

-   **`tabla_sintactica.csv`**:
    -   Representa la tabla de parseo LL(1) generada a partir de la `gramatica.txt`.
    -   Es utilizada por el `ArbolSintactico.py` para dirigir el análisis sintáctico. Cada fila corresponde a un no-terminal, cada columna a un terminal, y las celdas contienen la producción a aplicar o un error.

-   **`salida/`**:
    -   Directorio donde se almacenan los archivos generados durante la compilación.
    -   **`analisis_sintactico_paso_a_paso.txt`**: Un registro detallado de cada paso del análisis sintáctico, mostrando la pila, la entrada restante y la acción tomada. Útil para depuración.
    -   **`codigo_ensamblado.asm`**: El código ensamblador SPIM MIPS final generado por el compilador, listo para ser ejecutado en un simulador SPIM (como QtSpim o MARS).

-   **`arbol_sintactico/`**:
    -   Directorio donde se guardan las representaciones del Árbol de Sintaxis Abstracta.
    -   **`arbol_from_main_py.dot`**: La representación del AST en formato DOT de Graphviz.
    -   **`arbol_from_main_py.png`**: La imagen renderizada del AST (generalmente en formato PNG) a partir del archivo `.dot`.

## Características Principales

-   **Tipos de Datos Soportados**: `int`, `float`, `bool`, `string`, `void` (para funciones).
-   **Estructuras de Control**:
    -   Condicionales: `if-else`.
    -   Bucles: `while`, `for`.
-   **Funciones**:
    -   Definición de funciones con tipos de retorno y parámetros.
    -   Llamadas a funciones.
    -   Manejo básico de ámbitos (global y local a funciones).
    -   Soporte para la función `main` como punto de entrada.
-   **Declaraciones**: Variables globales y locales con inicialización opcional.
-   **Expresiones**: Aritméticas (`+`, `-`, `*`, `/`, `%`), relacionales (`==`, `!=`, `<`, `>`, `<=`, `>=`) y lógicas (`&&`, `||`).
-   **Entrada/Salida**: Función `print` para mostrar valores en la consola.
-   **Manejo de Errores**:
    -   Detección de errores léxicos.
    -   Detección de errores sintácticos.
    -   Detección de errores semánticos (e.g., variables no declaradas, tipos incompatibles, número incorrecto de argumentos en llamadas a funciones).
-   **Generación de Código**: Produce código ensamblador SPIM MIPS.

## Cómo Ejecutar

1.  Asegúrate de tener Python 3.x instalado.
2.  Instala las dependencias necesarias (ver sección de Requisitos).
3.  Escribe el código fuente que deseas compilar en el archivo `PROYECTO/codigo.txt`.
4.  Ejecuta el compilador desde el directorio raíz del proyecto (el que contiene el directorio `PROYECTO`):
    ```bash
    python PROYECTO/main.py
    ```
5.  Los resultados de la compilación, incluyendo el código ensamblado (`salida/codigo_ensamblado.asm`) y otros artefactos, se encontrarán en los directorios `PROYECTO/salida/` y `PROYECTO/arbol_sintactico/`.

## Requisitos

-   **Python 3.x**
-   **PLY (Python Lex-Yacc)**: Para el análisis léxico y sintáctico (aunque la parte de Yacc no se usa directamente si la tabla de parseo es precalculada).
    ```bash
    pip install ply
    ```
-   **Graphviz**: Para la visualización del AST. Debes tener Graphviz instalado en tu sistema y la biblioteca Python `graphviz`.
    ```bash
    pip install graphviz
    ```
    (La instalación de Graphviz a nivel de sistema operativo varía: `sudo apt-get install graphviz` en Debian/Ubuntu, `brew install graphviz` en macOS, o descarga desde el sitio oficial para Windows).

## Posibles Mejoras Futuras

-   Optimización del código SPIM generado.
-   Soporte para arrays y/o estructuras de datos más complejas.
-   Mejoras en el manejo de errores y recuperación.
-   Implementación de un sistema de tipos más avanzado (e.g., inferencia de tipos, polimorfismo).
-   Generación de código para otras arquitecturas.
-   Soporte para características orientadas a objetos.
-   Interfaz gráfica de usuario (GUI) o interfaz de línea de comandos (CLI) más robusta.
-   Incorporación de fases de optimización de código intermedio.
-   Mejora de la estructura del analizador semántico (actualmente en `AnalizadorSintactico.py`).
```
