from TablaSimbolos import SymbolTable
TYPE_ERROR = "TypeError"

class SemanticAnalyzer:
    def __init__(self, ast_root):
        self.ast_root = ast_root
        self.symbol_table = SymbolTable()
        self.current_function_name = None
        self.current_function_return_type = None 

    def analyze(self):
        if self.ast_root:
            self._visit(self.ast_root)
        else:
            self.symbol_table.add_error("Error semántico: No se proporcionó un árbol sintáctico para analizar.")
            return TYPE_ERROR

    def _visit(self, node):
        if not node: # Should not happen with a well-formed AST
            return TYPE_ERROR # Or some other indicator of an issue

        method_name = f'_visit_{node.value.lower().replace("(", "_lparen_").replace(")", "_rparen_")}' # Sanitize node names for methods
        visitor = getattr(self, method_name, self._generic_visit)

        #print(f"Visiting: {node.value}, Method: {visitor.__name__}") # For debugging traversal

        return visitor(node)

    def _get_node_type_str(self, tipo_node):
        if tipo_node and tipo_node.value == 'tipo' and tipo_node.children:
            type_keyword_node = tipo_node.children[0]
            type_mapping = {
                'INT': 'int',
                'FLOAT': 'float',
                'BOOL': 'bool',
                'STRING': 'string', # This should match the token type from lexer for "string" keyword
                'VOID': 'void'
            }
            # print(f"DEBUG _get_node_type_str: looking for '{type_keyword_node.value}' in mapping. Result: {type_mapping.get(type_keyword_node.value, 'UnknownType')}")
            return type_mapping.get(type_keyword_node.value, "UnknownType")
        return "UnknownType"


    def _generic_visit(self, node):
        #print(f"Generic visit for node: {node.value} with {len(node.children)} children") # Debug
        last_type = None
        
        for child in node.children:
            last_type = self._visit(child)
            if last_type == TYPE_ERROR: # Propagate error
                return TYPE_ERROR
        return last_type # Or simply None if no meaningful type from generic visit

    # Visitor methods for common top-level grammar rules

    def _visit_programa(self, node):
        #print(f"Visiting programa node: {node.value}") # Debug
        return self._generic_visit(node)
    
    def _visit_funciones(self, node):
        #print(f"Visiting funciones node: {node.value}") # Debug
        return self._generic_visit(node) 

    def _visit_funcion(self, node):
        if not node.children or not all(c for c in node.children):
            return TYPE_ERROR
        
        print("NODO ACTUAL: ",node.value)
        print("HIJOS: ")
        for i in node.children:
            print(" -> ",i.value)

        # funcion -> tipo ID funcion_rest
        if len(node.children) == 3 and \
           node.children[0] and node.children[0].value == 'tipo' and \
           node.children[1] and \
           node.children[2] and node.children[2].value == 'funcion_rest':

            funcion_rest_node = node.children[2]
            # funcion_rest -> inicializacion SEMI
            if funcion_rest_node and len(funcion_rest_node.children) == 2 and \
               funcion_rest_node.children[0] and funcion_rest_node.children[0].value == 'inicializacion' and \
               funcion_rest_node.children[1] and funcion_rest_node.children[1].value == 'SEMI':

                tipo_node = node.children[0] # tipo
                id_node = node.children[1] # ID
                inicializacion_node = funcion_rest_node.children[0] # inicializacion

                declared_type_str = self._get_node_type_str(tipo_node) # tipo de variable
                var_name = id_node.value # valor del ID
                var_lineno = id_node.lineno # linea ubicada

                # Add to symbol table first
                self.symbol_table.add_symbol(var_name, declared_type_str, var_lineno, 'global', param_types=None)

                # Then check initialization if present
                if inicializacion_node.children and inicializacion_node.children[0].value != 'ε':
                    # inicializacion -> EQUALS exp
                    if len(inicializacion_node.children) == 2 and inicializacion_node.children[0].value == 'EQUALS':
                        exp_node = inicializacion_node.children[1] # exp
                        exp_type = self._visit(exp_node) # 
                        if exp_type != TYPE_ERROR:
                            self._check_assignment_compatibility(declared_type_str, exp_type, var_lineno, var_name)
                return # Done with global var

        # MAIN function: MAIN LPAREN RPAREN LBRACE bloque RBRACE
        if len(node.children) == 6 and \
           node.children[0] and node.children[0].value == 'MAIN' and \
           node.children[1] and node.children[1].value == 'LPAREN' and \
           node.children[2] and node.children[2].value == 'RPAREN' and \
           node.children[3] and node.children[3].value == 'LBRACE'and \
           node.children[4] and node.children[4].value == 'bloque' and \
           node.children[5] and node.children[5].value == 'RBRACE':

            func_name = "main"
            func_lineno = node.children[0].lineno
            func_return_type = "void" # Main typically returns void or int, let's use void

            # Add main function symbol (type includes return type and empty param list)
            self.symbol_table.add_symbol(func_name, f"FUNCTION () -> {func_return_type.upper()}", func_lineno, "global", param_types=[])

            self.current_function_name = func_name
            self.current_function_return_type = func_return_type
            self.symbol_table.enter_scope(func_name)

            self._visit(node.children[4]) # bloque

            self.symbol_table.exit_scope()
            self.current_function_name = None
            self.current_function_return_type = None
            return # Done with main

        # Regular function definition: tipo ID funcion_rest (where funcion_rest is LPAREN parametros RPAREN bloque)
        if len(node.children) == 3 and \
           node.children[0] and node.children[0].value == 'tipo' and \
           node.children[1] and \
           node.children[2] and node.children[2].value == 'funcion_rest':

            funcion_rest_node = node.children[2]
            #funcion_rest_node -> LPAREN parametros RPAREN LBRACE bloque RBRACE
            if funcion_rest_node and len(funcion_rest_node.children) == 6 and \
               funcion_rest_node.children[0] and funcion_rest_node.children[0].value == 'LPAREN' and \
               funcion_rest_node.children[1] and funcion_rest_node.children[1].value == 'parametros' and \
               funcion_rest_node.children[2] and funcion_rest_node.children[2].value == 'RPAREN' and \
               funcion_rest_node.children[3] and funcion_rest_node.children[3].value == 'LBRACE'and \
               funcion_rest_node.children[4] and funcion_rest_node.children[4].value == 'bloque' and \
               funcion_rest_node.children[5] and funcion_rest_node.children[5].value == 'RBRACE':

                tipo_node_for_func = node.children[0] # tipo
                id_node = node.children[1] # ID
                func_name = id_node.value # valor de ID
                func_lineno = id_node.lineno # linea asignada
                func_return_type = self._get_node_type_str(tipo_node_for_func) 

                # Collect parameter types and names
                param_info = self._collect_param_info(funcion_rest_node.children[1]) # visit parametros
                if param_info == TYPE_ERROR: return TYPE_ERROR

                param_types = param_info['types']
                param_names_ordered = param_info['names']

                # Add function symbol (type includes return type and param types)
                param_types_str = ", ".join(param_types).upper() if param_types else ""
                self.symbol_table.add_symbol(
                    func_name,
                    f"FUNCTION ({param_types_str}) -> {func_return_type.upper()}",
                    func_lineno,
                    "global",
                    param_types=param_types,
                    param_names_ordered=param_names_ordered # Store ordered names
                )

                self.current_function_name = func_name
                self.current_function_return_type = func_return_type
                self.symbol_table.enter_scope(func_name)

                self._visit(funcion_rest_node.children[1]) # Re-visit parametros to add them to scope
                self._visit(funcion_rest_node.children[4]) # bloque

                self.symbol_table.exit_scope()
                self.current_function_name = None
                self.current_function_return_type = None
                return 

        return self._generic_visit(node) 

    def _collect_param_info(self, parametros_node):
        types = []
        names = []

        # 'parametros' -> 'parametro' 'parametros_rest' | epsilon
        # 'parametros_rest' -> COMMA 'parametro' 'parametros_rest' | epsilon
        # parametro -> tipo ID
        node_iter = parametros_node # Initially Node('parametros')
        while node_iter and node_iter.children and node_iter.children[0].value != 'ε':
            param_node_to_process = None
            next_iter_node = None

            if node_iter.value == 'parametros':
                # Children: [Node('parametro'), Node('parametros_rest')]
                if len(node_iter.children) == 2:
                    param_node_to_process = node_iter.children[0] # Node(parametro)
                    next_iter_node = node_iter.children[1] # Node('parametros_rest')
                else:
                    break
            elif node_iter.value == 'parametros_rest':
                # Children: [Node('COMMA'), Node('parametro'), Node('parametros_rest')]
                if len(node_iter.children) == 3:
                    param_node_to_process = node_iter.children[1] # Node(parametro)
                    next_iter_node = node_iter.children[2] # Node('parametros_rest')
                else: 
                    break
            else: # nunca deberia de pasar 
                self.symbol_table.add_error(f"Error Interno: Nodo inesperado '{node_iter.value}' en _collect_param_types.")
                return TYPE_ERROR

            if param_node_to_process and hasattr(param_node_to_process, 'value') and param_node_to_process.value == 'parametro' and \
               hasattr(param_node_to_process, 'children') and param_node_to_process.children and len(param_node_to_process.children) == 2:
                # parametro -> tipo ID
                tipo_node = param_node_to_process.children[0] # alamcena tipo
                id_node = param_node_to_process.children[1] # This is the ID node
                types.append(self._get_node_type_str(tipo_node))
                names.append(id_node.value) # Store the name
            else:
                err_lineno = -1
                if param_node_to_process and hasattr(param_node_to_process, 'lineno'):
                    err_lineno = param_node_to_process.lineno
                elif node_iter and hasattr(node_iter, 'lineno'):
                    err_lineno = node_iter.lineno
                self.symbol_table.add_error(f"Error semántico [línea {err_lineno}]: Estructura de parámetro inválida procesando '{param_node_to_process.value if param_node_to_process and hasattr(param_node_to_process, 'value') else 'Node?'}'.")
                return TYPE_ERROR

            node_iter = next_iter_node
            if not node_iter:
                break
        return {'types': types, 'names': names}


    def _visit_parametros(self, node):
        node_iter = node

        while node_iter and node_iter.children and node_iter.children[0].value != 'ε':
            param_node_to_visit = None
            next_iter_node = None

            if node_iter.value == 'parametros':
                if len(node_iter.children) == 2:
                    param_node_to_visit = node_iter.children[0]
                    next_iter_node = node_iter.children[1]
                else: break
            elif node_iter.value == 'parametros_rest':
                if len(node_iter.children) == 3:
                    param_node_to_visit = node_iter.children[1]
                    next_iter_node = node_iter.children[2]
                else: break
            else:
                self.symbol_table.add_error(f"Error Interno: Nodo inesperado '{node_iter.value}' en _visit_parametros.")
                return TYPE_ERROR

            if param_node_to_visit and param_node_to_visit.value == 'parametro':
                if self._visit(param_node_to_visit) == TYPE_ERROR: # This calls _visit_parametro
                    return TYPE_ERROR
            else: # Should be a 'parametro' node
                err_lineno = param_node_to_visit.lineno if param_node_to_visit and hasattr(param_node_to_visit, 'lineno') else node_iter.lineno
                self.symbol_table.add_error(f"Error semántico [línea {err_lineno}]: Se esperaba un nodo 'parametro'.")
                return TYPE_ERROR

            node_iter = next_iter_node
            if not node_iter: break

        return None 

    def _visit_parametros_rest(self, node):
        # This node is handled by the iteration logic in _visit_parametros.
        # If called directly, it means something is off, or it's just part of a traversal.
        # For type collection/adding symbols, it's part of the list traversal logic.
        # A direct visit here doesn't contribute a type for an expression.
        return None


    def _visit_parametro(self, node):
        # Children: [Node('tipo'), Node_with_lexeme_as_value (ID)]
        tipo_node_in_param = node.children[0] if node.children else None
        id_node_in_param = node.children[1] if node.children and len(node.children) > 1 else None
        #print(f"DEBUG _visit_parametro: ID='{id_node_in_param.value if id_node_in_param else 'N/A'}', TipoNode='{tipo_node_in_param.value if tipo_node_in_param else 'N/A'}'")
        if tipo_node_in_param and tipo_node_in_param.children:
            print(" ")
            #print(f"  DEBUG _visit_parametro: TipoNode child='{tipo_node_in_param.children[0].value}'")
        # print(f"DEBUG: _visit_parametro: node.value='{node.value if hasattr(node, 'value') else 'N/A'}' (type: {type(node).__name__}), node.lineno={node.lineno if hasattr(node, 'lineno') else 'N/A'}, num_children={len(node.children) if node.children else 'None'}")
        # if node.children:
        #     for i, child in enumerate(node.children):
        #         print(f"  Child {i}: value='{child.value if hasattr(child, 'value') else 'N/A'}' (type: {type(child).__name__}), lineno={child.lineno if hasattr(child, 'lineno') else 'N/A'}")
        # else:
        #     print("  _visit_parametro: Node has no children.")

        if node.children and len(node.children) == 2 and \
           node.children[0] and node.children[0].value == 'tipo' and \
           node.children[1]:

            tipo_node = node.children[0]
            id_node = node.children[1]

            type_str = self._get_node_type_str(tipo_node)
            param_name = id_node.value
            param_lineno = id_node.lineno

            if self.current_function_name:
                self.symbol_table.add_symbol(param_name, type_str, param_lineno, self.current_function_name, param_types=None)
                return type_str # Return the type of the parameter
            else:
                self.symbol_table.add_error(f"Error Interno [línea {param_lineno}]: Parámetro '{param_name}' declarado fuera del contexto de una función.")
                return TYPE_ERROR
        else:
            param_node_line = node.lineno if node else -1
            self.symbol_table.add_error(f"Error semántico [línea {param_node_line}]: Estructura de parámetro inválida.")
            return TYPE_ERROR


    def _visit_bloque(self, node):
        # Children: [Node('LBRACE'), Node('instrucciones'), Node('RBRACE')]
        if len(node.children) == 1 and \
           node.children[0] and node.children[0].value == 'instrucciones':

            return self._visit(node.children[0]) # Visit instrucciones
        else:
            # self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de bloque inválida.")
            return self._generic_visit(node)

    def _visit_instrucciones(self, node):
        if node.children and node.children[0].value != 'ε':
            # Has 'instruccion' and 'instrucciones'
            if len(node.children) > 0:
                 res_type = self._visit(node.children[0]) # Visit instruccion
                 if res_type == TYPE_ERROR: return TYPE_ERROR
            if len(node.children) > 1:
                 res_type_rest = self._visit(node.children[1]) # Visit next instrucciones
                 if res_type_rest == TYPE_ERROR: return TYPE_ERROR
        return None # Instructions don't have a collective type

    def _visit_instruccion(self, node):
        if not node.children or len(node.children) == 0:
            return None # Or TYPE_ERROR if this is considered an AST error

        first_child_of_instruccion = node.children[0]

        # Heuristic for ID-led assignment/call (instruccion -> ID id_rhs_instruccion)
        # This assumes ID lexemes don't clash with keywords like 'declaracion', 'If', etc.
        is_id_first_child = first_child_of_instruccion.value not in [
            'declaracion', 'If', 'While', 'For', 'Return', 'Print', 'bloque'
        ]

        if is_id_first_child and len(node.children) > 1: # 'ID id_rhs_instruccion'
            id_node_lhs = first_child_of_instruccion
            id_rhs_node = node.children[1] # Node('id_rhs_instruccion')

            if id_rhs_node and id_rhs_node.value == 'id_rhs_instruccion' and id_rhs_node.children:
                type_of_rhs_production = id_rhs_node.children[0].value # EQUALS or llamada_func

                if type_of_rhs_production == 'EQUALS': # Assignment: ID EQUALS exp SEMI
                    var_name = id_node_lhs.value
                    var_lineno = id_node_lhs.lineno

                    symbol = self.symbol_table.lookup_symbol(var_name)
                    if symbol is None:
                        self.symbol_table.add_error(
                            f"Error semántico [línea {var_lineno}]: La variable '{var_name}' no ha sido declarada."
                        )
                        return TYPE_ERROR

                    declared_type = symbol['type']
                    if declared_type.startswith("FUNCTION"): # Cannot assign to a function name
                        self.symbol_table.add_error(f"Error semántico [línea {var_lineno}]: No se puede asignar a una función '{var_name}'.")
                        return TYPE_ERROR

                    if len(id_rhs_node.children) > 1 and id_rhs_node.children[1].value == 'exp':
                        exp_node = id_rhs_node.children[1]
                        exp_type = self._visit(exp_node)
                        if exp_type == TYPE_ERROR:
                            return TYPE_ERROR

                        self._check_assignment_compatibility(declared_type, exp_type, var_lineno, var_name)
                    else: # Malformed assignment
                        self.symbol_table.add_error(f"Error semántico [línea {var_lineno}]: Asignación mal formada para '{var_name}'.")
                        return TYPE_ERROR
                    return None # Assignment statement has no type

                elif type_of_rhs_production == 'llamada_func': # Function Call Statement: ID llamada_func SEMI
                    # The ID is the function name, llamada_func node contains args
                    # Type checking for call is handled by _visit_a (when ID llamada_func is an expression)
                    # or here if it's a statement. _visit_a should return the function's return type.
                    # For a statement, we just care about arg compatibility, return type is discarded.
                    # We can re-use part of _visit_a's logic for ID + llamada_func.

                    # Simulate the structure for _visit_a for the call part:
                    # Create a temporary 'A' like node: A -> ID llamada_func
                    # This is a bit of a hack. Ideally, `llamada_func` visitor would handle this with context.
                    temp_a_node_for_call = type('Node', (), {
                        'value': 'A_temp_for_call', # Dummy value
                        'children': [id_node_lhs, id_rhs_node.children[0]], # ID, llamada_func_node
                        'lineno': id_node_lhs.lineno
                    })
                    call_type = self._visit_a(temp_a_node_for_call) # Will perform arg checks
                    if call_type == TYPE_ERROR:
                        return TYPE_ERROR
                    return None # Function call statement has no type
                else:
                    return self._generic_visit(id_rhs_node) # Fallback
            else:
                return self._generic_visit(node) # Fallback
        else: # Standard instruction like declaracion, If, Print etc.
            return self._visit(first_child_of_instruccion)


    def _visit_declaracion(self, node):
        # declaracion -> tipo ID inicializacion
        tipo_node_in_decl = node.children[0] if node.children else None
        id_node_in_decl = node.children[1] if node.children and len(node.children) > 1 else None
        #print(f"DEBUG _visit_declaracion: ID='{id_node_in_decl.value if id_node_in_decl else 'N/A'}', TipoNode='{tipo_node_in_decl.value if tipo_node_in_decl else 'N/A'}'")
        if tipo_node_in_decl and tipo_node_in_decl.children:
            print(" ")
            #print(f"  DEBUG _visit_declaracion: TipoNode child='{tipo_node_in_decl.children[0].value}'")


        if node.children and len(node.children) == 3 and \
            node.children[0] and node.children[0].value == 'tipo' and \
           node.children[1] and \
           node.children[2] and node.children[2].value == 'inicializacion':

            tipo_node = node.children[0]
            id_node = node.children[1]
            inicializacion_node = node.children[2]

            declared_type_str = self._get_node_type_str(tipo_node)
            var_name = id_node.value
            var_lineno = id_node.lineno

            scope_name = self.current_function_name if self.current_function_name else 'global'
            self.symbol_table.add_symbol(var_name, declared_type_str, var_lineno, scope_name, param_types=None)

            # Check initialization if present
            # inicializacion -> EQUALS exp | ε
            if inicializacion_node.children and inicializacion_node.children[0].value != 'ε':
                # Must be EQUALS exp
                if len(inicializacion_node.children) == 2 and inicializacion_node.children[0].value == 'EQUALS':
                    exp_node = inicializacion_node.children[1]
                    exp_type = self._visit(exp_node)

                    if exp_type != TYPE_ERROR:
                        self._check_assignment_compatibility(declared_type_str, exp_type, var_lineno, var_name)
                    else:
                        return TYPE_ERROR # Error from expression
                else: # Malformed initialization
                    self.symbol_table.add_error(f"Error semántico [línea {inicializacion_node.lineno}]: Inicialización de '{var_name}' mal formada.")
                    return TYPE_ERROR
            return None # Declaration statement has no type
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de declaración inválida.")
            return TYPE_ERROR

    def _check_assignment_compatibility(self, lhs_type, rhs_type, lineno, var_name="variable"):
        # Basic compatibility rules
        # print(f"DEBUG: CheckAssign: LHS={lhs_type}, RHS={rhs_type}, var={var_name}, line={lineno}")
        if lhs_type == rhs_type:
            return True # Types match

        # Promotion/conversion rules:
        # float = int (OK)
        # int = float (OK with truncation, or specific language rule)
        if lhs_type == 'float' and rhs_type == 'int':
            return True
        if lhs_type == 'int' and rhs_type == 'float':
            # print(f"Advertencia [línea {lineno}]: Asignación de float a int '{var_name}', posible truncamiento.")
            return True # Allow with potential truncation

        # Add more rules as needed, e.g. bool to int/float or vice-versa if language supports

        self.symbol_table.add_error(
            f"Error de tipo [línea {lineno}]: No se puede asignar un valor de tipo '{rhs_type}' a la variable '{var_name}' de tipo '{lhs_type}'."
        )
        return False


    def _visit_inicializacion(self, node):
        # This is mostly handled by _visit_declaracion or _visit_funcion (for global vars)
        # If called directly, it means we are interested in the type of the expression if one exists
        # inicializacion -> EQUALS exp | ε
        if node.children and node.children[0].value != 'ε':
            if node.children[0].value == 'EQUALS':
                if len(node.children) == 2:
                    return self._visit(node.children[1]) # Visit exp node, return its type
                else: # Malformed
                    self.symbol_table.add_error(f"Error semántico [línea {node.lineno}]: Estructura de inicialización con '=' inválida.")
                    return TYPE_ERROR
            else: # Should not happen based on grammar if not epsilon and not EQUALS
                self.symbol_table.add_error(f"Error semántico [línea {node.lineno}]: Estructura de inicialización inválida.")
                return TYPE_ERROR
        return None # Epsilon case, no type


    def _visit_for_assignment(self, node):
        # for_assignment -> ID EQUALS exp
        if node.children and len(node.children) == 3 and \
           node.children[0] and \
           node.children[1] and node.children[1].value == 'EQUALS' and \
           node.children[2] and node.children[2].value == 'exp':

            id_node = node.children[0]
            exp_node = node.children[2]

            var_name = id_node.value
            var_lineno = id_node.lineno

            symbol = self.symbol_table.lookup_symbol(var_name)
            if symbol is None:
                self.symbol_table.add_error(
                    f"Error semántico [línea {var_lineno}]: La variable '{var_name}' no ha sido declarada (en asignación de for)."
                )
                return TYPE_ERROR

            lhs_type = symbol['type']
            if lhs_type.startswith("FUNCTION"):
                 self.symbol_table.add_error(f"Error semántico [línea {var_lineno}]: No se puede asignar a una función '{var_name}' en bucle for.")
                 return TYPE_ERROR

            rhs_type = self._visit(exp_node)
            if rhs_type == TYPE_ERROR:
                return TYPE_ERROR

            self._check_assignment_compatibility(lhs_type, rhs_type, var_lineno, var_name)
            return None # Assignment in for has no type itself
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de for_assignment inválida.")
            return TYPE_ERROR

    # --- Expression visitors ---
    # These visitors should now return the inferred type of the expression, or TYPE_ERROR.

    def _infer_binary_op_type(self, type1, type2, op, lineno):
        # print(f"DEBUG: InferBinary: {type1} {op} {type2} at line {lineno}")
        if type1 == TYPE_ERROR or type2 == TYPE_ERROR:
            return TYPE_ERROR

        # Define valid operations and promotions
        # Arithmetic ops: +, -, *, /
        if op in ['PLUS', 'MINUS', 'TIMES', 'DIVIDE']:
            if type1 == 'int' and type2 == 'int': return 'int'
            if (type1 == 'float' and type2 == 'float') or \
               (type1 == 'int' and type2 == 'float') or \
               (type1 == 'float' and type2 == 'int'): return 'float'
            if type1 == 'string' and type2 == 'string' and op == 'PLUS': return 'string' # String concatenation

            self.symbol_table.add_error(f"Error de tipo [línea {lineno}]: Operación aritmética '{op}' inválida entre '{type1}' y '{type2}'.")
            return TYPE_ERROR

        # Modulo op: %
        if op == 'MOD':
            if type1 == 'int' and type2 == 'int': return 'int'
            self.symbol_table.add_error(f"Error de tipo [línea {lineno}]: Operación módulo '{op}' inválida entre '{type1}' y '{type2}'. Solo int % int permitido.")
            return TYPE_ERROR

        # Relational ops: EQ, NE, LT, GT, LE, GE -> always bool
        if op in ['EQ', 'NE', 'LT', 'GT', 'LE', 'GE']:
            # Allow comparison between int/float, or string/string, or bool/bool
            if (type1 in ['int', 'float'] and type2 in ['int', 'float']) or \
               (type1 == 'string' and type2 == 'string') or \
               (type1 == 'bool' and type2 == 'bool'):
                return 'bool'
            self.symbol_table.add_error(f"Error de tipo [línea {lineno}]: Comparación '{op}' inválida entre '{type1}' y '{type2}'.")
            return TYPE_ERROR

        # Logical ops: AND, OR -> bool op bool = bool
        if op in ['AND', 'OR']:
            if type1 == 'bool' and type2 == 'bool': return 'bool'
            self.symbol_table.add_error(f"Error de tipo [línea {lineno}]: Operación lógica '{op}' inválida entre '{type1}' y '{type2}'. Se esperan booleanos.")
            return TYPE_ERROR

        self.symbol_table.add_error(f"Error Interno: Operador binario desconocido '{op}' en inferencia de tipos.")
        return TYPE_ERROR


    def _visit_exp(self, node): # exp -> E
        if node.children and len(node.children) > 0:
            return self._visit(node.children[0]) # Type of E
        return TYPE_ERROR

    def _visit_e(self, node): # E -> C E_rest
        if len(node.children) == 2:
            type_c = self._visit(node.children[0]) # Visit C
            if type_c == TYPE_ERROR: return TYPE_ERROR
            # Pass type_c to E_rest, which might use it as LHS of an OR
            return self._visit_e_rest(node.children[1], type_c)
        return TYPE_ERROR

    def _visit_e_rest(self, node, lhs_type): # E_rest -> OR C E_rest | ε
        if node.children and node.children[0].value != 'ε':
            # Children: OR_OPERATOR_NODE, C_NODE, E_REST_NODE
            if len(node.children) == 3:
                op_node = node.children[0] # e.g. Node('OR')
                op_lineno = op_node.lineno

                type_c = self._visit(node.children[1]) # Visit C (RHS of OR)
                if type_c == TYPE_ERROR: return TYPE_ERROR

                current_result_type = self._infer_binary_op_type(lhs_type, type_c, op_node.value, op_lineno)
                if current_result_type == TYPE_ERROR: return TYPE_ERROR

                # Recursively call E_rest with the new result type as its LHS
                return self._visit_e_rest(node.children[2], current_result_type)
            return TYPE_ERROR # Malformed E_rest
        return lhs_type # Epsilon case, type is whatever was passed from E or previous E_rest

    def _visit_c(self, node): # C -> R C_rest
        if len(node.children) == 2:
            type_r = self._visit(node.children[0])
            if type_r == TYPE_ERROR: return TYPE_ERROR
            return self._visit_c_rest(node.children[1], type_r)
        return TYPE_ERROR

    def _visit_c_rest(self, node, lhs_type): # C_rest -> AND R C_rest | ε
        if node.children and node.children[0].value != 'ε':
            if len(node.children) == 3:
                op_node = node.children[0]
                op_lineno = op_node.lineno
                type_r = self._visit(node.children[1])
                if type_r == TYPE_ERROR: return TYPE_ERROR
                current_result_type = self._infer_binary_op_type(lhs_type, type_r, op_node.value, op_lineno)
                if current_result_type == TYPE_ERROR: return TYPE_ERROR
                return self._visit_c_rest(node.children[2], current_result_type)
            return TYPE_ERROR
        return lhs_type

    def _visit_r(self, node): # R -> T R_rest
        if len(node.children) == 2:
            type_t = self._visit(node.children[0])
            if type_t == TYPE_ERROR: return TYPE_ERROR
            return self._visit_r_rest(node.children[1], type_t)
        return TYPE_ERROR

    def _visit_r_rest(self, node, lhs_type): # R_rest -> (EQ | NE | LT | GT | LE | GE) T R_rest | ε
        if node.children and node.children[0].value != 'ε':
            if len(node.children) == 3:
                op_node = node.children[0] # This is the relational operator node itself
                op_lineno = op_node.lineno
                type_t = self._visit(node.children[1])
                if type_t == TYPE_ERROR: return TYPE_ERROR
                current_result_type = self._infer_binary_op_type(lhs_type, type_t, op_node.value, op_lineno)
                if current_result_type == TYPE_ERROR: return TYPE_ERROR
                # Relational ops result in bool, but further ops in R_rest might chain with this bool.
                # Example: a < b < c is not typical direct chaining in C-like languages (it's (a<b)<c)
                # Assuming R_rest implies operations of same precedence level, so result type is passed.
                return self._visit_r_rest(node.children[2], current_result_type)
            return TYPE_ERROR
        return lhs_type

    def _visit_t(self, node): # T -> F T_rest
        if len(node.children) == 2:
            type_f = self._visit(node.children[0])
            if type_f == TYPE_ERROR: return TYPE_ERROR
            return self._visit_t_rest(node.children[1], type_f)
        return TYPE_ERROR

    def _visit_t_rest(self, node, lhs_type): # T_rest -> (PLUS | MINUS) F T_rest | ε
        if node.children and node.children[0].value != 'ε':
            if len(node.children) == 3:
                op_node = node.children[0]
                op_lineno = op_node.lineno
                type_f = self._visit(node.children[1])
                if type_f == TYPE_ERROR: return TYPE_ERROR
                current_result_type = self._infer_binary_op_type(lhs_type, type_f, op_node.value, op_lineno)
                if current_result_type == TYPE_ERROR: return TYPE_ERROR
                return self._visit_t_rest(node.children[2], current_result_type)
            return TYPE_ERROR
        return lhs_type

    def _visit_f(self, node): # F -> A F_rest
        if len(node.children) == 2:
            type_a = self._visit(node.children[0])
            if type_a == TYPE_ERROR: return TYPE_ERROR
            return self._visit_f_rest(node.children[1], type_a)
        return TYPE_ERROR

    def _visit_f_rest(self, node, lhs_type): # F_rest -> (TIMES | DIVIDE | MOD) A F_rest | ε
        if node.children and node.children[0].value != 'ε':
            if len(node.children) == 3:
                op_node = node.children[0]
                op_lineno = op_node.lineno
                type_a = self._visit(node.children[1])
                if type_a == TYPE_ERROR: return TYPE_ERROR
                current_result_type = self._infer_binary_op_type(lhs_type, type_a, op_node.value, op_lineno)
                if current_result_type == TYPE_ERROR: return TYPE_ERROR
                return self._visit_f_rest(node.children[2], current_result_type)
            return TYPE_ERROR
        return lhs_type

    def _visit_a(self, node):
        # node es el nodo 'A'
        # node.children[0] es el nodo terminal (ID, TRUE, STRING_LITERAL, etc.)
        # cuyo .value ha sido establecido al lexema por el parser.

        if not node.children:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Nodo 'A' sin hijos.")
            return TYPE_ERROR

        terminal_node = node.children[0]
        lexeme = terminal_node.value # Este es el lexema o valor numérico
        lexeme_lineno = terminal_node.lineno

        # Primero, verificar si es un literal numérico (ya convertido por el lexer)
        if isinstance(lexeme, int):
            return 'int'
        if isinstance(lexeme, float):
            return 'float'

        # Si es LPAREN exp RPAREN
        # El .value del nodo LPAREN no es sobreescrito por LEXEME_TERMINALS.
        if lexeme == 'LPAREN':
            if len(node.children) == 3 and \
               hasattr(node.children[1], 'value') and node.children[1].value == 'exp' and \
               hasattr(node.children[2], 'value') and node.children[2].value == 'RPAREN':
                return self._visit(node.children[1]) # Tipo de la expresión encerrada
            else:
                self.symbol_table.add_error(f"Error semántico [línea {lexeme_lineno}]: Paréntesis desbalanceados o expresión faltante.")
                return TYPE_ERROR

        # Ahora, lexeme debe ser una cadena. Puede ser de TRUE, FALSE, ID, o STRING_LITERAL.
        if not isinstance(lexeme, str):
            self.symbol_table.add_error(f"Error Interno: Tipo de lexema inesperado en 'A': '{lexeme}' (tipo {type(lexeme).__name__}) en línea {lexeme_lineno}.")
            return TYPE_ERROR

        # Manejar literales booleanos explícitamente por su lexema
        if lexeme == "true":
            return 'bool'
        if lexeme == "false":
            return 'bool'

        # En este punto, el lexema es una cadena que no es "true" ni "false".
        # Podría ser un ID o el contenido de un STRING_LITERAL.

        is_function_call_syntax = False
        if len(node.children) > 1 and hasattr(node.children[1], 'value') and node.children[1].value == 'llamada_func':
            llamada_func_node = node.children[1]
            if llamada_func_node.children and hasattr(llamada_func_node.children[0], 'value') and llamada_func_node.children[0].value != 'ε':
                is_function_call_syntax = True

        if is_function_call_syntax:
            func_name = lexeme
            symbol_info = self.symbol_table.lookup_symbol(func_name)

            if symbol_info is None or not symbol_info['type'].startswith("FUNCTION"):
                self.symbol_table.add_error(f"Error semántico [línea {lexeme_lineno}]: '{func_name}' no es una función declarada o no se puede llamar.")
                return TYPE_ERROR

            expected_param_types = symbol_info.get('param_types', [])
            llamada_func_node = node.children[1]

            if not (llamada_func_node.children and \
                    len(llamada_func_node.children) == 3 and \
                    hasattr(llamada_func_node.children[0], 'value') and llamada_func_node.children[0].value == 'LPAREN' and \
                    hasattr(llamada_func_node.children[1], 'value') and llamada_func_node.children[1].value == 'lista_args' and \
                    hasattr(llamada_func_node.children[2], 'value') and llamada_func_node.children[2].value == 'RPAREN'):
                 self.symbol_table.add_error(f"Error semántico [línea {lexeme_lineno}]: Llamada a función '{func_name}' mal formada.")
                 return TYPE_ERROR

            lista_args_node = llamada_func_node.children[1]
            actual_arg_types = self._collect_arg_types(lista_args_node)
            if actual_arg_types == TYPE_ERROR: return TYPE_ERROR

            if len(actual_arg_types) != len(expected_param_types):
                self.symbol_table.add_error(f"Error de tipo [línea {lexeme_lineno}]: La función '{func_name}' esperaba {len(expected_param_types)} argumentos, pero recibió {len(actual_arg_types)}.")
                return TYPE_ERROR

            for i, (expected, actual) in enumerate(zip(expected_param_types, actual_arg_types)):
                if not self._check_assignment_compatibility(expected, actual, lexeme_lineno, f"argumento {i+1} de '{func_name}'"):
                    return TYPE_ERROR

            return_type_str = symbol_info['type'].split(' -> ')[-1].lower()
            return return_type_str if return_type_str else TYPE_ERROR
        else:
            # No es una llamada a función. El lexema es un ID o un STRING_LITERAL.
            symbol_info = self.symbol_table.lookup_symbol(lexeme)
            if symbol_info:
                if symbol_info['type'].startswith("FUNCTION"):
                    self.symbol_table.add_error(f"Error semántico [línea {lexeme_lineno}]: El nombre de función '{lexeme}' se usó como variable sin llamarla.")
                    return TYPE_ERROR
                return symbol_info['type']
            else:
                # No es "true", "false", no es una llamada, no es un ID declarado.
                # Por la gramática A -> STRING_LITERAL, este debe ser el caso.
                return 'string'

    def _collect_arg_types(self, lista_args_node):
        # lista_args -> exp lista_args_rest | ε
        types = []
        current_lista_node = lista_args_node
        while current_lista_node and current_lista_node.children and current_lista_node.children[0].value != 'ε':
            # First child of lista_args is 'exp' or first child of lista_args_rest is 'exp' (after COMMA)
            exp_node = None
            next_lista_node = None

            if current_lista_node.value == 'lista_args': # Top level: lista_args -> exp lista_args_rest
                if len(current_lista_node.children) == 2:
                    exp_node = current_lista_node.children[0]
                    next_lista_node = current_lista_node.children[1] # lista_args_rest
                else: return TYPE_ERROR # Malformed
            elif current_lista_node.value == 'lista_args_rest': # Recursive: lista_args_rest -> COMMA exp lista_args_rest
                if len(current_lista_node.children) == 3: # COMMA, exp, lista_args_rest
                    exp_node = current_lista_node.children[1]
                    next_lista_node = current_lista_node.children[2]
                else: return TYPE_ERROR # Malformed
            else: # Should not happen
                return TYPE_ERROR

            if not exp_node or exp_node.value != 'exp': return TYPE_ERROR # Expected exp

            arg_type = self._visit(exp_node)
            if arg_type == TYPE_ERROR: return TYPE_ERROR
            types.append(arg_type)

            current_lista_node = next_lista_node # Move to the _rest part
            if not next_lista_node or not next_lista_node.children or next_lista_node.children[0].value == 'ε':
                break # End of arguments
        return types


    # --- Function call related basic traversal (arguments are expressions) ---
    def _visit_llamada_func(self, node):
        # This node represents the ( ... ) part of a function call.
        # It's visited as part of _visit_a for `ID llamada_func` or `_visit_instruccion` for call statements.
        # The primary role here is to facilitate argument type collection if called directly,
        # but _collect_arg_types is more targeted.
        # If this method is called, it implies the call structure is valid.
        # It doesn't "return" a type itself; the type of a call is the function's return type, handled in _visit_a.
        if node.children and node.children[0].value != 'ε':
            if len(node.children) == 3 and node.children[0].value == 'LPAREN': # LPAREN, lista_args, RPAREN
                # Argument types are checked by the caller (_visit_a or _visit_instruccion via _collect_arg_types)
                # Visiting lista_args here would re-evaluate/re-check types, which is redundant if caller does it.
                # For now, let this be a simple traversal.
                return self._visit(node.children[1]) # Visit lista_args, effectively does nothing new if already checked
            else:
                self.symbol_table.add_error(f"Error semántico [línea {node.lineno}]: Estructura de llamada a función inválida.")
                return TYPE_ERROR
        return None # No specific type for the call construct itself, or epsilon case (no call)


    def _visit_lista_args(self, node):
        # lista_args -> exp lista_args_rest | ε
        # This is mainly for traversal if called independently.
        # Type collection is done by _collect_arg_types.
        if node.children and node.children[0].value != 'ε':
            if len(node.children) == 2:
                exp_type = self._visit(node.children[0]) # Visit exp
                if exp_type == TYPE_ERROR: return TYPE_ERROR
                rest_type = self._visit(node.children[1]) # Visit lista_args_rest
                if rest_type == TYPE_ERROR: return TYPE_ERROR
                return None # List of args doesn't have a single type
            else:
                self.symbol_table.add_error(f"Error semántico [línea {node.lineno}]: Estructura de lista de argumentos inválida.")
                return TYPE_ERROR
        return None # Epsilon case

    def _visit_lista_args_rest(self, node):
        # lista_args_rest -> COMMA exp lista_args_rest | ε
        if node.children and node.children[0].value != 'ε':
            if len(node.children) == 3: # COMMA, exp, lista_args_rest
                exp_type = self._visit(node.children[1]) # Visit exp
                if exp_type == TYPE_ERROR: return TYPE_ERROR
                rest_type = self._visit(node.children[2]) # Visit lista_args_rest
                if rest_type == TYPE_ERROR: return TYPE_ERROR
                return None
            else:
                self.symbol_table.add_error(f"Error semántico [línea {node.lineno}]: Estructura de continuación de lista de argumentos inválida.")
                return TYPE_ERROR
        return None

    def _visit_print(self, node):
        # Print -> PRINT LPAREN exp RPAREN (SEMI handled by instruccion)
        if len(node.children) == 4 and node.children[0].value == 'PRINT' and \
           node.children[1].value == 'LPAREN' and node.children[2].value == 'exp' and \
           node.children[3].value == 'RPAREN':
            exp_type = self._visit(node.children[2]) # Visit the expression child
            if exp_type == TYPE_ERROR:
                return TYPE_ERROR
            # Optionally, check if exp_type is printable (e.g., not function type if functions not first-class)
            # For now, allow printing any validly typed expression.
            return None # Print statement has no type
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de Print inválida.")
            return TYPE_ERROR


    def _visit_if(self, node): # If -> IF LPAREN exp RPAREN LBRACE bloque RBRACE Else
        if len(node.children) == 8 and node.children[0].value == 'IF' and \
           node.children[1].value == 'LPAREN' and node.children[2].value == 'exp' and \
           node.children[3].value == 'RPAREN' and node.children[4].value == 'LBRACE' and \
           node.children[5].value == 'bloque' and node.children[6].value == 'RBRACE' and \
           node.children[7].value == 'Else':
           

            cond_type = self._visit(node.children[2]) # Visit exp (condition)
            if cond_type == TYPE_ERROR: return TYPE_ERROR
            if cond_type != 'bool':
                self.symbol_table.add_error(f"Error de tipo [línea {node.children[2].lineno}]: La condición del If debe ser de tipo bool, no '{cond_type}'.")
                # Continue checking other parts if desired, or return TYPE_ERROR

            if self._visit(node.children[4]) == TYPE_ERROR: return TYPE_ERROR # Visit bloque
            if self._visit(node.children[5]) == TYPE_ERROR: return TYPE_ERROR # Visit Else
            return None # If statement has no type
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de If inválida.")
            return TYPE_ERROR

    def _visit_else(self, node): # Else -> ELSE LBRACE bloque RBRACE | ε
        if node.children and node.children[0].value != 'ε':
            # Children: ELSE_KW_NODE, bloque_NODE
            if len(node.children) == 4 and node.children[0].value == 'ELSE' \
                and node.children[1].value == 'LBRACE'\
                and node.children[2].value == 'bloque'\
                and node.children[3].value == 'RBRACE':
                 return self._visit(node.children[2]) # Visit bloque
            else:
                 self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de Else inválida.")
                 return TYPE_ERROR
        return None # Epsilon case

    def _visit_while(self, node): # While -> WHILE LPAREN exp RPAREN LBRACE bloque RBRACE
        if node.children and len(node.children) == 7 and node.children[0].value == 'WHILE' and \
           node.children[1].value == 'LPAREN' and node.children[2].value == 'exp' and \
           node.children[3].value == 'RPAREN' and node.children[4].value == 'LPAREN' and\
           node.children[5].value == 'bloque' and node.children[6].value == 'RPAREN':

            cond_type = self._visit(node.children[2]) # Visit exp (condition)
            if cond_type == TYPE_ERROR: return TYPE_ERROR
            if cond_type != 'bool':
                self.symbol_table.add_error(f"Error de tipo [línea {node.children[2].lineno}]: La condición del While debe ser de tipo bool, no '{cond_type}'.")

            if self._visit(node.children[5]) == TYPE_ERROR: return TYPE_ERROR # Visit bloque
            return None # While statement has no type
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de While inválida.")
            return TYPE_ERROR

    def _visit_for(self, node): # For -> FOR LPAREN for_assignment SEMI exp SEMI for_assignment RPAREN LBRACE bloque RBRACE
        if node.children and len(node.children) == 11 and \
           node.children[0].value == 'FOR' and \
           node.children[1].value == 'LPAREN' and node.children[2].value == 'for_assignment' and \
           node.children[3].value == 'SEMI' and node.children[4].value == 'exp' and \
           node.children[5].value == 'SEMI' and node.children[6].value == 'for_assignment' and \
           node.children[7].value == 'RPAREN' and node.children[8].value == 'LBRACE' and \
           node.children[9].value == 'bloque' and node.children[10].value == 'RBRACE':

            if self._visit(node.children[2]) == TYPE_ERROR: return TYPE_ERROR # Visit for_assignment1 (init)

            cond_type = self._visit(node.children[4]) # Visit exp (condition)
            if cond_type == TYPE_ERROR: return TYPE_ERROR
            if cond_type != 'bool' and cond_type is not None : # None if exp is empty, grammar might need exp_opt
                self.symbol_table.add_error(f"Error de tipo [línea {node.children[4].lineno}]: La condición del For debe ser de tipo bool, no '{cond_type}'.")

            if self._visit(node.children[6]) == TYPE_ERROR: return TYPE_ERROR # Visit for_assignment2 (increment)
            if self._visit(node.children[9]) == TYPE_ERROR: return TYPE_ERROR # Visit bloque
            return None # For statement has no type
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de For inválida.")
            return TYPE_ERROR

    def _visit_return(self, node): # Return -> RETURN exp_opt SEMI (SEMI handled by instruccion)
        # Assuming node.value is 'Return' and children are [RETURN_KW, exp_opt] or [RETURN_KW, exp_opt, SEMI]
        # Let's assume children are [RETURN_KW, exp_opt, SEMI] as per typical full rule node
        exp_opt_node = None
        return_kw_lineno = node.lineno # Line of RETURN keyword

        if len(node.children) == 3 and node.children[0].value == 'RETURN' and \
           node.children[1].value == 'exp_opt' and node.children[2].value == 'SEMI':
            exp_opt_node = node.children[1]
            return_kw_lineno = node.children[0].lineno
        elif len(node.children) == 1 and node.children[0].value == 'exp_opt': # If called on 'Return' node from instruccion -> Return
             exp_opt_node = node.children[0] # Return node's child is exp_opt
             # lineno of Return node itself
        elif len(node.children) == 2 and node.children[0].value == 'RETURN' and node.children[1].value == 'SEMI': # Return -> RETURN SEMI
            exp_opt_node = None # No expression
            return_kw_lineno = node.children[0].lineno
        else: # Malformed
            self.symbol_table.add_error(f"Error semántico [línea {return_kw_lineno}]: Estructura de Return inválida.")
            return TYPE_ERROR

        returned_type = None
        if exp_opt_node and exp_opt_node.children and exp_opt_node.children[0].value != 'ε':
            # exp_opt -> exp
            returned_type = self._visit(exp_opt_node) # This will visit 'exp' child if exp_opt -> exp
            if returned_type == TYPE_ERROR:
                return TYPE_ERROR
        else: # exp_opt -> ε (empty return)
            returned_type = 'void'

        expected_return_type = self.current_function_return_type
        if not expected_return_type: # Should not happen if current_function_return_type is managed
            self.symbol_table.add_error(f"Error Interno [línea {return_kw_lineno}]: No se pudo determinar el tipo de retorno esperado de la función actual '{self.current_function_name}'.")
            return TYPE_ERROR

        # Check compatibility: returned_type vs expected_return_type
        if expected_return_type == 'void' and returned_type != 'void':
            self.symbol_table.add_error(f"Error de tipo [línea {return_kw_lineno}]: La función '{self.current_function_name}' no debe retornar un valor (esperado: void, obtenido: {returned_type}).")
            return TYPE_ERROR
        if expected_return_type != 'void' and returned_type == 'void':
            self.symbol_table.add_error(f"Error de tipo [línea {return_kw_lineno}]: La función '{self.current_function_name}' debe retornar un valor de tipo {expected_return_type} (obtenido: void).")
            return TYPE_ERROR

        if expected_return_type != 'void' and returned_type != 'void':
            if not self._check_assignment_compatibility(expected_return_type, returned_type, return_kw_lineno, "valor de retorno"):
                # Error already added by _check_assignment_compatibility
                return TYPE_ERROR

        return None # Return statement has no type


    def _visit_exp_opt(self, node): # exp_opt -> exp | ε
        if node.children and node.children[0].value != 'ε':
            # Children: [Node('exp')]
            if len(node.children) == 1 and node.children[0].value == 'exp':
                return self._visit(node.children[0]) # visit exp, return its type
            else: # Malformed
                self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de exp_opt inválida.")
                return TYPE_ERROR
        return 'void' # Epsilon case means effectively void type for return context


    def get_symbol_table_formatted(self):
        return self.symbol_table.get_formatted_symbol_table()

    def get_errors_formatted(self):
        return self.symbol_table.get_formatted_errors()