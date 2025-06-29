import os
import AnalizadorLexico
import ArbolSintactico
from AnalizadorSintactico import SemanticAnalyzer

def run_compiler():
    base_dir = os.path.dirname(__file__) 
    codigo_file = os.path.join(base_dir, "codigo.txt")
    tabla_sintactica_file = os.path.join(base_dir, "tabla_sintactica.csv")
    ast_output_file = os.path.join(base_dir, "arbol_sintactico", "arbol_from_main_py")

    print("--- 1. Iniciando Compilador ---")

    # 1. Leer contenido del archivo de entrada
    print(f"Leyendo código desde: {codigo_file}")
    try:
        with open(codigo_file, "r", encoding="utf-8") as f:
            contenido = f.read()
        print("--- Código Fuente ---")
        print(contenido)
        print("--------------------")
    except FileNotFoundError:
        print(f"Error: El archivo de código '{codigo_file}' no fue encontrado.")
        return

    # 2. Análisis Léxico - REVISAR Lexer.  . 
    print("\n--- 2. Fase Léxica ---")

    tokens = ArbolSintactico.ejecutar_lexer(contenido)

    if not tokens:
        print("Error: No se generaron tokens o el lexer falló.")
        return
    print(f"Tokens generados: {len(tokens)}")
    print("--- Análisis léxico completado. ---")

    # 3. Análisis Sintáctico - REVISAR 
    print("\n--- 3. Fase Sintáctica ---")
    try:
        tabla, terminales = ArbolSintactico.cargar_tabla_sintactica(tabla_sintactica_file)
        
    except FileNotFoundError:
        print(f"Error: El archivo de tabla sintáctica '{tabla_sintactica_file}' no fue encontrado.")
        return
    #AQUI SE USA ANALIZAR CADENA
    historial_sintactico, aceptado, error_info, ast_root = ArbolSintactico.analizar_cadena(tabla, tokens, terminales, contenido)

    # Guardar el análisis sintáctico paso a paso en un archivo
    output_dir = os.path.join(base_dir, "salida")
    os.makedirs(output_dir, exist_ok=True)
    analisis_sintactico = os.path.join(output_dir, "analisis_sintactico_paso_a_paso.txt")

    try:
        with open(analisis_sintactico, "w", encoding="utf-8") as f_analisis:
            f_analisis.write("| Paso | Pila | Entrada | Acción |\n")
            f_analisis.write("|------|------|---------|--------|\n")
            if historial_sintactico: # si existe historial sintactico entonces ...

                for paso_info in historial_sintactico:
                    
                    pila_escaped = paso_info['pila'].replace('|', '\\|')
                    entrada_escaped = paso_info['entrada'].replace('|', '\\|')
                    accion_escaped = paso_info['accion'].replace('|', '\\|')
                    f_analisis.write(f"| {paso_info['paso']} | {pila_escaped} | {entrada_escaped} | {accion_escaped} |\n")
            else:
                f_analisis.write("|      |      |         |                |\n") # Fila vacía si no hay historial

        print(f"Análisis sintáctico paso a paso guardado en: {analisis_sintactico}")

    except IOError as e:
        print(f"Error al escribir el archivo de análisis sintáctico: {e}")

    if not aceptado:
        print("Error en el análisis sintáctico.")
        print(f"  - Token problemático: '{error_info.get('token', '?')}'")
        print(f"  - Posición: línea {error_info.get('linea', '?')}, columna {error_info.get('columna', '?')}")
        print(f"  - Tipo error {error_info.get('error','?')}")
        return
    print("--- Análisis sintáctico completado con éxito.---")

    # 4. Generar Arbol Sintantactico AST
    if ast_root: # si existe una razi entonces
        print("\n--- 4. Árbol Sintáctico (AST) generado. ---")
        try:
            ArbolSintactico.guardar_ast(ast_root, terminales, ast_output_file)
            print(f"AST guardado en imágenes en: {ast_output_file}.(dot/png)")
        except Exception as e:
            print(f"Advertencia: No se pudo guardar la imagen del AST: {e}")
    else:
        print("Advertencia: El análisis sintáctico fue aceptado pero no se generó un AST.")

    # 5. Análisis Semántico
    print("\n--- 5. Fase Semántica ---")
    if not ast_root:
        print("Error: No se puede realizar el análisis semántico sin un AST.")
        return
    
    analyzer = SemanticAnalyzer(ast_root)
    analyzer.analyze() 

    symbol_table_output = analyzer.get_symbol_table_formatted()
    semantic_errors_output = analyzer.get_errors_formatted()

    print("Análisis semántico completado.")

    # 6. Mostrar Resultados
    print("\n--- Resultados del Análisis Semántico ---")

    print("\n" + symbol_table_output)
    print("\n" + semantic_errors_output)

    '''
    # 5. Generación de Código SPIM (si no hay errores semánticos graves)
    if not analyzer.symbol_table.errors: # or check a specific error severity
        print("\n--- Fase de Generación de Código SPIM ---")
        try:
            from CodeGeneratorSPIM import CodeGeneratorSPIM

            code_generator = CodeGeneratorSPIM(ast_root, analyzer.symbol_table)
            spim_code = code_generator.generate_code()

            output_asm_path = os.path.join(output_dir, "output.asm")
            with open(output_asm_path, "w", encoding="utf-8") as f_asm:
                f_asm.write(spim_code)
            print(f"✅ Código SPIM generado en: {output_asm_path}")
        except ImportError:
            print("Error: No se pudo importar CodeGeneratorSPIM. Asegúrate que el archivo existe y está accesible.")
        except Exception as e:
            print(f"Error durante la generación de código SPIM: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nNo se generará código SPIM debido a errores semánticos.")
    '''
    print("\n--- Compilador Finalizado ---")

if __name__ == "__main__":
    run_compiler()