# Informe Técnico: Lenguaje de Programación Imperativo Simple "LISC" (Lenguaje Imperativo Simple Compilable)

## 1. Introducción

### Motivación y Propósito

El lenguaje de programación "LISC" (Lenguaje Imperativo Simple Compilable) ha sido diseñado como una herramienta educativa con el objetivo principal de ilustrar los conceptos fundamentales involucrados en la construcción de un compilador. La motivación detrás de su creación es ofrecer un lenguaje lo suficientemente simple como para ser comprendido y compilado en un plazo razonable, pero lo bastante completo como para demostrar las fases clave de la compilación: análisis léxico, sintáctico, semántico y generación de código.

El propósito fundamental de LISC es servir como lenguaje fuente para un compilador que genere código ensamblador SPIM MIPS. Esto permite a los estudiantes y desarrolladores experimentar directamente con la traducción de construcciones de alto nivel a un lenguaje de bajo nivel, entendiendo los desafíos y decisiones de diseño que esto implica.

### Características Principales

LISC es un lenguaje imperativo, de tipado estático, que toma inspiración de lenguajes como C y Pascal en su sintaxis y semántica básica. Sus características principales incluyen:

*   **Tipos de Datos Básicos**: Soporta tipos de datos fundamentales como enteros (`int`), números de punto flotante (`float`), booleanos (`bool`) y cadenas de caracteres (`string`). También incluye el tipo `void` para funciones que no retornan valor.
*   **Declaraciones**: Permite la declaración de variables globales y locales, con la opción de inicialización en el momento de la declaración.
*   **Estructuras de Control**:
    *   Condicionales: `if-else`.
    *   Bucles: `while` y `for`.
*   **Funciones**: Soporta la definición de funciones, incluyendo parámetros, tipos de retorno y una función `main` como punto de entrada obligatorio del programa.
*   **Expresiones**: Permite la construcción de expresiones aritméticas, relacionales y lógicas.
*   **Entrada/Salida**: Proporciona una función `print` para la salida de datos.
*   **Compilación a SPIM MIPS**: El objetivo final del compilador de LISC es producir código ensamblador ejecutable en simuladores SPIM.
*   **Análisis Estático**: Realiza análisis léxico, sintáctico y semántico, incluyendo la verificación de tipos y la gestión de ámbitos mediante una tabla de símbolos.

## 2. Especificación Léxica

Los tokens que conforman el lenguaje LISC se detallan en la siguiente tabla. Cada token se define mediante una expresión regular que describe el patrón de caracteres que lo forma.

