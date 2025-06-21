import os
import ply.lex as lex
from Lexer import lexer, tokens

def main():
    # Nombre del archivo de entrada
    input_file = 'codigo.txt'
    
    # Leer el archivo de entrada
    try:
        with open(input_file, 'r', encoding='utf-8') as file:
            code = file.read()
    except FileNotFoundError:
        print(f"El archivo {input_file} no fue encontrado.")
        return
    
    # Crear la carpeta de salida si no existe
    output_dir = 'salida'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Archivo de salida para los resultados
    output_file = os.path.join(output_dir, 'resultados.txt')
    
    # Archivo de errores léxicos
    error_file = os.path.join(output_dir, 'errores_lexicos.txt')
    
    # Limpiar el archivo de errores léxicos si ya existe
    if os.path.exists(error_file):
        os.remove(error_file)
    
    # Analizar el código fuente
    lexer.input(code)
    
    # Variables para el resumen
    token_count = 0
    error_count = 0
    
    # Procesar tokens y errores
    with open(output_file, 'w', encoding='utf-8') as outfile:
        while True:
            tok = lexer.token()
            if not tok:
                break  # No hay más tokens
            token_count += 1
            outfile.write(f"Token: {tok.type}, Valor: '{tok.value}', Línea: {tok.lineno}, Posición: {tok.lexpos}\n")
    
    # Leer y contar errores léxicos
    if os.path.exists(error_file):
        with open(error_file, 'r', encoding='utf-8') as errfile:
            errors = errfile.readlines()
            error_count = len(errors)
    
    # Escribir el resumen en el archivo de resultados
    with open(output_file, 'a', encoding='utf-8') as outfile:
        outfile.write("\nResumen:\n")
        outfile.write(f"Tokens encontrados: {token_count}\n")
        outfile.write(f"Errores léxicos detectados: {error_count}\n")
    
    print(f"Análisis completado. Resultados guardados en {output_file}")
    if error_count > 0:
        print(f"Errores léxicos detectados. Detalles en {error_file}")

if __name__ == "__main__":
    main()