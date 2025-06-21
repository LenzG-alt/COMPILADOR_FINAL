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
    _, aceptado, error_info, ast_root = Parser.analizar_cadena(tabla, tokens, terminales, contenido)

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

    print("\n--- Compilador Finalizado ---")

if __name__ == "__main__":
    run_compiler_pipeline()