| Token              | Expresión Regular                                 | Descripción                                                                 |
| ------------------ | ------------------------------------------------- | --------------------------------------------------------------------------- |
| **Palabras Clave** |                                                   |                                                                             |
| `INT`              | `int`                                             | Palabra reservada para el tipo de dato entero.                              |
| `FLOAT`            | `float`                                           | Palabra reservada para el tipo de dato de punto flotante.                   |
| `BOOL`             | `bool`                                            | Palabra reservada para el tipo de dato booleano.                            |
| `STRING`           | `string`                                          | Palabra reservada para el tipo de dato cadena de caracteres.                |
| `VOID`             | `void`                                            | Palabra reservada para funciones que no retornan valor.                     |
| `IF`               | `if`                                              | Palabra reservada para la estructura de control condicional.                |
| `ELSE`             | `else`                                            | Palabra reservada para la rama alternativa de la estructura `if`.           |
| `WHILE`            | `while`                                           | Palabra reservada para la estructura de control de bucle `while`.             |
| `FOR`              | `for`                                             | Palabra reservada para la estructura de control de bucle `for`.               |
| `MAIN`             | `main`                                            | Palabra reservada para la función principal, punto de entrada del programa. |
| `RETURN`           | `return`                                          | Palabra reservada para retornar un valor desde una función.                 |
| `PRINT`            | `print`                                           | Palabra reservada para la función de salida estándar.                       |
| `TRUE`             | `true`                                            | Palabra reservada para el valor booleano verdadero.                         |
| `FALSE`            | `false`                                           | Palabra reservada para el valor booleano falso.                             |
| **Identificadores**|                                                   |                                                                             |
| `ID`               | `[a-zA-Z_][a-zA-Z0-9_]*`                          | Nombres para variables y funciones.                                         |
| **Literales**      |                                                   |                                                                             |
| `INT_NUM`          | `\d+`                                             | Números enteros.                                                            |
| `FLOAT_NUM`        | `((\d*\.\d+)\|(\d+\.\d*))([eE][-+]?\d+)?\|\d+[eE][-+]?\d+` | Números de punto flotante (incluye notación científica básica).         |
| `STRING_LITERAL`   | `\"([^\\\n]|(\\.))*?\"`                           | Secuencias de caracteres encerradas entre comillas dobles.                  |
| **Operadores**     |                                                   |                                                                             |
| `PLUS`             | `\+`                                              | Operador de suma.                                                           |
| `MINUS`            | `-`                                               | Operador de resta.                                                          |
| `TIMES`            | `\*`                                              | Operador de multiplicación.                                                 |
| `DIVIDE`           | `/`                                               | Operador de división.                                                       |
| `MOD`              | `%`                                               | Operador de módulo.                                                         |
| `EQ`               | `==`                                              | Operador de igualdad.                                                       |
| `NE`               | `!=`                                              | Operador de desigualdad.                                                    |
| `LT`               | `<`                                               | Operador "menor que".                                                       |
| `GT`               | `>`                                               | Operador "mayor que".                                                       |
| `LE`               | `<=`                                              | Operador "menor o igual que".                                               |
| `GE`               | `>=`                                              | Operador "mayor o igual que".                                               |
| `AND`              | `&&`                                              | Operador lógico AND.                                                        |
| `OR`               | `\|\|`                                            | Operador lógico OR.                                                         |
| `EQUALS`           | `=`                                               | Operador de asignación.                                                     |
| **Puntuación**     |                                                   |                                                                             |
| `LPAREN`           | `\(`                                              | Paréntesis izquierdo.                                                       |
| `RPAREN`           | `\)`                                              | Paréntesis derecho.                                                         |
| `LBRACE`           | `\{`                                              | Llave izquierda (inicio de bloque).                                         |
| `RBRACE`           | `\}`                                              | Llave derecha (fin de bloque).                                              |
| `COMMA`            | `,`                                               | Coma (separador de parámetros/argumentos).                                  |
| `SEMI`             | `;`                                               | Punto y coma (fin de sentencia).                                            |
| **Ignorados**      |                                                   |                                                                             |
| `COMMENT`          | `//.* \| /\*([^*]\|\*[^/])*\*/`                   | Comentarios de una línea o multilínea. Se ignoran.                          |
| `WHITESPACE`       | `[ \t\n]+`                                        | Espacios, tabuladores, saltos de línea. Se ignoran.                         |

## 3. Gramática

La gramática formal del lenguaje LISC, que define su estructura sintáctica, se presenta a continuación. Esta gramática está diseñada para ser LL(1) y es la base para el analizador sintáctico predictivo.

