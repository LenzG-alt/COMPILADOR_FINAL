
import os
import csv
import AnalizadorLexico  # Ahora importamos nuestro lexer personalizado
from graphviz import Digraph

# === Clase para nodos del AST ===
class Node:
    def __init__(self, value, children=None, lineno=-1):
        self.value = value
        self.children = children if children else []
        self.lineno = lineno

    def to_dot(self, dot, terminal_symbols):
        node_id = str(id(self))
        prefix = ""
        if self.value == 'ε':
            prefix = "[T]"
        elif self.value in terminal_symbols:
            prefix = "[T]"
        else:
            prefix = "[N]"

        dot.node(node_id, f"{prefix} {self.value}")
        for child in self.children:
            child_id = child.to_dot(dot, terminal_symbols)
            dot.edge(node_id, child_id)
        return node_id # retorna un puntero al nodo raiz

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
    AnalizadorLexico.lexer.input(contenido)  # Accedemos al lexer construido en lexer.py
    tokens = []
    while True:
        tok = AnalizadorLexico.lexer.token()
        if not tok:
            break
        tokens.append({
            'type': tok.type,
            'value': tok.value,
            'lineno': tok.lineno,
            'lexpos': tok.lexpos
        })
    return tokens

# === Analizador Bottom-Up LL1 con construcción de AST ===
def analizar_cadena(tabla, tokens, terminales, contenido):
    root = list(tabla.keys())[-2]
    nodo_raiz_arbol = Node(root, lineno=1) # Root node lineno set to 1
    stack = [('$', None), (root, nodo_raiz_arbol)]
    
    print(root)

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

    LEXEME_TERMINALS = {"ID", "INT_NUM", "FLOAT_NUM", "STRING_LITERAL", "TRUE", "FALSE"}
    #LEXEME_TERMINALS = AnalizadorLexico.tokens

    while len(stack) > 0:
        paso += 1
        simbolo_pila, nodo_en_pila = stack[-1]
        token_entrada = entrada[0]['token']
        valor_entrada = entrada[0]['value']
        current_lookahead_token_lineno = entrada[0]['lineno']

        if nodo_en_pila and nodo_en_pila.lineno == -1 and simbolo_pila != '$':
            nodo_en_pila.lineno = current_lookahead_token_lineno

        accion = ""
        if simbolo_pila == token_entrada:
            accion = f"Coincidir '{simbolo_pila}'"
            terminal_node_from_stack = nodo_en_pila
            if terminal_node_from_stack: # Ensure node exists
                 terminal_node_from_stack.lineno = current_lookahead_token_lineno
            if simbolo_pila in LEXEME_TERMINALS:
                if terminal_node_from_stack: # Ensure node exists
                    terminal_node_from_stack.value = valor_entrada
            stack.pop()
            entrada.pop(0)

        elif simbolo_pila in tabla and token_entrada in tabla[simbolo_pila]:
            lhs_node = nodo_en_pila # This is the node being expanded
            if lhs_node and lhs_node.lineno == -1 : # Set lineno if not already set by earlier top-of-stack update
                lhs_node.lineno = current_lookahead_token_lineno

            stack.pop()
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
                epsilon_child_node = Node('ε', lineno=current_lookahead_token_lineno)
                if lhs_node: # Ensure node exists
                    lhs_node.children = [epsilon_child_node]
                    # Optionally, update lhs_node.lineno if it was -1, though top-of-stack logic should handle it
                    if lhs_node.lineno == -1:
                        lhs_node.lineno = current_lookahead_token_lineno
            else:
                accion = f"{simbolo_pila} → {regla}"
                partes_rhs = regla.split()
                children_nodes_for_lhs = []
                for parte_symbol in partes_rhs:
                    child_node = Node(parte_symbol)
                    children_nodes_for_lhs.append(child_node)

                if lhs_node: # Ensure node exists
                    lhs_node.children = children_nodes_for_lhs
                    if lhs_node.lineno == -1:
                        lhs_node.lineno = current_lookahead_token_lineno

                for i in range(len(partes_rhs) - 1, -1, -1):
                    stack.append((partes_rhs[i], children_nodes_for_lhs[i]))
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
            if stack[0][0] == simbolo_pila and simbolo_pila == token_entrada : #This case should be handled by the first if in the loop
                 stack.pop() # pop $
                 entrada.pop(0) # pop $ from input
            break

    ast_to_return = None
    if aceptado:
        ast_to_return = nodo_raiz_arbol

    return historial, aceptado, error_info, ast_to_return

# === Generar archivo DOT y renderizado del AST ===
def guardar_ast(ast, terminales, nombre_salida="arbol_sintactico/"):
    os.makedirs("arbol_sintactico", exist_ok=True)
    dot = Digraph(comment='Árbol Sintáctico Abstracto')
    dot = Digraph(comment='https://dreampuf.github.io/GraphvizOnline')
    if ast:
        ast.to_dot(dot, terminales)
        dot.render(nombre_salida, format='png', cleanup=True)
        dot.save(filename=nombre_salida + ".dot")
        print(f"✅ Árbol guardado en arbol_sintactico/{os.path.basename(nombre_salida)}")