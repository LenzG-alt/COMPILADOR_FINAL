import csv
import os

def cargar_tabla_sintactica(ruta_archivo):
    tabla = {}
    with open(ruta_archivo, newline='', encoding='utf-8') as csvfile:
        lector = csv.reader(csvfile, delimiter=';')
        encabezados = next(lector)
        terminales = encabezados[1:]
        for fila in lector:
            if not fila:
                continue
            no_terminal = fila[0]
            tabla[no_terminal] = {}
            for i, accion in enumerate(fila[1:]):
                terminal = terminales[i]
                tabla[no_terminal][terminal] = accion.strip()
    return tabla, terminales


def analizar_cadena(tabla, tokens, terminales):
    stack = ['$']
    stack.append(list(tabla.keys())[0])  # Símbolo inicial

    entrada = tokens + ['$']
    paso = 0
    historial = []
    aceptado = True
    error_info = {}

    while len(stack) > 0:
        paso += 1
        simbolo_pila = stack[-1]
        token_entrada = entrada[0]

        accion = ""
        if simbolo_pila == token_entrada:
            accion = f"Coincidir '{simbolo_pila}'"
            stack.pop()
            entrada.pop(0)
        elif simbolo_pila in tabla and token_entrada in tabla[simbolo_pila]:
            regla = tabla[simbolo_pila][token_entrada]
            if regla == '':  # Celda vacía
                aceptado = False
                error_info = {
                    "token": token_entrada,
                    "linea": 1,
                    "columna": tokens.index(token_entrada) + 1 if token_entrada in tokens else 0
                }
                break
            if regla == 'ε':
                accion = f"{simbolo_pila} → ε"
                stack.pop()
            else:
                accion = f"{simbolo_pila} → {regla}"
                stack.pop()
                partes = regla.split()
                for parte in reversed(partes):
                    if parte != '':  # Evitar espacios vacíos
                        stack.append(parte)
        else:
            aceptado = False
            error_info = {
                "token": token_entrada,
                "linea": 1,
                "columna": tokens.index(token_entrada) + 1 if token_entrada in tokens else 0
            }
            break

        historial.append({
            "paso": paso,
            "pila": ' '.join(stack),
            "entrada": ' '.join(entrada),
            "accion": accion
        })

        if len(stack) == 1 and stack[0] == '$' and token_entrada == '$':
            break

    return historial, aceptado, error_info

def guardar_resultado(historial, aceptado, tokens, nombre_salida="salida/resultados_parser.txt"):
    os.makedirs("salida", exist_ok=True)
    with open(nombre_salida, 'w', encoding='utf-8') as f:
        f.write("=== Análisis Sintáctico Paso a Paso ===\n\n")
        f.write("| {:<4} | {:<20} | {:<20} | {:<20} |\n".format("Paso", "Pila", "Entrada", "Acción"))
        f.write("-" * 75 + "\n")
        for registro in historial:
            f.write("| {:<4} | {:<20} | {:<20} | {:<20} |\n".format(
                registro["paso"],
                registro["pila"],
                registro["entrada"],
                registro["accion"]
            ))
        f.write("\nResumen:\n")
        f.write(f"- Tokens analizados: {len(tokens)}\n")
        f.write(f"- Pasos realizados: {len(historial)}\n")
        if aceptado:
            f.write("- Resultado: ✅ Cadena aceptada.\n")
        else:
            f.write("- Resultado: ❌ Error sintáctico.\n")
            # Extraer token problemático del último paso o usar el primer token restante
            if historial:
                ultimo_registro = historial[-1]
                entrada_restante = ultimo_registro["entrada"].split()
                if len(entrada_restante) > 0:
                    token_error = entrada_restante[0]
                    posicion = tokens.index(token_error) + 1 if token_error in tokens else '?'
                else:
                    token_error = "EOF"
                    posicion = "desconocida"
            else:
                token_error = tokens[0] if tokens else "vacío"
                posicion = 1
            f.write(f"  - Token problemático: '{token_error}'\n")
            f.write(f"  - Posición: línea 1, columna {posicion}\n")

    print("✅ Resultado guardado en:", nombre_salida)

def leer_tokens(ruta_archivo):
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
    return [linea.strip().split() for linea in lineas]


def main():
    ruta_csv = "tabla.csv"
    ruta_tokens = "tokens.txt"

    tabla, terminales = cargar_tabla_sintactica(ruta_csv)
    listas_tokens = leer_tokens(ruta_tokens)

    for idx, tokens in enumerate(listas_tokens):
        print(f"\n🔹 Analizando cadena {idx+1}: {' '.join(tokens)}")
        historial, aceptado, error_info = analizar_cadena(tabla, tokens, terminales)
        guardar_resultado(historial, aceptado, tokens, f"salida/resultados_cadena_{idx+1}.txt")
        if aceptado:
            print("✅ La cadena es sintácticamente correcta.")
        else:
            print("❌ Error sintáctico detectado.")
            print(f"  - Token problemático: '{error_info['token']}'")
            print(f"  - Posición: línea {error_info['linea']}, columna {error_info['columna']}")

if __name__ == "__main__":
    main()