```
programa -> funciones

funciones -> funcion funciones
funciones -> ε

funcion -> tipo ID funcion_rest
funcion -> MAIN LPAREN RPAREN LBRACE bloque RBRACE

funcion_rest -> inicializacion SEMI
funcion_rest -> LPAREN parametros RPAREN LBRACE bloque RBRACE

parametros -> parametro parametros_rest
parametros -> ε

parametros_rest -> COMMA parametro parametros_rest
parametros_rest -> ε

parametro -> tipo ID

bloque -> instrucciones
bloque -> ε

instrucciones -> instruccion instrucciones
instrucciones -> ε

instruccion -> declaracion SEMI
instruccion -> For
instruccion -> If
instruccion -> Print
instruccion -> Return
instruccion -> While
instruccion -> ID id_rhs_instruccion

declaracion -> tipo ID inicializacion
inicializacion -> EQUALS exp
inicializacion -> ε

id_rhs_instruccion -> EQUALS exp SEMI
id_rhs_instruccion -> llamada_func SEMI

If -> IF LPAREN exp RPAREN LBRACE bloque RBRACE  Else
Print -> PRINT LPAREN exp_opt RPAREN SEMI
Else -> ELSE LBRACE bloque RBRACE
Else -> ε

While -> WHILE LPAREN exp RPAREN LBRACE bloque RBRACE

For -> FOR LPAREN for_assignment SEMI exp SEMI for_assignment RPAREN LBRACE bloque RBRACE
for_assignment -> ID EQUALS exp

Return -> RETURN exp_opt SEMI
exp_opt -> exp
exp_opt -> ε

exp -> E
E -> C E_rest

E_rest -> OR C E_rest
E_rest -> ε

C -> R C_rest

C_rest -> AND R C_rest
C_rest -> ε

R -> T R_rest

R_rest -> EQ T R_rest
R_rest -> GE T R_rest
R_rest -> GT T R_rest
R_rest -> LE T R_rest
R_rest -> LT T R_rest
R_rest -> NE T R_rest
R_rest -> ε

T -> F T_rest

T_rest -> PLUS F T_rest
T_rest -> MINUS F T_rest
T_rest -> ε

F -> A F_rest

F_rest -> TIMES A F_rest
F_rest -> DIVIDE A F_rest
F_rest -> MOD A F_rest
F_rest -> ε

A -> ID llamada_func
A -> INT_NUM
A -> LPAREN exp RPAREN
A -> FLOAT_NUM
A -> STRING_LITERAL
A -> TRUE
A -> FALSE

lista_args -> exp lista_args_rest
lista_args -> ε

lista_args_rest -> COMMA exp lista_args_rest
lista_args_rest -> ε

llamada_func -> LPAREN lista_args RPAREN
llamada_func -> ε

tipo -> BOOL
tipo -> FLOAT
tipo -> INT
tipo -> STRING
tipo -> VOID
```

## 4. Implementación

La implementación de los analizadores léxico y sintáctico, así como las fases subsiguientes del compilador para LISC, se encuentra disponible en el repositorio que contiene este informe.

**Enlace al Repositorio:** (Referencia al repositorio actual donde se encuentra este archivo).

### Descripción del Contenido del Repositorio:

El proyecto está estructurado en varios módulos Python, cada uno encargado de una parte específica del proceso de compilación:

*   **`PROYECTO/AnalizadorLexico.py`**: Implementa el analizador léxico utilizando la biblioteca PLY. Define los tokens y las reglas para identificarlos en el código fuente.
*   **`PROYECTO/ArbolSintactico.py`**: Contiene la lógica para el análisis sintáctico predictivo LL(1) basado en una tabla de parseo (`tabla_sintactica.csv`). Construye el Árbol de Sintaxis Abstracta (AST) si el código es sintácticamente correcto. También incluye la funcionalidad para visualizar el AST con Graphviz.
*   **`PROYECTO/AnalizadorSintactico.py`**: (Nombre destinado a ser `AnalizadorSemantico.py`) Realiza el análisis semántico. Recorre el AST, gestiona la tabla de símbolos (`TablaSimbolos.py`) para verificar declaraciones, tipos, ámbitos y reportar errores semánticos.
*   **`PROYECTO/TablaSimbolos.py`**: Define la estructura y la lógica para la tabla de símbolos, crucial para el análisis semántico.
*   **`PROYECTO/GeneradorSPIM.py`**: Encargado de la fase de generación de código. Traduce el AST (validado semánticamente) a código ensamblador SPIM MIPS.
*   **`PROYECTO/main.py`**: Es el script principal que orquesta todas las fases del compilador, desde la lectura del código fuente (`codigo.txt`) hasta la generación del código ensamblado (`salida/codigo_ensamblado.asm`).
*   **`PROYECTO/gramatica.txt`**: Archivo de texto con la gramática formal del lenguaje.
*   **`PROYECTO/tabla_sintactica.csv`**: Tabla de parseo LL(1) utilizada por el analizador sintáctico.
*   **`PROYECTO/codigo.txt`**: Archivo de ejemplo con código fuente en LISC.
*   **`PROYECTO/salida/`**: Directorio donde se guardan los artefactos de la compilación, como el código ensamblado.
*   **`PROYECTO/arbol_sintactico/`**: Directorio para las visualizaciones del AST.

## 5. Conclusiones

### Logros del Proyecto

