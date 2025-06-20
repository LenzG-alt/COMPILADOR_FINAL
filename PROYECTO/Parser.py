
import Lexer  # Ahora importamos nuestro lexer personalizado
import os
import csv
from graphviz import Digraph

# === Clase para nodos del AST ===
class Node:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children if children else []

    def to_dot(self, dot):
        node_id = str(id(self))
        dot.node(node_id, self.value)
        for child in self.children:
            child_id = child.to_dot(dot)
            dot.edge(node_id, child_id)
        return node_id


# === Cargar tabla sintáctica desde CSV ===
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


# === Ejecutar Lexer e imprimir tokens (debug opcional) ===
def ejecutar_lexer(contenido):
    Lexer.lexer.input(contenido)  # Accedemos al lexer construido en lexer.py
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
    return tokens


# === Analizador Bottom-Up (LL(1)) con construcción de AST ===
def analizar_cadena(tabla, tokens, terminales, contenido):
    stack = [('$', None)]
    root = list(tabla.keys())[0]
    stack.append((root, None))

    entrada = [{'token': t['type'], 'value': t['value'], 'pos': t['lexpos'], 'lineno': t['lineno']} for t in tokens]
    # Añadir el token de fin de cadena ($)
    entrada.append({
        'token': '$',
        'value': '$',
        'pos': len(contenido),
        'lineno': tokens[-1]['lineno'] if tokens else 1
    })
    
    paso = 0
    historial = []
    aceptado = True
    error_info = {}
    nodo_raiz = None
    pila_nodos = []

    while len(stack) > 0:
        paso += 1
        simbolo_pila, nodo_pila = stack[-1]
        token_entrada = entrada[0]['token']
        valor_entrada = entrada[0]['value']

        accion = ""
        if simbolo_pila == token_entrada:
            accion = f"Coincidir '{simbolo_pila}'"
            if nodo_pila:
                pila_nodos.append(nodo_pila)
            stack.pop()
            entrada.pop(0)
        elif simbolo_pila in tabla and token_entrada in tabla[simbolo_pila]:
            regla = tabla[simbolo_pila][token_entrada]
            if regla == '':
                aceptado = False
                error_info = {
                    "token": valor_entrada,
                    "linea": entrada[0]['lineno'],
                    "columna": entrada[0]['pos'] + 1
                }
                break
            if regla == 'ε':
                accion = f"{simbolo_pila} → ε"
                new_node = Node(simbolo_pila, [Node('ε')])
                stack.pop()
                if pila_nodos:
                    pila_nodos[-1].children.append(new_node)
                else:
                    pila_nodos.append(new_node)
            else:
                accion = f"{simbolo_pila} → {regla}"
                partes = regla.split()
                stack.pop()
                new_children = []
                for parte in reversed(partes):
                    stack.append((parte, Node(parte)))
                    new_children.insert(0, stack[-1][1])
                new_node = Node(simbolo_pila, new_children)
                if pila_nodos:
                    pila_nodos[-1].children.append(new_node)
                else:
                    pila_nodos.append(new_node)
        else:
            aceptado = False
            error_info = {
                "token": valor_entrada,
                "linea": entrada[0]['lineno'],
                "columna": entrada[0]['pos'] + 1
            }
            break

        historial.append({
            "paso": paso,
            "pila": ' '.join([s[0] for s in stack]),
            "entrada": ' '.join([t['token'] for t in entrada]),
            "accion": accion
        })

        if len(stack) == 1 and stack[0][0] == '$' and token_entrada == '$':
            break

    if aceptado and pila_nodos:
        nodo_raiz = pila_nodos[-1]

    return historial, aceptado, error_info, nodo_raiz


# === Generar archivo DOT y renderizado del AST ===
def guardar_ast(ast, nombre_salida="arbol_sintactico/arbol"):
    os.makedirs("arbol_sintactico", exist_ok=True)
    dot = Digraph(comment='Árbol Sintáctico Abstracto')
    if ast:
        ast.to_dot(dot)
        dot.render(nombre_salida, format='png', cleanup=True)
        dot.save(filename=nombre_salida + ".dot")
        print(f"✅ Árbol guardado en arbol_sintactico/{os.path.basename(nombre_salida)}")


# === Main ===
def main():
    # Leer contenido del archivo de entrada
    with open("codigo.txt", "r") as f:
        contenido = f.read()

    # Ejecutar lexer y obtener tokens
    tokens = ejecutar_lexer(contenido)

    # Cargar gramática
    tabla, terminales = cargar_tabla_sintactica("tabla.csv")

    # Analizar cadena
    historial, aceptado, error_info, ast = analizar_cadena(tabla, tokens, terminales, contenido)
    # Mostrar resultados
    if aceptado:
        print("✅ La cadena es sintácticamente correcta.")
        guardar_ast(ast)
    else:
        print("❌ Error sintáctico detectado.")
        print(f"  - Token problemático: '{error_info.get('token', '?')}'")
        print(f"  - Posición: línea {error_info.get('linea', '?')}, columna {error_info.get('columna', '?')}")

if __name__ == "__main__":
    main()