class GeneradorSPIM:
    def __init__(self):
        self.codigo_data = []
        self.codigo_text = []
        self.contador_etiquetas = 0
        self.tabla_simbolos = None
        self.ast_root = None
        self.registros_temporales = [f"$t{i}" for i in range(10)]
        self.registros_usados = [False] * 10
        self.registros_flotantes_temporales = [f"$f{i}" for i in list(range(4, 12)) + list(range(16,30))]
        self.registros_flotantes_usados = [False] * len(self.registros_flotantes_temporales)
        self.funcion_actual_nombre = None
        self.funcion_actual_info = {}
        self.offsets_locales_actuales = {}
        self.offset_local_actual = 0

    def _nueva_etiqueta(self, prefijo="L"):
        self.contador_etiquetas += 1
        return f"{prefijo}{self.contador_etiquetas}"

    def _obtener_registro_temporal(self):
        for i, usado in enumerate(self.registros_usados):
            if not usado:
                self.registros_usados[i] = True
                return self.registros_temporales[i]
        print("ERROR CRÍTICO: ¡No hay registros temporales $tX disponibles! Se necesita spilling.")
        return self.registros_temporales[-1]

    def _obtener_registro_flotante_temporal(self):
        for i, usado in enumerate(self.registros_flotantes_usados):
            if not usado:
                self.registros_flotantes_usados[i] = True
                return self.registros_flotantes_temporales[i]
        print("ERROR CRÍTICO: ¡No hay registros flotantes $fX disponibles! Se necesita spilling.")
        return self.registros_flotantes_temporales[-1]

    def _liberar_registro_temporal(self, registro_a_liberar):
        if registro_a_liberar is None: return # No intentar liberar None
        if registro_a_liberar.startswith("$f"):
            try:
                index = self.registros_flotantes_temporales.index(registro_a_liberar)
                if self.registros_flotantes_usados[index]:
                    self.registros_flotantes_usados[index] = False
                # else: print(f"Advertencia: Intento de liberar registro flotante ({registro_a_liberar}) no usado.")
            except ValueError:
                # No es un temporal nuestro, podría ser $f0, $f12, etc. No hacer nada.
                pass
        elif registro_a_liberar.startswith("$t"):
            try:
                index = self.registros_temporales.index(registro_a_liberar)
                if self.registros_usados[index]:
                    self.registros_usados[index] = False
                # else: print(f"Advertencia: Intento de liberar registro CPU ({registro_a_liberar}) no usado.")
            except ValueError:
                 # No es un temporal nuestro, podría ser $a0, $v0, etc. No hacer nada.
                pass

    def _reset_registros_temporales_para_nueva_expresion(self):
        self.registros_usados = [False] * 10
        self.registros_flotantes_usados = [False] * len(self.registros_flotantes_temporales)

    def _calcular_offsets_funcion_actual(self, nodo_funcion):
        nombre_func = ""
        bloque_nodo = None
        if nodo_funcion.children[0].value == 'MAIN':
            nombre_func = "main"
            bloque_nodo = nodo_funcion.children[4]
            self.funcion_actual_info = {'locals_size': 0, 'params_count': 0, 'params_on_stack_map': {}}
        elif nodo_funcion.children[0].value == 'tipo':
            id_nodo = nodo_funcion.children[1]
            nombre_func = id_nodo.value
            funcion_rest_nodo = nodo_funcion.children[2]
            if len(funcion_rest_nodo.children) == 6: # Es una definición de función completa
                parametros_nodo = funcion_rest_nodo.children[1]
                bloque_nodo = funcion_rest_nodo.children[4]
            else: return # Variable global, no una función con cuerpo
        self.funcion_actual_nombre = nombre_func
        self.offsets_locales_actuales = {}
        self.offset_local_actual = 0
        info_simbolo_func = self.tabla_simbolos.lookup_symbol(nombre_func)
        if not info_simbolo_func or not info_simbolo_func['type'].startswith("FUNCTION"):
            print(f"Error: No se encontró info de función para '{nombre_func}' al calcular offsets.")
            return
        nombres_params_ordenados = info_simbolo_func.get('param_names_ordered', [])
        param_offset = 8
        params_map = {}
        for i, nombre_param in enumerate(nombres_params_ordenados):
            self.offsets_locales_actuales[nombre_param] = param_offset
            params_map[nombre_param] = {'offset': param_offset, 'type': info_simbolo_func['param_types'][i]}
            param_offset += 4
        self.funcion_actual_info = {'locals_size': 0, 'params_count': len(nombres_params_ordenados), 'params_on_stack_map': params_map}
        if bloque_nodo: self._pre_scan_locales(bloque_nodo)

    def _pre_scan_locales(self, nodo_bloque_o_instrucciones):
        if not nodo_bloque_o_instrucciones: return
        for hijo in nodo_bloque_o_instrucciones.children:
            if not hijo: continue
            if hijo.value == 'instrucciones': self._pre_scan_locales(hijo)
            elif hijo.value == 'instruccion':
                if hijo.children and hijo.children[0].value == 'declaracion':
                    decl_node = hijo.children[0]
                    id_node = decl_node.children[1]
                    nombre_var = id_node.value
                    self.offset_local_actual -= 4
                    self.offsets_locales_actuales[nombre_var] = self.offset_local_actual
                    self.funcion_actual_info['locals_size'] += 4
            elif hijo.value == 'If' and len(hijo.children) == 8:
                self._pre_scan_locales(hijo.children[5]) # bloque if
                if hijo.children[7].children and hijo.children[7].children[0].value != 'ε':
                    self._pre_scan_locales(hijo.children[7].children[2]) # bloque else
            elif hijo.value == 'While' and len(hijo.children) == 7: # Similar para While
                 self._pre_scan_locales(hijo.children[5]) # bloque while
            elif hijo.value == 'For' and len(hijo.children) == 11: # Similar para For
                 self._pre_scan_locales(hijo.children[9]) # bloque for
            elif hijo.value == 'bloque': self._pre_scan_locales(hijo)

    def _obtener_offset_variable(self, nombre_variable):
        return self.offsets_locales_actuales.get(nombre_variable)

    def generar(self, ast_root, tabla_simbolos):
        self.ast_root = ast_root
        self.tabla_simbolos = tabla_simbolos
        self.codigo_data.append(".data")
        if "newline_char: .asciiz \"\\n\"" not in self.codigo_data:
            self.codigo_data.append("newline_char: .asciiz \"\\n\"  # Para saltos de línea en print")
        self.codigo_text.append(".text")
        self.codigo_text.append(".globl main")
        self._visitar(ast_root)
        return "\n".join(self.codigo_data) + "\n\n" + "\n".join(self.codigo_text)

    def _visitar(self, nodo):
        if nodo is None: return
        nombre_metodo = f'_visitar_{nodo.value.lower().replace("(", "_lparen_").replace(")", "_rparen_")}'
        visitor = getattr(self, nombre_metodo, self._visitar_generico)
        return visitor(nodo)

    def _visitar_generico(self, nodo):
        if nodo is None: return
        for hijo in nodo.children: self._visitar(hijo)
        return None

    def _visitar_programa(self, nodo):
        for hijo in nodo.children: self._visitar(hijo)

    def _visitar_funciones(self, nodo):
        if nodo.children and nodo.children[0].value != 'ε':
            self._visitar(nodo.children[0])
            if len(nodo.children) > 1: self._visitar(nodo.children[1])

    def _visitar_funcion(self, nodo):
        if not nodo.children: return
        primer_hijo = nodo.children[0]
        nombre_func_o_var = ""
        old_funcion_actual_nombre = self.funcion_actual_nombre
        old_funcion_actual_info = self.funcion_actual_info.copy()
        old_offsets_locales_actuales = self.offsets_locales_actuales.copy()
        old_offset_local_actual = self.offset_local_actual

        is_regular_function_def = (primer_hijo.value == 'tipo' and
                                   len(nodo.children) > 2 and
                                   nodo.children[2].children and
                                   len(nodo.children[2].children) == 6) # LPAREN parametros RPAREN LBRACE bloque RBRACE
        is_main_function = primer_hijo.value == 'MAIN'

        if is_main_function or is_regular_function_def:
            self._calcular_offsets_funcion_actual(nodo)

        if is_main_function:
            nombre_func_o_var = "main"
            if len(nodo.children) == 6 and nodo.children[4].value == 'bloque':
                bloque_nodo_func = nodo.children[4]
                self.codigo_text.append(f"\n{nombre_func_o_var}:")
                self.codigo_text.append(f"  # Prólogo de {nombre_func_o_var}")
                self.codigo_text.append(f"  addiu $sp, $sp, -4   # Espacio para guardar $fp antiguo")
                self.codigo_text.append(f"  sw $fp, 0($sp)        # Guardar frame pointer antiguo")
                self.codigo_text.append(f"  move $fp, $sp         # Nuevo frame pointer")
                locals_total_size = self.funcion_actual_info.get('locals_size', 0)
                if locals_total_size > 0:
                    self.codigo_text.append(f"  addiu $sp, $sp, -{locals_total_size}  # Espacio para locales")
                self._visitar(bloque_nodo_func)
                self.codigo_text.append(f"\n  # Fin de {nombre_func_o_var}")
                if locals_total_size > 0:
                     self.codigo_text.append(f"  move $sp, $fp          # Liberar locales, $sp apunta a $fp guardado")
                self.codigo_text.append(f"  lw $fp, 0($sp)        # Restaurar $fp antiguo")
                self.codigo_text.append(f"  addiu $sp, $sp, 4   # Liberar espacio de $fp guardado")
                self.codigo_text.append(f"  li $v0, 10            # Syscall para terminar programa")
                self.codigo_text.append(f"  syscall")
        elif primer_hijo.value == 'tipo':
            id_nodo = nodo.children[1]
            nombre_func_o_var = id_nodo.value
            funcion_rest_nodo = nodo.children[2]
            if funcion_rest_nodo.children and len(funcion_rest_nodo.children) == 2 and \
               funcion_rest_nodo.children[0].value == 'inicializacion' and \
               funcion_rest_nodo.children[1].value == 'SEMI': # Variable Global
                tipo_str = self._obtener_tipo_de_nodo_tipo(primer_hijo)
                inicializacion_nodo = funcion_rest_nodo.children[0]
                # ... (código de manejo de variables globales sin cambios) ...
                if tipo_str == 'int' or tipo_str == 'bool':
                    valor_inicial = 0
                    if inicializacion_nodo.children and inicializacion_nodo.children[0].value != 'ε':
                        exp_nodo = inicializacion_nodo.children[1]
                        val_expr = self._evaluar_expresion_literal_para_data(exp_nodo)
                        if val_expr is not None: valor_inicial = val_expr
                        else: print(f"Advertencia: Inicializador no constante para global '{nombre_func_o_var}'.")
                    self.codigo_data.append(f"  {nombre_func_o_var}: .word {valor_inicial}  # Global {tipo_str}")
                elif tipo_str == 'float':
                    valor_inicial = 0.0
                    if inicializacion_nodo.children and inicializacion_nodo.children[0].value != 'ε':
                        exp_nodo = inicializacion_nodo.children[1]
                        val_expr = self._evaluar_expresion_literal_para_data(exp_nodo)
                        if isinstance(val_expr, (int, float)): valor_inicial = float(val_expr)
                        else: print(f"Advertencia: Inicializador no constante/numérico para global float '{nombre_func_o_var}'.")
                    self.codigo_data.append(f"  {nombre_func_o_var}: .float {valor_inicial:.6f}  # Global float")
                elif tipo_str == 'string':
                    valor_inicial_str = None
                    if inicializacion_nodo.children and inicializacion_nodo.children[0].value != 'ε':
                        exp_nodo = inicializacion_nodo.children[1]
                        val_expr = self._evaluar_expresion_literal_para_data(exp_nodo)
                        if isinstance(val_expr, str):
                            valor_inicial_str = val_expr
                        else: print(f"Advertencia: Inicializador no string para global string '{nombre_func_o_var}'.")
                    if valor_inicial_str is not None:
                        self.codigo_data.append(f"  {nombre_func_o_var}: .asciiz \"{valor_inicial_str}\"  # Global string")
                    else:
                        self.codigo_data.append(f"  {nombre_func_o_var}: .word 0  # Global string (puntero no inicializado)")
                else: print(f"Advertencia: Tipo global '{tipo_str}' no manejado para .data.")
            elif is_regular_function_def: # Definición de función regular (no main)
                id_func_actual = nombre_func_o_var # Ya se obtuvo de id_nodo.value
                info_func_ts = self.tabla_simbolos.lookup_symbol(id_func_actual, "global")
                self.funcion_actual_return_type = info_func_ts['type'].split(' -> ')[-1].lower() if info_func_ts else "unknown"

                bloque_nodo_func = funcion_rest_nodo.children[4]
                self.codigo_text.append(f"\n{nombre_func_o_var}:  # Definición de función '{nombre_func_o_var}'")
                self.codigo_text.append(f"  # Prólogo de {nombre_func_o_var}")
                self.codigo_text.append(f"  addiu $sp, $sp, -8   # Espacio para guardar $ra y $fp antiguos")
                self.codigo_text.append(f"  sw $ra, 4($sp)        # Guardar dirección de retorno $ra")
                self.codigo_text.append(f"  sw $fp, 0($sp)        # Guardar frame pointer antiguo")
                self.codigo_text.append(f"  move $fp, $sp         # Nuevo frame pointer")
                locals_total_size = self.funcion_actual_info.get('locals_size',0)
                if locals_total_size > 0:
                    self.codigo_text.append(f"  addiu $sp, $sp, -{locals_total_size}  # Espacio para locales")
                self._visitar(bloque_nodo_func)
                epilogo_label = self._nueva_etiqueta(f"epilogo_{nombre_func_o_var}")
                self.codigo_text.append(f"{epilogo_label}:") # Etiqueta para saltos de return
                self.codigo_text.append(f"  # Epílogo de {nombre_func_o_var}")
                if locals_total_size > 0: # Liberar locales
                     self.codigo_text.append(f"  move $sp, $fp          # $sp apunta a $fp/$ra guardados")
                self.codigo_text.append(f"  lw $fp, 0($sp)        # Restaurar $fp antiguo")
                self.codigo_text.append(f"  lw $ra, 4($sp)        # Restaurar $ra original")
                self.codigo_text.append(f"  addiu $sp, $sp, 8   # Liberar espacio de $ra y $fp guardados")
                self.codigo_text.append(f"  jr $ra                # Retorno de {nombre_func_o_var}")
        else: self._visitar_generico(nodo)

        self.funcion_actual_nombre = old_funcion_actual_nombre
        self.funcion_actual_info = old_funcion_actual_info
        self.offsets_locales_actuales = old_offsets_locales_actuales
        self.offset_local_actual = old_offset_local_actual

    def _obtener_tipo_de_nodo_tipo(self, tipo_node):
        # ... (sin cambios)
        if tipo_node and tipo_node.value == 'tipo' and tipo_node.children:
            type_keyword_node = tipo_node.children[0]
            type_mapping = {'INT': 'int', 'FLOAT': 'float', 'BOOL': 'bool', 'STRING': 'string', 'VOID': 'void'}
            return type_mapping.get(type_keyword_node.value, "UnknownType")
        return "UnknownType"

    def _evaluar_expresion_literal_para_data(self, exp_nodo):
        # ... (sin cambios)
        try:
            nodo_a = exp_nodo.children[0].children[0].children[0].children[0].children[0].children[0]
            literal_node = nodo_a.children[0]
            if isinstance(literal_node.value, int): return int(literal_node.value)
            if isinstance(literal_node.value, float): return float(literal_node.value)
            if literal_node.value == 'true': return 1
            if literal_node.value == 'false': return 0
            if isinstance(literal_node.value, str) and nodo_a.children[0].value.startswith('"'):
                 val_str = literal_node.value
                 if val_str.startswith('"') and val_str.endswith('"'): val_str = val_str[1:-1]
                 return val_str
        except: pass
        return None

    def _visitar_bloque(self, nodo):
        # ... (sin cambios)
        for hijo in nodo.children:
            if hijo.value == 'instrucciones' or hijo.value == 'ε': self._visitar(hijo)

    def _visitar_instrucciones(self, nodo):
        # ... (sin cambios)
        if nodo.children and nodo.children[0].value != 'ε':
            self._visitar(nodo.children[0])
            if len(nodo.children) > 1: self._visitar(nodo.children[1])

    def _visitar_instruccion(self, nodo_instruccion):
        if nodo_instruccion.children:
            nodo_principal_instruccion = nodo_instruccion.children[0] # Puede ser ID, Print, If, etc.

            # Caso: ID (podría ser asignación o llamada a función como statement)
            if nodo_principal_instruccion.value not in ['declaracion', 'Print', 'If', 'While', 'For', 'Return', 'bloque', 'MAIN'] and \
               len(nodo_instruccion.children) > 1 and nodo_instruccion.children[1].value == 'id_rhs_instruccion':

                id_nodo_lhs = nodo_principal_instruccion # Este es el ID
                id_rhs_nodo = nodo_instruccion.children[1]

                # Subcaso: Asignación (ID EQUALS exp SEMI)
                if id_rhs_nodo.children and id_rhs_nodo.children[0].value == 'EQUALS':
                    exp_nodo_rhs = id_rhs_nodo.children[1]
                    self._generar_asignacion(id_nodo_lhs, exp_nodo_rhs)
                # Subcaso: Llamada a función como statement (ID llamada_func SEMI)
                elif id_rhs_nodo.children and id_rhs_nodo.children[0].value == 'llamada_func':
                    llamada_func_nodo = id_rhs_nodo.children[0]
                    self.codigo_text.append(f"  # Inicio llamada a función (statement): {id_nodo_lhs.value}")
                    # id_nodo_lhs es el nodo ID de la función
                    # llamada_func_nodo es el nodo 'llamada_func'
                    reg_ret_ignorado = self._visitar_llamada_func_como_expresion(id_nodo_lhs, llamada_func_nodo)
                    self._liberar_registro_temporal(reg_ret_ignorado) # Liberar si se usó un temporal para el retorno
                    self.codigo_text.append(f"  # Fin llamada a función (statement): {id_nodo_lhs.value}")
                else:
                    # Podría ser un ID solo seguido de SEMI (aunque la gramática podría no permitirlo como instrucción)
                    # o alguna otra estructura no esperada aquí.
                    self.codigo_text.append(f"  # Instrucción con ID '{id_nodo_lhs.value}' no reconocida completamente.")
                    self._visitar(nodo_principal_instruccion) # Comportamiento genérico si no coincide

            # Caso: Otras instrucciones directas (Print, If, While, For, Return, declaracion, bloque)
            else:
                self._visitar(nodo_principal_instruccion)

            self._reset_registros_temporales_para_nueva_expresion()

    def _generar_asignacion(self, id_nodo_lhs, exp_nodo_rhs):
        nombre_variable = id_nodo_lhs.value
        # Comentario mejorado
        self.codigo_text.append(f"  # Inicio Asignación: {nombre_variable} = ...")
        resultado_rhs = self._visitar(exp_nodo_rhs)
        if resultado_rhs is None or resultado_rhs[0] is None:
            print(f"Error: No se obtuvo valor/registro para RHS en asignación a '{nombre_variable}'.")
            return
        reg_rhs, tipo_rhs_str = resultado_rhs
        simbolo_lhs = self.tabla_simbolos.lookup_symbol(nombre_variable, self.funcion_actual_nombre)
        if not simbolo_lhs:
            print(f"Error de generación: Variable LHS '{nombre_variable}' no encontrada.")
            self._liberar_registro_temporal(reg_rhs)
            return
        tipo_lhs_str = simbolo_lhs['type'].lower()
        store_instruction = "sw"
        comment_type = "entero/puntero"
        if tipo_lhs_str == "float":
            store_instruction = "s.s"
            comment_type = "float"
            if not reg_rhs.startswith("$f"):
                print(f"ADVERTENCIA: Asignando a float '{nombre_variable}' pero RHS reg '{reg_rhs}' no es FPU. Se requiere conversión.")
                # Aquí se necesitaría conversión explícita si no se hizo en la expresión
        offset = self._obtener_offset_variable(nombre_variable)
        if offset is not None:
            self.codigo_text.append(f"  {store_instruction} {reg_rhs}, {offset}($fp)  # Guardar {comment_type} en local '{nombre_variable}'")
        elif simbolo_lhs['scope_attr'] == 'global':
            self.codigo_text.append(f"  {store_instruction} {reg_rhs}, {nombre_variable}  # Guardar {comment_type} en global '{nombre_variable}'")
        else: print(f"Error: Variable '{nombre_variable}' sin ubicación para asignación.")
        self._liberar_registro_temporal(reg_rhs)
        self.codigo_text.append(f"  # Fin Asignación: {nombre_variable}")


    def _visitar_declaracion(self, nodo_decl):
        # ... (lógica de obtención de nombre_variable, tipo_str, offset sin cambios) ...
        tipo_nodo = nodo_decl.children[0]
        id_nodo = nodo_decl.children[1]
        inicializacion_nodo = nodo_decl.children[2]
        nombre_variable = id_nodo.value
        tipo_str = self._obtener_tipo_de_nodo_tipo(tipo_nodo)
        offset = self._obtener_offset_variable(nombre_variable)

        # Comentario para la declaración (reserva de espacio ya hecha en prólogo)
        self.codigo_text.append(f"  # Declaración de local '{nombre_variable}' de tipo {tipo_str} en offset {offset}($fp)")


        if offset is None and self.funcion_actual_nombre: # Esto es un parche, el pre-scan debería haberlo cubierto
            print(f"Error CRÍTICO: Local '{nombre_variable}' sin offset en _visitar_declaracion.")
            self.offset_local_actual -= 4
            self.offsets_locales_actuales[nombre_variable] = self.offset_local_actual
            self.funcion_actual_info['locals_size'] += 4
            offset = self.offset_local_actual
            self.codigo_text.append(f"  # ADVERTENCIA: Offset para '{nombre_variable}' asignado dinámicamente: {offset}($fp)")

        if inicializacion_nodo.children and inicializacion_nodo.children[0].value != 'ε':
            self.codigo_text.append(f"  # Inicio Inicialización de '{nombre_variable}'")
            exp_nodo_rhs = inicializacion_nodo.children[1]
            resultado_rhs = self._visitar(exp_nodo_rhs)
            if resultado_rhs is None or resultado_rhs[0] is None:
                print(f"Error: No se obtuvo reg para inicializador de '{nombre_variable}'.")
                if offset is not None:
                    if tipo_str == 'float':
                        # Cargar 0.0 a un registro flotante y guardarlo
                        reg_fzero = self._obtener_registro_flotante_temporal()
                        zero_float_label = self._nueva_etiqueta("zero_float_lit_")
                        if f"{zero_float_label}: .float 0.0" not in self.codigo_data: # Evitar duplicados
                             self.codigo_data.append(f"  {zero_float_label}: .float 0.0")
                        self.codigo_text.append(f"  l.s {reg_fzero}, {zero_float_label}   # Cargar 0.0 para inicializar {nombre_variable}")
                        self.codigo_text.append(f"  s.s {reg_fzero}, {offset}($fp)      # Inicializar float local '{nombre_variable}' a 0.0")
                        self._liberar_registro_temporal(reg_fzero)
                    else: # int, bool, string (puntero)
                        reg_zero = self._obtener_registro_temporal()
                        self.codigo_text.append(f"  li {reg_zero}, 0")
                        self.codigo_text.append(f"  sw {reg_zero}, {offset}($fp)      # Inicializar local '{nombre_variable}' a 0 por error en RHS")
                        self._liberar_registro_temporal(reg_zero)
                return

            reg_rhs, tipo_rhs_str = resultado_rhs
            if offset is not None:
                store_instr_decl = "sw"
                comment_type_decl = "entero/puntero"
                if tipo_str == 'float':
                    store_instr_decl = "s.s"
                    comment_type_decl = "float"
                    if not reg_rhs.startswith("$f"):
                         print(f"ADVERTENCIA: Inicializando float local '{nombre_variable}' pero RHS reg '{reg_rhs}' no es FPU.")
                         # Aquí se necesitaría conversión explícita si no se hizo en la expresión RHS
                self.codigo_text.append(f"  {store_instr_decl} {reg_rhs}, {offset}($fp)  # Inicializar local '{nombre_variable}' ({comment_type_decl})")
            else: print(f"Error: No se pudo almacenar inicialización para '{nombre_variable}'.")
            self._liberar_registro_temporal(reg_rhs)
            self.codigo_text.append(f"  # Fin Inicialización de '{nombre_variable}'")


    def _visitar_print(self, nodo_print_rule):
        # ... (lógica sin cambios significativos, excepto comentarios y liberación de reg_con_valor)
        exp_opt_nodo = nodo_print_rule.children[2]
        if exp_opt_nodo.children and exp_opt_nodo.children[0].value != 'ε':
            exp_nodo_a_imprimir = exp_opt_nodo.children[0]
            self.codigo_text.append(f"  # Inicio Print: evaluando expresión en línea {exp_nodo_a_imprimir.lineno}")
            resultado_exp = self._visitar(exp_nodo_a_imprimir)
            if resultado_exp is None or resultado_exp[0] is None:
                print(f"Error: No se pudo obtener valor/tipo para print en línea {exp_opt_nodo.lineno}.")
                # Aun así, imprimir un newline
                self.codigo_text.append(f"  la $a0, newline_char  # Cargar dirección de newline")
                self.codigo_text.append(f"  li $v0, 4             # Syscall para imprimir string")
                self.codigo_text.append(f"  syscall")
                return

            reg_con_valor, tipo_expresion = resultado_exp

            self.codigo_text.append(f"  # Print: valor de tipo '{tipo_expresion}' en registro '{reg_con_valor}'")
            if tipo_expresion == "int" or tipo_expresion == "bool":
                self.codigo_text.append(f"  move $a0, {reg_con_valor}    # Preparar para imprimir int/bool")
                self.codigo_text.append(f"  li $v0, 1           # Syscall para imprimir entero")
            elif tipo_expresion == "string":
                self.codigo_text.append(f"  move $a0, {reg_con_valor}    # Preparar para imprimir string (dirección)")
                self.codigo_text.append(f"  li $v0, 4           # Syscall para imprimir string")
            elif tipo_expresion == "float":
                self.codigo_text.append(f"  mov.s $f12, {reg_con_valor} # Mover float a $f12 para imprimir")
                self.codigo_text.append(f"  li $v0, 2             # Syscall para imprimir float")
            else:
                print(f"Advertencia: Tipo desconocido '{tipo_expresion}' para print. Intentando imprimir como entero.")
                self.codigo_text.append(f"  move $a0, {reg_con_valor}    # Fallback: Mover a $a0")
                self.codigo_text.append(f"  li $v0, 1             # Fallback: Syscall para imprimir entero")
            self.codigo_text.append(f"  syscall               # Ejecutar print")
            self._liberar_registro_temporal(reg_con_valor) # Liberar después de usarlo en syscall

        self.codigo_text.append(f"  la $a0, newline_char  # Cargar dirección de newline")
        self.codigo_text.append(f"  li $v0, 4             # Syscall para imprimir string (newline)")
        self.codigo_text.append(f"  syscall               # Ejecutar print de newline")
        self.codigo_text.append(f"  # Fin Print")

    # ... (resto de los visitors de expresiones con posibles mejoras en comentarios y liberación de registros)

    def _visitar_exp(self, nodo_exp):
        # ... (sin cambios)
        if nodo_exp.children: return self._visitar(nodo_exp.children[0])
        return None, None

    def _visitar_e(self, nodo_e):
        # ... (sin cambios)
        if len(nodo_e.children) == 2:
            reg_c, tipo_c = self._visitar(nodo_e.children[0])
            if reg_c is None: return None, None
            return self._visitar_e_rest(nodo_e.children[1], reg_c, tipo_c)
        return None, None

    def _visitar_e_rest(self, nodo_e_rest, reg_lhs, tipo_lhs):
        # ... (revisar liberación de reg_rhs)
        if nodo_e_rest.children and nodo_e_rest.children[0].value != 'ε':
            op_nodo = nodo_e_rest.children[0]
            reg_rhs, tipo_rhs = self._visitar(nodo_e_rest.children[1])
            if reg_rhs is None:
                self._liberar_registro_temporal(reg_lhs) # Liberar LHS si RHS falla
                return None, None
            if tipo_lhs == 'bool' and tipo_rhs == 'bool':
                self.codigo_text.append(f"  # Operación OR: {reg_lhs} = {reg_lhs} or {reg_rhs}")
                self.codigo_text.append(f"  or {reg_lhs}, {reg_lhs}, {reg_rhs}")
                self._liberar_registro_temporal(reg_rhs) # Liberar RHS después de la operación
                return self._visitar_e_rest(nodo_e_rest.children[2], reg_lhs, 'bool')
            else:
                print(f"Error de tipo en OR: {tipo_lhs} con {tipo_rhs}")
                self._liberar_registro_temporal(reg_lhs)
                self._liberar_registro_temporal(reg_rhs)
                return None, None
        return reg_lhs, tipo_lhs

    def _visitar_c(self, nodo_c):
        # ... (sin cambios)
        if len(nodo_c.children) == 2:
            reg_r, tipo_r = self._visitar(nodo_c.children[0])
            if reg_r is None: return None, None
            return self._visitar_c_rest(nodo_c.children[1], reg_r, tipo_r)
        return None, None

    def _visitar_c_rest(self, nodo_c_rest, reg_lhs, tipo_lhs):
        # ... (revisar liberación de reg_rhs)
        if nodo_c_rest.children and nodo_c_rest.children[0].value != 'ε':
            op_nodo = nodo_c_rest.children[0]
            reg_rhs, tipo_rhs = self._visitar(nodo_c_rest.children[1])
            if reg_rhs is None:
                self._liberar_registro_temporal(reg_lhs)
                return None, None
            if tipo_lhs == 'bool' and tipo_rhs == 'bool':
                self.codigo_text.append(f"  # Operación AND: {reg_lhs} = {reg_lhs} and {reg_rhs}")
                self.codigo_text.append(f"  and {reg_lhs}, {reg_lhs}, {reg_rhs}")
                self._liberar_registro_temporal(reg_rhs)
                return self._visitar_c_rest(nodo_c_rest.children[2], reg_lhs, 'bool')
            else:
                print(f"Error de tipo en AND: {tipo_lhs} con {tipo_rhs}")
                self._liberar_registro_temporal(reg_lhs)
                self._liberar_registro_temporal(reg_rhs)
                return None, None
        return reg_lhs, tipo_lhs


    def _visitar_r(self, nodo_r):
        # ... (sin cambios)
        if len(nodo_r.children) == 2:
            reg_t, tipo_t = self._visitar(nodo_r.children[0])
            if reg_t is None: return None, None
            return self._visitar_r_rest(nodo_r.children[1], reg_t, tipo_t)
        return None, None

    def _visitar_r_rest(self, nodo_r_rest, reg_lhs, tipo_lhs):
        # ... (revisar liberación de reg_rhs, comentarios para comparaciones)
        if nodo_r_rest.children and nodo_r_rest.children[0].value != 'ε':
            op_nodo = nodo_r_rest.children[0]
            op_nombre = op_nodo.value
            reg_rhs, tipo_rhs = self._visitar(nodo_r_rest.children[1])
            if reg_rhs is None:
                self._liberar_registro_temporal(reg_lhs)
                return None, None

            self.codigo_text.append(f"  # Comparación {op_nombre}: {reg_lhs} vs {reg_rhs}")
            # TODO: Comparaciones flotantes (c.eq.s, c.lt.s, etc. y luego bc1t/bc1f)
            if tipo_lhs == 'float' or tipo_rhs == 'float':
                print(f"Advertencia: Comparación de/con flotantes ({op_nombre}) no completamente implementada.")
                # Aquí se necesitarían instrucciones c.xx.s y bc1t/f

            if op_nombre == 'EQ':   self.codigo_text.append(f"  seq {reg_lhs}, {reg_lhs}, {reg_rhs}")
            elif op_nombre == 'NE': self.codigo_text.append(f"  sne {reg_lhs}, {reg_lhs}, {reg_rhs}")
            elif op_nombre == 'LT': self.codigo_text.append(f"  slt {reg_lhs}, {reg_lhs}, {reg_rhs}")
            elif op_nombre == 'GT': self.codigo_text.append(f"  sgt {reg_lhs}, {reg_lhs}, {reg_rhs}")
            elif op_nombre == 'LE': self.codigo_text.append(f"  sle {reg_lhs}, {reg_lhs}, {reg_rhs}")
            elif op_nombre == 'GE': self.codigo_text.append(f"  sge {reg_lhs}, {reg_lhs}, {reg_rhs}")
            else: print(f"Operador relacional '{op_nombre}' no manejado.")

            self._liberar_registro_temporal(reg_rhs) # RHS siempre se puede liberar después de la comparación
            return self._visitar_r_rest(nodo_r_rest.children[2], reg_lhs, 'bool') # Resultado es booleano
        return reg_lhs, tipo_lhs


    def _visitar_t(self, nodo_t):
        # ... (sin cambios)
        if len(nodo_t.children) == 2:
            reg_f, tipo_f = self._visitar(nodo_t.children[0])
            if reg_f is None: return None,None
            return self._visitar_t_rest(nodo_t.children[1], reg_f, tipo_f)
        return None, None

    def _visitar_t_rest(self, nodo_t_rest, reg_lhs, tipo_lhs):
        if nodo_t_rest.children and nodo_t_rest.children[0].value != 'ε':
            op_nodo = nodo_t_rest.children[0]
            reg_rhs, tipo_rhs = self._visitar(nodo_t_rest.children[1])
            if reg_rhs is None:
                self._liberar_registro_temporal(reg_lhs)
                return None, None

            tipo_resultado = "unknown"
            reg_final_lhs = reg_lhs # El registro que contendrá el resultado final

            self.codigo_text.append(f"  # Operación {op_nodo.value} ({tipo_lhs} y {tipo_rhs})")

            if tipo_lhs == 'int' and tipo_rhs == 'int':
                tipo_resultado = 'int'
                if op_nodo.value == 'PLUS':
                    self.codigo_text.append(f"  add {reg_final_lhs}, {reg_lhs}, {reg_rhs}  # Suma int: {reg_final_lhs} = {reg_lhs} + {reg_rhs}")
                elif op_nodo.value == 'MINUS':
                    self.codigo_text.append(f"  sub {reg_final_lhs}, {reg_lhs}, {reg_rhs}  # Resta int: {reg_final_lhs} = {reg_lhs} - {reg_rhs}")
                self._liberar_registro_temporal(reg_rhs)
            elif tipo_lhs == 'float' and tipo_rhs == 'float':
                tipo_resultado = 'float'
                # Asegurarse que reg_final_lhs es un registro FPU si no lo era (aunque debería serlo si tipo_lhs es float)
                if not reg_final_lhs.startswith("$f"): # Caso poco probable si la lógica es correcta
                    self._liberar_registro_temporal(reg_final_lhs) # Liberar el $t si se reasigna
                    reg_final_lhs = self._obtener_registro_flotante_temporal()

                if op_nodo.value == 'PLUS':
                    self.codigo_text.append(f"  add.s {reg_final_lhs}, {reg_lhs}, {reg_rhs}  # Suma float: {reg_final_lhs} = {reg_lhs} + {reg_rhs}")
                elif op_nodo.value == 'MINUS':
                    self.codigo_text.append(f"  sub.s {reg_final_lhs}, {reg_lhs}, {reg_rhs}  # Resta float: {reg_final_lhs} = {reg_lhs} - {reg_rhs}")
                self._liberar_registro_temporal(reg_rhs)
            elif (tipo_lhs == 'int' and tipo_rhs == 'float') or \
                 (tipo_lhs == 'float' and tipo_rhs == 'int'):
                tipo_resultado = 'float'
                fpu_reg_lhs = reg_lhs
                fpu_reg_rhs = reg_rhs

                fpu_reg_lhs = reg_lhs
                fpu_reg_rhs = reg_rhs

                if tipo_lhs == 'int':
                    fpu_reg_lhs = self._obtener_registro_flotante_temporal()
                    self.codigo_text.append(f"  mtc1 {reg_lhs}, {fpu_reg_lhs}            # Mover int ({reg_lhs}) a FPU para op {op_nodo.value}")
                    self.codigo_text.append(f"  cvt.s.w {fpu_reg_lhs}, {fpu_reg_lhs}      # Convertir a float")
                    # No liberar reg_lhs aquí si es el mismo que reg_final_lhs y fpu_reg_lhs fue un nuevo temporal
                    if reg_lhs != reg_final_lhs : self._liberar_registro_temporal(reg_lhs)
                elif not fpu_reg_lhs.startswith("$f"): # LHS es float pero no está en reg FPU (error previo?)
                    print(f"ADVERTENCIA: Operando LHS float {reg_lhs} no está en registro FPU para op {op_nodo.value}")
                    # Intentar moverlo si es un $t que contiene un patrón de bits float
                    # Esto es muy arriesgado, el tipo debería garantizar que ya está en FPU
                    temp_f_lhs = self._obtener_registro_flotante_temporal()
                    self.codigo_text.append(f"  mtc1 {reg_lhs}, {temp_f_lhs} # Moviendo supuestamente float de CPU a FPU")
                    self._liberar_registro_temporal(reg_lhs)
                    fpu_reg_lhs = temp_f_lhs

                if tipo_rhs == 'int':
                    temp_fpu_for_rhs_conv = self._obtener_registro_flotante_temporal()
                    self.codigo_text.append(f"  mtc1 {reg_rhs}, {temp_fpu_for_rhs_conv} # Mover int ({reg_rhs}) a FPU para op {op_nodo.value}")
                    self.codigo_text.append(f"  cvt.s.w {temp_fpu_for_rhs_conv}, {temp_fpu_for_rhs_conv} # Convertir a float")
                    self._liberar_registro_temporal(reg_rhs)
                    fpu_reg_rhs = temp_fpu_for_rhs_conv
                elif not fpu_reg_rhs.startswith("$f"):
                     print(f"ADVERTENCIA: Operando RHS float {reg_rhs} no está en registro FPU para op {op_nodo.value}")
                     temp_f_rhs = self._obtener_registro_flotante_temporal()
                     self.codigo_text.append(f"  mtc1 {reg_rhs}, {temp_f_rhs} # Moviendo supuestamente float de CPU a FPU")
                     self._liberar_registro_temporal(reg_rhs)
                     fpu_reg_rhs = temp_f_rhs

                # El resultado debe estar en un registro FPU. Si fpu_reg_lhs era originalmente un $tX,
                # entonces reg_final_lhs (que es fpu_reg_lhs) ya es el nuevo FPU temporal.
                # Si fpu_reg_lhs era ya un FPU, se reutiliza.
                reg_final_lhs = fpu_reg_lhs

                if op_nodo.value == 'PLUS': self.codigo_text.append(f"  add.s {reg_final_lhs}, {fpu_reg_lhs}, {fpu_reg_rhs}  # Suma float (mixto)")
                elif op_nodo.value == 'MINUS': self.codigo_text.append(f"  sub.s {reg_final_lhs}, {fpu_reg_lhs}, {fpu_reg_rhs}  # Resta float (mixto)")

                if fpu_reg_rhs != reg_final_lhs:
                     self._liberar_registro_temporal(fpu_reg_rhs) # Libera el FPU temporal de RHS si se creó uno diferente al destino

            elif tipo_lhs == 'string' and tipo_rhs == 'string' and op_nodo.value == 'PLUS':
                self.codigo_text.append(f"  # TODO: Concatenación de strings: {reg_lhs} + {reg_rhs}")
                print("TODO: Concatenación de strings no implementada en _visitar_t_rest.")
                tipo_resultado = 'string'
                # Aquí, reg_lhs y reg_rhs contienen direcciones. Necesitaríamos una rutina.
                # Por ahora, simplemente pasamos el LHS y liberamos el RHS. Esto es incorrecto.
                self._liberar_registro_temporal(reg_rhs)
            else:
                print(f"Error: Tipos incompatibles para {op_nodo.value}: {tipo_lhs} y {tipo_rhs}")
                self._liberar_registro_temporal(reg_lhs) # Liberar ambos si son temporales y hay error
                self._liberar_registro_temporal(reg_rhs)
                return None, None

            # No liberar reg_rhs si ya se liberó específicamente (ej. conversión int a float)
            # if reg_rhs.startswith("$t") and not (tipo_resultado == 'float' and tipo_rhs == 'int') : self._liberar_registro_temporal(reg_rhs)

            return self._visitar_t_rest(nodo_t_rest.children[2], reg_final_lhs, tipo_resultado)
        return reg_lhs, tipo_lhs


    def _visitar_f(self, nodo_f):
        # ... (sin cambios)
        if len(nodo_f.children) == 2:
            reg_a, tipo_a = self._visitar(nodo_f.children[0])
            if reg_a is None: return None,None
            return self._visitar_f_rest(nodo_f.children[1], reg_a, tipo_a)
        return None,None

    def _visitar_f_rest(self, nodo_f_rest, reg_lhs, tipo_lhs):
        # ... (similar a _visitar_t_rest, aplicar misma lógica de tipos y liberación)
        if nodo_f_rest.children and nodo_f_rest.children[0].value != 'ε':
            op_nodo = nodo_f_rest.children[0]
            reg_rhs, tipo_rhs = self._visitar(nodo_f_rest.children[1])
            if reg_rhs is None:
                self._liberar_registro_temporal(reg_lhs)
                return None,None

            tipo_resultado = "unknown"
            reg_final_lhs = reg_lhs
            self.codigo_text.append(f"  # Operación {op_nodo.value} ({tipo_lhs} y {tipo_rhs})")

            if tipo_lhs == 'int' and tipo_rhs == 'int':
                tipo_resultado = 'int'
                if op_nodo.value == 'TIMES':
                    self.codigo_text.append(f"  mult {reg_lhs}, {reg_rhs}     # Mult int: {reg_lhs} * {reg_rhs}")
                    self.codigo_text.append(f"  mflo {reg_final_lhs}            # Resultado en {reg_final_lhs}")
                elif op_nodo.value == 'DIVIDE':
                    self.codigo_text.append(f"  # División entera: {reg_lhs} / {reg_rhs}")
                    self.codigo_text.append(f"  div {reg_lhs}, {reg_rhs}       # $LO = cociente, $HI = residuo")
                    self.codigo_text.append(f"  mflo {reg_final_lhs}            # Cociente en {reg_final_lhs}")
                elif op_nodo.value == 'MOD':
                    self.codigo_text.append(f"  # Módulo: {reg_lhs} % {reg_rhs}")
                    self.codigo_text.append(f"  div {reg_lhs}, {reg_rhs}       # $LO = cociente, $HI = residuo")
                    self.codigo_text.append(f"  mfhi {reg_final_lhs}            # Residuo en {reg_final_lhs}")
                self._liberar_registro_temporal(reg_rhs)
            elif tipo_lhs == 'float' and tipo_rhs == 'float':
                tipo_resultado = 'float'
                # Asegurar que reg_final_lhs es FPU
                if not reg_final_lhs.startswith("$f"):
                    self._liberar_registro_temporal(reg_final_lhs)
                    reg_final_lhs = self._obtener_registro_flotante_temporal()

                if op_nodo.value == 'TIMES':
                    self.codigo_text.append(f"  mul.s {reg_final_lhs}, {reg_lhs}, {reg_rhs} # Mult float: {reg_final_lhs} = {reg_lhs} * {reg_rhs}")
                elif op_nodo.value == 'DIVIDE':
                    self.codigo_text.append(f"  div.s {reg_final_lhs}, {reg_lhs}, {reg_rhs} # Div float: {reg_final_lhs} = {reg_lhs} / {reg_rhs}")
                elif op_nodo.value == 'MOD':
                    print(f"Error: Operador MOD no aplica a floats ({tipo_lhs} % {tipo_rhs})")
                    self._liberar_registro_temporal(reg_lhs)
                    self._liberar_registro_temporal(reg_rhs)
                    return None, None
                self._liberar_registro_temporal(reg_rhs)
            elif (tipo_lhs == 'int' and tipo_rhs == 'float') or \
                 (tipo_lhs == 'float' and tipo_rhs == 'int'):
                tipo_resultado = 'float'
                fpu_reg_lhs = reg_lhs
                fpu_reg_rhs = reg_rhs
                if tipo_lhs == 'int':
                    fpu_reg_lhs = self._obtener_registro_flotante_temporal()
                    self.codigo_text.append(f"  mtc1 {reg_lhs}, {fpu_reg_lhs}            # Mover int ({reg_lhs}) a FPU para op {op_nodo.value}")
                    self.codigo_text.append(f"  cvt.s.w {fpu_reg_lhs}, {fpu_reg_lhs}      # Convertir a float")
                    self._liberar_registro_temporal(reg_lhs)
                if tipo_rhs == 'int':
                    temp_fpu_for_rhs_conv = self._obtener_registro_flotante_temporal()
                    self.codigo_text.append(f"  mtc1 {reg_rhs}, {temp_fpu_for_rhs_conv} # Mover int ({reg_rhs}) a FPU para op {op_nodo.value}")
                    self.codigo_text.append(f"  cvt.s.w {temp_fpu_for_rhs_conv}, {temp_fpu_for_rhs_conv} # Convertir a float")
                    self._liberar_registro_temporal(reg_rhs)
                    fpu_reg_rhs = temp_fpu_for_rhs_conv

                reg_final_lhs = fpu_reg_lhs
                if op_nodo.value == 'TIMES':
                    self.codigo_text.append(f"  mul.s {reg_final_lhs}, {fpu_reg_lhs}, {fpu_reg_rhs} # Mult float (mixto): {reg_final_lhs} = {fpu_reg_lhs} * {fpu_reg_rhs}")
                elif op_nodo.value == 'DIVIDE':
                    self.codigo_text.append(f"  div.s {reg_final_lhs}, {fpu_reg_lhs}, {fpu_reg_rhs} # Div float (mixto): {reg_final_lhs} = {fpu_reg_lhs} / {fpu_reg_rhs}")
                elif op_nodo.value == 'MOD':
                     print(f"Error: Operador MOD no aplica a floats ({tipo_lhs} % {tipo_rhs})")
                     self._liberar_registro_temporal(reg_final_lhs)
                     self._liberar_registro_temporal(fpu_reg_rhs)
                     return None,None
                if fpu_reg_rhs != reg_final_lhs : self._liberar_registro_temporal(fpu_reg_rhs)
            else:
                print(f"Error: Tipos incompatibles para {op_nodo.value}: {tipo_lhs} y {tipo_rhs}")
                self._liberar_registro_temporal(reg_lhs)
                self._liberar_registro_temporal(reg_rhs)
                return None, None

            # No liberar reg_rhs si ya se liberó específicamente (ej. conversión int a float)
            # if reg_rhs.startswith("$t") and not (tipo_resultado == 'float' and tipo_rhs == 'int'): self._liberar_registro_temporal(reg_rhs)
            return self._visitar_f_rest(nodo_f_rest.children[2], reg_final_lhs, tipo_resultado)
        return reg_lhs, tipo_lhs

    def _visitar_a(self, nodo_a):
        # ... (resto del método _visitar_a sin cambios desde la última versión)
        # A -> ID | INT_NUM | FLOAT_NUM | STRING_LITERAL | TRUE | FALSE | LPAREN exp RPAREN | ID llamada_func
        # Devuelve (registro_con_valor, tipo_string_del_valor)
        primer_hijo_de_a = nodo_a.children[0]
        valor_primer_hijo = primer_hijo_de_a.value

        # Caso 1: Literal INT_NUM
        if isinstance(valor_primer_hijo, int):
            reg_dest = self._obtener_registro_temporal()
            self.codigo_text.append(f"  li {reg_dest}, {valor_primer_hijo}  # Cargar entero literal {valor_primer_hijo}")
            return reg_dest, "int"

        # Caso 2: Literal FLOAT_NUM
        if isinstance(valor_primer_hijo, float):
            etiqueta_float = self._nueva_etiqueta("L_float_lit_")
            self.codigo_data.append(f"  {etiqueta_float}: .float {float(valor_primer_hijo):.6f}  # Literal float {valor_primer_hijo}")
            reg_f_dest = self._obtener_registro_flotante_temporal()
            self.codigo_text.append(f"  l.s {reg_f_dest}, {etiqueta_float} # Cargar float literal a {reg_f_dest}")
            return reg_f_dest, "float"

        # Caso 3: Literales TRUE / FALSE
        if valor_primer_hijo == "true":
            reg_dest = self._obtener_registro_temporal()
            self.codigo_text.append(f"  li {reg_dest}, 1  # Cargar literal true (1)")
            return reg_dest, "bool"
        if valor_primer_hijo == "false":
            reg_dest = self._obtener_registro_temporal()
            self.codigo_text.append(f"  li {reg_dest}, 0  # Cargar literal false (0)")
            return reg_dest, "bool"

        # Caso 4: Literal STRING_LITERAL
        simbolo_info_lookup = self.tabla_simbolos.lookup_symbol(str(valor_primer_hijo), self.funcion_actual_nombre)
        if isinstance(valor_primer_hijo, str) and \
           valor_primer_hijo not in ["true", "false", "LPAREN"] and \
           simbolo_info_lookup is None:
            contenido_str = valor_primer_hijo
            if contenido_str.startswith('"') and contenido_str.endswith('"'):
                contenido_str = contenido_str[1:-1]
            etiqueta_str = self._nueva_etiqueta("L_str_")
            self.codigo_data.append(f"  {etiqueta_str}: .asciiz \"{contenido_str}\" # Literal string")
            reg_dest = self._obtener_registro_temporal()
            self.codigo_text.append(f"  la {reg_dest}, {etiqueta_str}  # Cargar dirección de string literal")
            return reg_dest, "string"

        # Caso 5: Paréntesis LPAREN exp RPAREN
        if valor_primer_hijo == 'LPAREN':
            if len(nodo_a.children) == 3 and nodo_a.children[1].value == 'exp':
                self.codigo_text.append(f"  # Inicio expresión entre paréntesis")
                reg_exp, tipo_exp = self._visitar(nodo_a.children[1])
                self.codigo_text.append(f"  # Fin expresión entre paréntesis, resultado en {reg_exp}")
                return reg_exp, tipo_exp
            else:
                print("Error: Estructura de paréntesis (A -> LPAREN exp RPAREN) mal formada.")
                return None, None

        # Caso 6: Identificador (variable) o Llamada a función
        nombre_id_o_func = str(valor_primer_hijo)
        simbolo_info = self.tabla_simbolos.lookup_symbol(nombre_id_o_func, self.funcion_actual_nombre)

        if not simbolo_info:
            print(f"Error CRÍTICO de generación: Símbolo '{nombre_id_o_func}' no encontrado en _visitar_a.")
            return None, None

        tipo_simbolo = simbolo_info['type']

        is_syntactic_call = False
        if len(nodo_a.children) > 1 and nodo_a.children[1].value == 'llamada_func':
            # Es una estructura A -> ID llamada_func.
            # Ahora, hay que verificar si llamada_func es una llamada real o la producción epsilon.
            # Una llamada_func real no tendrá 'ε' como su (único) hijo.
            # Típicamente, tendrá LPAREN, lista_args, RPAREN.
            # Si llamada_func -> ε, entonces nodo_a.children[1].children[0].value == 'ε'.
            llamada_func_node_candidate = nodo_a.children[1]
            if not (len(llamada_func_node_candidate.children) == 1 and llamada_func_node_candidate.children[0].value == 'ε'):
                is_syntactic_call = True

        if is_syntactic_call:
            # Ahora estamos seguros de que es una llamada a función real.
            if not tipo_simbolo.startswith("FUNCTION"):
                # Esto sería un error grave si la tabla de símbolos y el AST están desincronizados
                # o si un no-función tiene una estructura de llamada no-epsilon.
                print(f"Error CRÍTICO: '{nombre_id_o_func}' (tipo: {tipo_simbolo}) tiene estructura de llamada pero no es FUNCTION.")
                return None, None

            # primer_hijo_de_a es el nodo ID de la función.
            # nodo_a.children[1] es el nodo 'llamada_func' directamente.
            llamada_func_node = nodo_a.children[1]
            tipo_retorno_str = tipo_simbolo.split(' -> ')[-1].lower()
            self.codigo_text.append(f"  # Inicio llamada a función '{nombre_id_o_func}'")
            reg_retorno = self._visitar_llamada_func_como_expresion(primer_hijo_de_a, llamada_func_node)
            self.codigo_text.append(f"  # Fin llamada a función '{nombre_id_o_func}', retorno en {reg_retorno}")
            return reg_retorno, tipo_retorno_str
        else:
            # Esto se ejecuta si no es una llamada sintáctica (es una variable, o un ID de función sin '()')
            # O si el ID es un parámetro/variable que casualmente tiene un nodo 'llamada_func' con epsilon debajo (caso de 'x' en el AST)
            a_prime_node_for_var_check = nodo_a.children[1] if len(nodo_a.children) > 1 else None
            is_actually_var_despite_a_prime = True
            if a_prime_node_for_var_check and a_prime_node_for_var_check.value == 'llamada_func':
                # Si a_prime es llamada_func, pero sus hijos son epsilon (ej. para variable 'x'), entonces no es una llamada real.
                if not (len(a_prime_node_for_var_check.children) == 1 and a_prime_node_for_var_check.children[0].value == 'ε'):
                    # Esto sería una llamada_func con argumentos no vacíos, lo que contradiría is_syntactic_call = False
                    # Es un caso que no debería ocurrir si la lógica de is_syntactic_call es correcta.
                     print(f"ADVERTENCIA: Confusión en _visitar_a para {nombre_id_o_func}. Tratando como variable.")


            if tipo_simbolo.startswith("FUNCTION") and is_actually_var_despite_a_prime:
                 # Solo imprimir error si es una FUNCION y no se identificó como llamada sintáctica
                 # Y además, si a_prime no es una llamada_func vacía (que es normal para variables)
                 if not (a_prime_node_for_var_check and \
                         a_prime_node_for_var_check.value == 'llamada_func' and \
                         len(a_prime_node_for_var_check.children) == 1 and \
                         a_prime_node_for_var_check.children[0].value == 'ε'):
                    print(f"Error SEMÁNTICO (debería ser del analizador): Func. '{nombre_id_o_func}' usada como variable.")
                    return None, None

            reg_dest = None
            tipo_var_lower = tipo_simbolo.lower()
            offset = self._obtener_offset_variable(nombre_id_o_func)
            load_instr = "lw"
            comment_suffix = f"variable '{nombre_id_o_func}'"

            if tipo_var_lower == 'float':
                load_instr = "l.s"
                reg_dest = self._obtener_registro_flotante_temporal()
            else:
                reg_dest = self._obtener_registro_temporal()

            if offset is not None:
                self.codigo_text.append(f"  {load_instr} {reg_dest}, {offset}($fp)  # Cargar local/param {comment_suffix}")
            elif simbolo_info['scope_attr'] == 'global':
                if tipo_var_lower == 'string':
                     self.codigo_text.append(f"  la {reg_dest}, {nombre_id_o_func}  # Cargar dirección de string global {comment_suffix}")
                else:
                    self.codigo_text.append(f"  {load_instr} {reg_dest}, {nombre_id_o_func}   # Cargar global {comment_suffix}")
            else:
                print(f"Error CRÍTICO: Variable '{nombre_id_o_func}' sin ubicación de carga en _visitar_a.")
                if reg_dest: self._liberar_registro_temporal(reg_dest)
                return None, None

            return reg_dest, tipo_var_lower

        print(f"Advertencia: Nodo A con hijo '{valor_primer_hijo}' no manejado (final de _visitar_a).")
        return None, None

    def _visitar_llamada_func_como_expresion(self, id_func_node, llamada_func_node):
        # ... (lógica de llamada a función con mejoras en comentarios y liberación de registros de args)
        nombre_funcion = id_func_node.value
        info_funcion_ts = self.tabla_simbolos.lookup_symbol(nombre_funcion, "global")

        if not info_funcion_ts or not info_funcion_ts['type'].startswith("FUNCTION"):
            print(f"Error CRÍTICO: Llamando a '{nombre_funcion}' que no es función.")
            return None

        tipo_retorno_func = info_funcion_ts['type'].split(' -> ')[-1].lower()

        lista_args_node = llamada_func_node.children[1]
        registros_args_info = []

        current_arg_list_part = lista_args_node
        arg_num = 0
        while current_arg_list_part and current_arg_list_part.children and current_arg_list_part.children[0].value != 'ε':
            arg_num +=1
            exp_arg_node = None
            next_arg_list_part = None
            if current_arg_list_part.value == 'lista_args':
                exp_arg_node = current_arg_list_part.children[0]
                next_arg_list_part = current_arg_list_part.children[1]
            elif current_arg_list_part.value == 'lista_args_rest':
                exp_arg_node = current_arg_list_part.children[1]
                next_arg_list_part = current_arg_list_part.children[2]
            else: break

            if exp_arg_node:
                self.codigo_text.append(f"    # Evaluando argumento {arg_num} para '{nombre_funcion}'")
                reg_arg, tipo_arg = self._visitar(exp_arg_node)
                if reg_arg:
                    registros_args_info.append({'reg': reg_arg, 'type': tipo_arg, 'num': arg_num})
                else:
                    print(f"Error: No se pudo evaluar argumento {arg_num} para {nombre_funcion}")
                    for arg_info_err in registros_args_info: # Liberar los ya evaluados
                        self._liberar_registro_temporal(arg_info_err['reg'])
                    return None
            current_arg_list_part = next_arg_list_part

        # Pasar argumentos a registros $aX o $fX
        cpu_arg_idx = 0
        fpu_arg_idx = 0
        self.codigo_text.append(f"    # Pasando argumentos a '{nombre_funcion}'")
        for arg_info in registros_args_info:
            reg_arg_val = arg_info['reg']
            tipo_arg_val = arg_info['type']
            arg_n = arg_info['num']
            if tipo_arg_val == 'float':
                if fpu_arg_idx == 0:
                    self.codigo_text.append(f"  mov.s $f12, {reg_arg_val}  # Pasar arg float {arg_n} ({reg_arg_val}) a $f12")
                    fpu_arg_idx +=1
                else: print(f"Advertencia: Pasar más de 1 arg float por registro no implementado para '{nombre_funcion}'.")
            else:
                if cpu_arg_idx < 4:
                    self.codigo_text.append(f"  move $a{cpu_arg_idx}, {reg_arg_val}  # Pasar arg {arg_n} ({reg_arg_val}) a $a{cpu_arg_idx}")
                    cpu_arg_idx += 1
                else: print(f"Advertencia: Pasar más de 4 args CPU por registro no implementado para '{nombre_funcion}'.")

        # Liberar registros temporales de argumentos DESPUÉS de pasarlos
        for arg_info in registros_args_info:
            self._liberar_registro_temporal(arg_info['reg'])

        self.codigo_text.append(f"  jal {nombre_funcion}      # Llamar a la función '{nombre_funcion}'")

        reg_final_retorno = None
        if tipo_retorno_func != "void":
            if tipo_retorno_func == "float": # Resultado en $f0
                reg_final_retorno = self._obtener_registro_flotante_temporal()
                self.codigo_text.append(f"  mov.s {reg_final_retorno}, $f0 # Mover resultado float de '{nombre_funcion}' desde $f0")
            else: # Resultado en $v0
                reg_final_retorno = self._obtener_registro_temporal()
                self.codigo_text.append(f"  move {reg_final_retorno}, $v0 # Mover resultado de '{nombre_funcion}' desde $v0")

        return reg_final_retorno

    # --- Visitors para Estructuras de Control ---

    def _visitar_if(self, nodo_if):
        # Estructura esperada del AST para If:
        # nodo_if.value == 'If'
        # nodo_if.children[0] == IF_KW
        # nodo_if.children[1] == LPAREN
        # nodo_if.children[2] == exp (condición)
        # nodo_if.children[3] == RPAREN
        # nodo_if.children[4] == LBRACE
        # nodo_if.children[5] == bloque (rama then)
        # nodo_if.children[6] == RBRACE
        # nodo_if.children[7] == Else (nodo Else)

        self.codigo_text.append(f"\n  # Inicio IF en línea {nodo_if.lineno}")

        cond_exp_node = nodo_if.children[2]
        reg_cond, tipo_cond = self._visitar(cond_exp_node)

        if reg_cond is None or tipo_cond != 'bool':
            print(f"Error: La condición del IF en línea {nodo_if.lineno} no evaluó a un booleano o falló.")
            # Podríamos intentar recuperar o simplemente generar código potencialmente incorrecto/incompleto.
            # Por ahora, si la condición falla, no generamos el cuerpo del if/else.
            self._liberar_registro_temporal(reg_cond) # Liberar si se obtuvo algo
            self.codigo_text.append(f"  # ERROR: Condición de IF fallida en línea {nodo_if.lineno}")
            return

        etiqueta_else = self._nueva_etiqueta("L_else_")
        etiqueta_endif = self._nueva_etiqueta("L_endif_")

        # Si la condición (en reg_cond) es 0 (false), saltar a la etiqueta_else.
        # Si no hay bloque else, etiqueta_else será la misma que etiqueta_endif.

        nodo_else_interno = nodo_if.children[7] # Este es el nodo 'Else'
        tiene_rama_else = nodo_else_interno.children and nodo_else_interno.children[0].value != 'ε'

        etiqueta_salto_condicion_falsa = etiqueta_else if tiene_rama_else else etiqueta_endif

        self.codigo_text.append(f"  beq {reg_cond}, $zero, {etiqueta_salto_condicion_falsa}  # Salta si la condición es falsa (0)")
        self._liberar_registro_temporal(reg_cond) # El registro de condición ya no se necesita

        # Rama THEN (bloque del if)
        self.codigo_text.append(f"  # Rama THEN del IF en línea {nodo_if.lineno}")
        bloque_then_node = nodo_if.children[5]
        self._visitar(bloque_then_node)

        if tiene_rama_else:
            self.codigo_text.append(f"  j {etiqueta_endif}          # Salto incondicional al final del IF desde la rama THEN")
            self.codigo_text.append(f"{etiqueta_else}:  # Etiqueta para la rama ELSE")
            # El nodo Else tiene hijos: [ELSE_KW, LBRACE, bloque_else, RBRACE]
            # El bloque del else está en nodo_else_interno.children[2]
            bloque_else_node = nodo_else_interno.children[2]
            self.codigo_text.append(f"  # Rama ELSE del IF en línea {nodo_if.lineno}")
            self._visitar(bloque_else_node)
        # Si no tiene rama else, la etiqueta_else no se usa o es la misma que endif,
        # y el beq saltó directamente a endif.

        self.codigo_text.append(f"{etiqueta_endif}:  # Etiqueta final del IF-ELSE")
        self.codigo_text.append(f"  # Fin IF en línea {nodo_if.lineno}")

    # _visitar_else no es estrictamente necesario como un visitor de nodo separado si _visitar_if
    # maneja la lógica de visitar el bloque del else directamente.
    # El nodo 'Else' en sí mismo es más una construcción gramatical.
    # Lo mantenemos por si se necesita una lógica más compleja para 'Else' en el futuro.
    def _visitar_else(self, nodo_else_rule):
        # Este método sería llamado si el AST tuviera un nodo 'Else' que necesitara ser visitado
        # independientemente. Pero _visitar_if ya maneja la visita a su bloque interno.
        # Si se llama, es probable que sea a través de un _visitar_generico si no se maneja
        # explícitamente en el padre (como _visitar_if lo hace).
        # Por ahora, si se visita un nodo 'Else' directamente, solo visitamos a sus hijos.
        # self.codigo_text.append(f"  # Visitando nodo Else (inesperado directamente)")
        # self._visitar_generico(nodo_else_rule)
        pass # La lógica está en _visitar_if

    def _visitar_while(self, nodo_while):
        # Estructura esperada del AST para While:
        # nodo_while.value == 'While'
        # nodo_while.children[0] == WHILE_KW
        # nodo_while.children[1] == LPAREN
        # nodo_while.children[2] == exp (condición)
        # nodo_while.children[3] == RPAREN
        # nodo_while.children[4] == LBRACE
        # nodo_while.children[5] == bloque (cuerpo del bucle)
        # nodo_while.children[6] == RBRACE

        self.codigo_text.append(f"\n  # Inicio WHILE en línea {nodo_while.lineno}")

        etiqueta_loop_start = self._nueva_etiqueta("L_loop_start_")
        etiqueta_loop_end = self._nueva_etiqueta("L_loop_end_")

        self.codigo_text.append(f"{etiqueta_loop_start}:  # Etiqueta de inicio/condición del while")

        # Evaluar la condición
        cond_exp_node = nodo_while.children[2]
        self.codigo_text.append(f"  # Evaluando condición del WHILE en línea {cond_exp_node.lineno}")
        reg_cond, tipo_cond = self._visitar(cond_exp_node)

        if reg_cond is None or tipo_cond != 'bool':
            print(f"Error: La condición del WHILE en línea {nodo_while.lineno} no evaluó a un booleano o falló.")
            self._liberar_registro_temporal(reg_cond)
            self.codigo_text.append(f"  # ERROR: Condición de WHILE fallida, posible bucle infinito o no ejecución.")
            # Para evitar un bucle infinito si la condición falla, podríamos saltar a loop_end
            self.codigo_text.append(f"  j {etiqueta_loop_end} # Salto de emergencia por condición fallida")
        else:
            self.codigo_text.append(f"  beq {reg_cond}, $zero, {etiqueta_loop_end}  # Salta a loop_end si la condición es falsa (0)")
            self._liberar_registro_temporal(reg_cond) # El registro de condición ya no se necesita para esta iteración

        # Cuerpo del bucle
        self.codigo_text.append(f"  # Cuerpo del WHILE en línea {nodo_while.lineno}")
        bloque_cuerpo_node = nodo_while.children[5]
        self._visitar(bloque_cuerpo_node)

        self.codigo_text.append(f"  j {etiqueta_loop_start}      # Volver al inicio del bucle para re-evaluar condición")
        self.codigo_text.append(f"{etiqueta_loop_end}:  # Etiqueta final del WHILE")
        self.codigo_text.append(f"  # Fin WHILE en línea {nodo_while.lineno}")