El desarrollo del compilador para LISC ha culminado con éxito en la creación de una herramienta funcional capaz de traducir programas escritos en un lenguaje imperativo simple a código ensamblador SPIM MIPS. Los principales logros incluyen:

*   Un **analizador léxico** robusto capaz de tokenizar correctamente el código fuente.
*   Un **analizador sintáctico predictivo LL(1)** que valida la estructura del código y construye un Árbol de Sintaxis Abstracta (AST) representativo.
*   Un **analizador semántico** que gestiona una tabla de símbolos, verifica tipos, ámbitos y detecta una variedad de errores semánticos comunes.
*   Un **generador de código** que traduce eficazmente las construcciones del AST a instrucciones SPIM, manejando variables, expresiones, estructuras de control y llamadas a funciones.
*   La integración de todas las fases en un flujo de compilación coherente orquestado por `main.py`.

### Posibles Extensiones Futuras

El proyecto actual sienta una base sólida que puede extenderse de diversas maneras:

*   **Optimización de Código**: Implementar fases de optimización en el código SPIM generado para mejorar su eficiencia (e.g., eliminación de código muerto, optimización de bucles).
*   **Nuevas Características del Lenguaje**:
    *   Soporte para **arrays** y posiblemente otros tipos de datos estructurados (e.g., `structs`).
    *   Mejoras en el sistema de **módulos o importaciones**.
    *   Introducción de **manejo de excepciones** básico.
*   **Mejora del Manejo de Errores**: Proporcionar mensajes de error más descriptivos y, potencialmente, mecanismos de recuperación de errores para permitir que el compilador continúe analizando después de encontrar un error.
*   **Generación de Código para Otras Arquitecturas**: Adaptar el generador de código para producir ensamblador para diferentes arquitecturas de procesador.
*   **Interfaz de Usuario**: Desarrollar una interfaz de línea de comandos (CLI) más amigable o incluso una interfaz gráfica (GUI) simple.

### Dificultades Encontradas

Durante el diseño e implementación del compilador LISC, se presentaron varios desafíos:

*   **Diseño de la Gramática LL(1)**: Asegurar que la gramática del lenguaje fuera libre de ambigüedades y adecuada para el análisis predictivo LL(1) requirió iteraciones y ajustes cuidadosos.
*   **Integración de Fases**: Coordinar la salida de una fase como entrada para la siguiente (e.g., los tokens del léxico al sintáctico, el AST del sintáctico al semántico) y asegurar la coherencia de los datos fue un aspecto crucial.
*   **Análisis Semántico**: La implementación de la tabla de símbolos, la gestión de ámbitos anidados y la correcta verificación de tipos (especialmente con promoción de tipos o conversiones implícitas) fue compleja.
*   **Generación de Código SPIM**: Traducir las construcciones de alto nivel (como bucles `for` o llamadas a funciones con paso de parámetros y gestión del stack frame) a instrucciones MIPS detalladas requirió una planificación meticulosa.
*   **Depuración**: La depuración de un compilador puede ser desafiante, ya que los errores en una fase temprana pueden tener efectos cascada en fases posteriores. La visualización del AST y el seguimiento paso a paso del análisis sintáctico fueron herramientas útiles.

### Utilidad del Lenguaje Diseñado

A pesar de su simplicidad, LISC y su compilador asociado ofrecen una considerable utilidad, especialmente en un contexto educativo:

*   **Herramienta de Aprendizaje**: Proporciona una plataforma práctica para que los estudiantes de ciencias de la computación comprendan los principios teóricos y prácticos detrás del diseño y la implementación de compiladores.
*   **Base para Proyectos Más Avanzados**: El código fuente del compilador puede servir como punto de partida para desarrollar compiladores para lenguajes más ricos en características o para explorar diferentes técnicas de compilación.
*   **Comprensión de la Interacción Hardware-Software**: Al generar código ensamblador, se fomenta una mejor comprensión de cómo los lenguajes de alto nivel se traducen a instrucciones que una máquina puede ejecutar.

En resumen, LISC, aunque modesto en su alcance, cumple su propósito como un lenguaje diseñado para la enseñanza y la experimentación en el campo de los compiladores, proporcionando una visión clara del viaje desde el código fuente hasta el código ejecutable.
```
