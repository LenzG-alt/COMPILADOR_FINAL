import csv
from collections import defaultdict
from Lexer import tokens  # Importamos los tokens definidos en lexer.py

# Función para leer la gramática desde un archivo
def leer_gramatica(archivo):
    producciones = []
    with open(archivo, 'r') as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            lhs_rhs = linea.split('->')
            if len(lhs_rhs) != 2:
                raise ValueError(f"Línea inválida: {linea}")
            lhs = lhs_rhs[0].strip()
            rhs = [parte.strip() for parte in lhs_rhs[1].split('|')]
            for cuerpo in rhs:
                producciones.append((lhs, cuerpo.split()))
    return producciones

# Calcular First
def calcular_first(producciones, no_terminales):
    first = defaultdict(set)

    cambio = True
    while cambio:
        cambio = False
        for nt, cuerpo in producciones:
            antes = len(first[nt])
            elementos = cuerpo[:]
            while elementos:
                simbolo = elementos.pop(0)
                if simbolo not in no_terminales:
                    first[nt].add(simbolo)
                    break
                else:
                    first[nt] |= first[simbolo]
                    if 'ε' not in first[simbolo]:
                        break
                    if not elementos:  # Si todos pueden ser ε
                        first[nt].add('ε')
            if len(first[nt]) > antes:
                cambio = True
    return first

# Calcular Follow
def calcular_follow(producciones, no_terminales, first):
    follow = defaultdict(set)
    # Añadimos el símbolo de fin de cadena al primer no terminal
    follow[producciones[0][0]].add('$')

    cambio = True
    while cambio:
        cambio = False
        for lhs, cuerpo in producciones:
            for i in range(len(cuerpo)):
                simbolo = cuerpo[i]
                if simbolo in no_terminales:
                    siguientes = cuerpo[i+1:]
                    temp_set = set()
                    if siguientes:
                        j = 0
                        while j < len(siguientes):
                            sig_simbolo = siguientes[j]
                            if sig_simbolo in no_terminales:
                                temp_set.update(first[sig_simbolo] - {'ε'})
                            else:
                                temp_set.add(sig_simbolo)
                                break
                            if 'ε' not in first[sig_simbolo]:
                                break
                            j += 1
                        if j == len(siguientes):  # Todos pueden ser ε
                            temp_set.update(follow[lhs])
                    else:
                        temp_set.update(follow[lhs])

                    antes = len(follow[simbolo])
                    follow[simbolo].update(temp_set)
                    if len(follow[simbolo]) > antes:
                        cambio = True
    return follow

# Calcular Predict
def calcular_predict(producciones, first):
    predict = defaultdict(list)
    for lhs, cuerpo in producciones:
        conjunto = set()
        elementos = cuerpo[:]
        while elementos:
            simbolo = elementos.pop(0)
            if simbolo in first:
                conjunto.update(first[simbolo])
                if 'ε' not in first[simbolo]:
                    break
            else:
                conjunto.add(simbolo)
                break
        if not conjunto or (len(conjunto) == 1 and 'ε' in conjunto):
            conjunto = set(follow[lhs])
        for t in conjunto:
            predict[(lhs, t)].append((lhs, cuerpo))
    return predict

# Construir tabla sintáctica LL(1)
def construir_tabla(producciones, predict, no_terminales, terminales):
    tabla = defaultdict(dict)
    conflictos = []

    for (nt, t), prods in predict.items():
        if len(prods) > 1:
            conflictos.append(f"Conflicto en [{nt}, {t}]: múltiples producciones")
        elif len(prods) == 1:
            prod = prods[0]
            cuerpo = " ".join(prod[1])
            if t in tabla[nt]:
                conflictos.append(f"Conflicto en [{nt}, {t}]: ya existe una producción")
            tabla[nt][t] = cuerpo
        else:
            tabla[nt][t] = ""
    
    # Rellenar celdas vacías
    for nt in no_terminales:
        for t in terminales:
            if t not in tabla[nt]:
                tabla[nt][t] = ""

    return tabla, conflictos

# Mostrar tabla en consola
def mostrar_tabla(tabla, terminales, no_terminales):
    encabezado = [""] + terminales
    print("+" + "+".join(["-"*15 for _ in encabezado]) + "+")
    print("|" + "|".join([f"{col:^15}" for col in encabezado]) + "|")
    print("+" + "+".join(["-"*15 for _ in encabezado]) + "+")

    for nt in no_terminales:
        fila = [nt]
        for t in terminales:
            contenido = tabla[nt].get(t, "")
            fila.append(contenido[:13] + ".." if len(contenido) > 15 else contenido)
        print("|" + "|".join([f"{celda:^15}" for celda in fila]) + "|")
    print("+" + "+".join(["-"*15 for _ in encabezado]) + "+")

# Guardar tabla en CSV
def guardar_csv(tabla, terminales, no_terminales, archivo='tabla_sintactica.csv'):
    with open(archivo, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')  # <- Aquí se especifica el delimitador
        writer.writerow([''] + terminales)
        for nt in no_terminales:
            fila = [nt]
            for t in terminales:
                fila.append(tabla[nt].get(t, ""))
            writer.writerow(fila)
    print(f"[+] Tabla guardada en '{archivo}'")


# Programa principal
if __name__ == "__main__":
    archivo_gramatica = "gramatica.txt" # Hardcoded path
    print(f"Usando archivo de gramática: {archivo_gramatica}")
    producciones = leer_gramatica(archivo_gramatica)

    # Obtener no terminales y terminales
    no_terminales = set()
    terminales = set()
    for lhs, cuerpo in producciones:
        no_terminales.add(lhs)
        for s in cuerpo:
            if s == 'ε':
                continue
            elif s in tokens or s in ['+', '-', '*', '/', '(', ')', ';', '=', '<', '>']:
                terminales.add(s)
            elif s.isupper() or s in no_terminales:
                no_terminales.add(s)
            else:
                terminales.add(s)

    # Convertir a listas ordenadas
    no_terminales = sorted(no_terminales)
    terminales = sorted(set(terminales) | {'$'})

    # Calcular conjuntos
    first = calcular_first(producciones, no_terminales)
    follow = calcular_follow(producciones, no_terminales, first)
    predict = calcular_predict(producciones, first)
    tabla, conflictos = construir_tabla(producciones, predict, no_terminales, terminales)

    # Mostrar resultados
    mostrar_tabla(tabla, terminales, no_terminales)
    guardar_csv(tabla, terminales, no_terminales)

    if conflictos:
        print("\n[!] La gramática NO es LL(1). Se encontraron conflictos:")
        for msg in conflictos:
            print("   -", msg)
    else:
        print("\n[✓] La gramática es LL(1). No se encontraron conflictos.")