# PROYECTO/main.py

import os # For potential path joining, though direct paths are used for now

# Assuming Lexer.py, Parser.py, SemanticAnalyzer.py, SymbolTable.py are in the same directory (PROYECTO)
import Lexer
import Parser
from SemanticAnalyzer import SemanticAnalyzer
# Node class is part of Parser module and used implicitly by ast_root
# SymbolTable is used by SemanticAnalyzer

def run_compiler_pipeline():
    # Define file paths relative to the PROYECTO directory
    # Assumes main.py is in PROYECTO and executed from parent of PROYECTO, or PROYECTO is in PYTHONPATH
    # For simplicity, if running `python PROYECTO/main.py`, relative paths from PROYECTO are fine.

    base_dir = os.path.dirname(__file__) # Gets the directory where main.py is located (PROYECTO)

    codigo_file_path = os.path.join(base_dir, "codigo.txt")
    tabla_sintactica_path = os.path.join(base_dir, "tabla_sintactica.csv")
    ast_output_path_prefix = os.path.join(base_dir, "arbol_sintactico", "arbol_from_main_py")

    print("--- Iniciando Compilador ---")

    # 1. Leer contenido del archivo de entrada
    print(f"Leyendo código desde: {codigo_file_path}")
    try:
        with open(codigo_file_path, "r", encoding="utf-8") as f:
            contenido = f.read()
        print("--- Código Fuente ---")
        print(contenido)
        print("--------------------")
    except FileNotFoundError:
        print(f"Error: El archivo de código '{codigo_file_path}' no fue encontrado.")
        return

    # 2. Análisis Léxico
    print("\n--- Fase Léxica ---")

    Lexer.lexer.input(contenido)
    tokens = []
    while True:
        tok = Lexer.lexer.token()
        if not tok:
            break
        tokens.append({
            'type': tok.type,
            'value': tok.value,
            'lineno': tok.lineno,
            'lexpos': tok.lexpos
        })

    if not tokens:
        print("Error: No se generaron tokens o el lexer falló.")
        # Lexer errors are printed directly by t_error in Lexer.py
        return
    print(f"Tokens generados: {len(tokens)}")
    # print("Tokens:", tokens) # Optional: very verbose
    print("Análisis léxico completado.")

    # 3. Análisis Sintáctico
    print("\n--- Fase Sintáctica ---")
    try:
        tabla, terminales = Parser.cargar_tabla_sintactica(tabla_sintactica_path)
    except FileNotFoundError:
        print(f"Error: El archivo de tabla sintáctica '{tabla_sintactica_path}' no fue encontrado.")
        return

    # `analizar_cadena` returns: historial, aceptado, error_info, ast_root
    historial_sintactico, aceptado, error_info, ast_root = Parser.analizar_cadena(tabla, tokens, terminales, contenido)

    # Guardar el análisis sintáctico paso a paso en un archivo
    output_dir = os.path.join(base_dir, "salida")
    os.makedirs(output_dir, exist_ok=True)
    analisis_sintactico_filepath = os.path.join(output_dir, "analisis_sintactico_paso_a_paso.txt")

    try:
        with open(analisis_sintactico_filepath, "w", encoding="utf-8") as f_analisis:
            f_analisis.write("| Paso | Pila | Entrada | Acción |\n")
            f_analisis.write("|------|------|---------|--------|\n")
            if historial_sintactico:
                for paso_info in historial_sintactico:
                    # Escapar pipes dentro de los valores para no romper el formato Markdown de la tabla
                    pila_escaped = paso_info['pila'].replace('|', '\\|')
                    entrada_escaped = paso_info['entrada'].replace('|', '\\|')
                    accion_escaped = paso_info['accion'].replace('|', '\\|')
                    f_analisis.write(f"| {paso_info['paso']} | {pila_escaped} | {entrada_escaped} | {accion_escaped} |\n")
            else:
                f_analisis.write("|      |      |         |                |\n") # Fila vacía si no hay historial
        print(f"Análisis sintáctico paso a paso guardado en: {analisis_sintactico_filepath}")
    except IOError as e:
        print(f"Error al escribir el archivo de análisis sintáctico: {e}")

    if not aceptado:
        print("Error en el análisis sintáctico.")
        print(f"  - Token problemático: '{error_info.get('token', '?')}'")
        print(f"  - Posición: línea {error_info.get('linea', '?')}, columna {error_info.get('columna', '?')}")
        return

    print("Análisis sintáctico completado con éxito.")
    if ast_root:
        print("Árbol Sintáctico (AST) generado.")
        try:
            Parser.guardar_ast(ast_root, terminales, ast_output_path_prefix)
            print(f"AST guardado en imágenes en: {ast_output_path_prefix}.(dot/png)")
        except Exception as e:
            print(f"Advertencia: No se pudo guardar la imagen del AST: {e}")
    else:
        print("Advertencia: El análisis sintáctico fue aceptado pero no se generó un AST.")
        # This case might indicate an issue in parser logic if 'aceptado' is true but ast_root is None

    # 4. Análisis Semántico
    print("\n--- Fase Semántica ---")
    if not ast_root:
        print("Error: No se puede realizar el análisis semántico sin un AST.")
        return

    analyzer = SemanticAnalyzer(ast_root)
    analyzer.analyze() # Perform semantic analysis

    symbol_table_output = analyzer.get_symbol_table_formatted()
    semantic_errors_output = analyzer.get_errors_formatted()

    print("Análisis semántico completado.")

    # 5. Mostrar Resultados
    print("\n--- Resultados del Análisis Semántico ---")

    print("\n" + symbol_table_output)
    print("\n" + semantic_errors_output)

    # 5. Generación de Código SPIM (si no hay errores semánticos graves)
    # Check if there are errors. analyzer.symbol_table.errors is a list.
    # We might allow proceeding if only warnings, but for now, stop on any error.
    if not analyzer.symbol_table.errors: # or check a specific error severity
        print("\n--- Fase de Generación de Código SPIM ---")
        try:
            # Ensure CodeGeneratorSPIM is imported
            from CodeGeneratorSPIM import CodeGeneratorSPIM

            code_generator = CodeGeneratorSPIM(ast_root, analyzer.symbol_table)
            spim_code = code_generator.generate_code()

            output_asm_path = os.path.join(output_dir, "output.asm")
            with open(output_asm_path, "w", encoding="utf-8") as f_asm:
                f_asm.write(spim_code)
            print(f"✅ Código SPIM generado en: {output_asm_path}")

            # Optionally print SPIM code to console
            # print("\n--- Código SPIM Generado ---")
            # print(spim_code)
            # print("--------------------------")

        except ImportError:
            print("Error: No se pudo importar CodeGeneratorSPIM. Asegúrate que el archivo existe y está accesible.")
        except Exception as e:
            print(f"Error durante la generación de código SPIM: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nNo se generará código SPIM debido a errores semánticos.")


    print("\n--- Compilador Finalizado ---")

if __name__ == "__main__":
    run_compiler_pipeline()