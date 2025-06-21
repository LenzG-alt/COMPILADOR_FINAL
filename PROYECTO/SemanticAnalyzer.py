from SymbolTable import SymbolTable
# Assuming Node class is in Parser.py or accessible if needed for type hinting (not strictly required for this step)
# from .Parser import Node # Example if Parser.Node was needed and Parser is in the same package

class SemanticAnalyzer:
    def __init__(self, ast_root):
        self.ast_root = ast_root
        self.symbol_table = SymbolTable()
        # current_function_name can be useful to pass down during traversal for context,
        # especially when adding local symbols to know their function scope.
        self.current_function_name = None

    def analyze(self):
        if self.ast_root:
            self._visit(self.ast_root)
        else:
            # This case should ideally not happen if parsing was successful
            self.symbol_table.add_error("Error semántico: No se proporcionó un árbol sintáctico para analizar.")

    def _visit(self, node):
        # Basic dispatcher based on node.value (non-terminal name or terminal type/value)
        # More specific checks (e.g. based on children structure) might be needed for some rules.

        if not node: # Should not happen with a well-formed AST
            return

        method_name = f'_visit_{node.value.lower().replace("(", "_lparen_").replace(")", "_rparen_")}' # Sanitize node names for methods

        # Fallback for generic node types or specific terminals not handled explicitly
        visitor = getattr(self, method_name, self._generic_visit)

        # print(f"Visiting: {node.value}, Method: {visitor.__name__}") # For debugging traversal

        return visitor(node)

    def _get_node_type_str(self, tipo_node):
        if tipo_node and tipo_node.value == 'tipo' and tipo_node.children:
            return tipo_node.children[0].value
        return "UnknownType"

    def _generic_visit(self, node):
        # Default behavior: visit all children
        # print(f"Generic visit for node: {node.value} with {len(node.children)} children") # Debug
        for child in node.children:
            self._visit(child)

    # Visitor methods for common top-level grammar rules

    def _visit_programa(self, node):
        # print(f"Visiting programa node: {node.value}") # Debug
        # Global scope is already entered by SymbolTable.__init__
        # Children of 'programa' are typically 'funciones'
        self._generic_visit(node) # Or iterate children: for child in node.children: self._visit(child)

    def _visit_funciones(self, node):
        # print(f"Visiting funciones node: {node.value}") # Debug
        # Iterates over 'funcion' and subsequent 'funciones' or 'epsilon'
        self._generic_visit(node) # Or iterate children: for child in node.children: self._visit(child)

    def _visit_funcion(self, node):
        # Ensure children are not None before accessing them
        if not node.children or not all(c for c in node.children): # Basic check if node.children or any child is None
            self._generic_visit(node) # Or log an error for malformed AST
            return

        # Check for global variable declaration pattern (from Step 4.1)
        # The structure is: funcion -> tipo ID funcion_rest
        # where ID node's value has been replaced by the lexeme (e.g., "hola")
        # So, we check for 'tipo' and 'funcion_rest', and assume child[1] is the ID node.
        if len(node.children) == 3 and \
           node.children[0] and node.children[0].value == 'tipo' and \
           node.children[1] and \
           node.children[2] and node.children[2].value == 'funcion_rest':
            # node.children[1] is the ID node, its .value is the lexeme
            funcion_rest_node = node.children[2]
            # funcion_rest -> inicializacion SEMI (for global variables)
            if funcion_rest_node and len(funcion_rest_node.children) == 2 and \
               funcion_rest_node.children[0] and funcion_rest_node.children[0].value == 'inicializacion' and \
               funcion_rest_node.children[1] and funcion_rest_node.children[1].value == 'SEMI':

                # This is a global variable declaration
                tipo_node = node.children[0]
                id_node = node.children[1] # This node holds the lexeme e.g. "hola"

                type_str = self._get_node_type_str(tipo_node)
                var_name = id_node.value # var_name is the lexeme e.g. "hola"
                var_lineno = id_node.lineno

                self.symbol_table.add_symbol(var_name, type_str, var_lineno, 'global')
                return

        # Check for MAIN function definition: MAIN LPAREN RPAREN bloque
        if len(node.children) == 4 and \
           node.children[0] and node.children[0].value == 'MAIN' and \
           node.children[1] and node.children[1].value == 'LPAREN' and \
           node.children[2] and node.children[2].value == 'RPAREN' and \
           node.children[3] and node.children[3].value == 'bloque':

            func_name = "main"
            func_lineno = node.children[0].lineno # Line of 'MAIN' keyword

            # Add main function to symbol table (current scope should be global)
            # Assuming global scope is the first one in scope_stack
            current_scope_name_for_func_decl = self.symbol_table.scope_stack[-1]['name']
            self.symbol_table.add_symbol(func_name, "FUNCTION (VOID)", func_lineno, current_scope_name_for_func_decl)

            # Order: set name, enter scope, visit params (none for main), visit block, exit, reset name
            self.current_function_name = func_name
            self.symbol_table.enter_scope(func_name)

            # Main has no explicit parameters in this grammar structure to visit via _visit(parametros_node)

            bloque_node = node.children[3] # bloque_node is child 3
            if bloque_node: self._visit(bloque_node) # Visit function block

            self.symbol_table.exit_scope()
            self.current_function_name = None # Reset after exiting scope
            return

        # Check for regular function definition: tipo ID funcion_rest (where funcion_rest is LPAREN parametros RPAREN bloque)
        # The ID node (node.children[1]) for function name should have its .value as the lexeme.
        if len(node.children) == 3 and \
           node.children[0] and node.children[0].value == 'tipo' and \
           node.children[1] and \
           node.children[2] and node.children[2].value == 'funcion_rest':
            # node.children[1] is the ID node for function name, its .value is the lexeme
            funcion_rest_node = node.children[2]
            if funcion_rest_node and len(funcion_rest_node.children) == 4 and \
               funcion_rest_node.children[0] and funcion_rest_node.children[0].value == 'LPAREN' and \
               funcion_rest_node.children[1] and funcion_rest_node.children[1].value == 'parametros' and \
               funcion_rest_node.children[2] and funcion_rest_node.children[2].value == 'RPAREN' and \
               funcion_rest_node.children[3] and funcion_rest_node.children[3].value == 'bloque':

                tipo_node_for_func = node.children[0]
                id_node = node.children[1] # Function name ID node
                func_name = id_node.value # Function name is the lexeme
                func_lineno = id_node.lineno
                func_return_type_str = self._get_node_type_str(tipo_node_for_func)

                # Add function symbol itself to parent scope (e.g., global)
                # Assuming global scope is the first one in scope_stack
                current_scope_name_for_func_decl = self.symbol_table.scope_stack[-1]['name']
                self.symbol_table.add_symbol(func_name, f"FUNCTION ({func_return_type_str})", func_lineno, current_scope_name_for_func_decl)

                # Order: set name, enter scope, visit params, visit block, exit, reset name
                self.current_function_name = func_name
                self.symbol_table.enter_scope(func_name)

                parametros_node = funcion_rest_node.children[1]
                if parametros_node: self._visit(parametros_node) # Visit parameters

                bloque_node = funcion_rest_node.children[3]
                if bloque_node: self._visit(bloque_node) # Visit function block

                self.symbol_table.exit_scope()
                self.current_function_name = None # Reset after exiting scope
                return

        # Fallback for other cases
        self._generic_visit(node)

    def _visit_parametros(self, node):
        if node.children and node.children[0].value != 'ε':
            # Has a 'parametro' and 'parametros_rest'
            self._visit(node.children[0]) # Visit parametro
            if len(node.children) > 1:
                self._visit(node.children[1]) # Visit parametros_rest
        # Else: epsilon production, do nothing

    def _visit_parametros_rest(self, node):
        if node.children and node.children[0].value != 'ε':
            # Has COMMA, parametro, parametros_rest
            if len(node.children) == 3:
                self._visit(node.children[1]) # Visit parametro
                self._visit(node.children[2]) # Visit next parametros_rest
        # Else: epsilon production, do nothing

    def _visit_parametro(self, node):
        print(f"DEBUG: _visit_parametro: node.value='{node.value if hasattr(node, 'value') else 'N/A'}' (type: {type(node).__name__}), node.lineno={node.lineno if hasattr(node, 'lineno') else 'N/A'}, num_children={len(node.children) if node.children else 'None'}")
        if node.children:
            for i, child in enumerate(node.children):
                print(f"  Child {i}: value='{child.value if hasattr(child, 'value') else 'N/A'}' (type: {type(child).__name__}), lineno={child.lineno if hasattr(child, 'lineno') else 'N/A'}")
        else:
            print("  _visit_parametro: Node has no children.")

        # Children: [Node('tipo'), Node_with_lexeme_as_value]
        # The ID node's value is the lexeme.
        if node.children and len(node.children) == 2 and \
           node.children[0] and node.children[0].value == 'tipo' and \
           node.children[1]: # Ensure the second child (ID node) exists

            tipo_node = node.children[0]
            id_node = node.children[1] # id_node is node.children[1]

            type_str = self._get_node_type_str(tipo_node)
            param_name = id_node.value # Correctly uses .value as lexeme
            param_lineno = id_node.lineno

            if self.current_function_name: # Should always be true here
                print(f"DEBUG: Adding param '{param_name}' type '{type_str}' line {param_lineno} to scope '{self.current_function_name}'")
                self.symbol_table.add_symbol(param_name, type_str, param_lineno, self.current_function_name)
            else:
                # This error should ideally not be hit if current_function_name is managed well
                self.symbol_table.add_error(f"Error Interno [línea {param_lineno}]: Parámetro '{param_name}' declarado fuera del contexto de una función.")
            return

        # If structural check fails:
        param_node_line = node.lineno if node else -1
        print(f"DEBUG: _visit_parametro structural check failed for node line {param_node_line} (value: {node.value if node else 'N/A'})")
        self.symbol_table.add_error(f"Error semántico [línea {param_node_line}]: Estructura de parámetro inválida.")

    def _visit_bloque(self, node):
        # Children: [Node('LBRACE'), Node('instrucciones'), Node('RBRACE')]
        if len(node.children) == 3 and \
           node.children[0] and node.children[0].value == 'LBRACE' and \
           node.children[1] and node.children[1].value == 'instrucciones' and \
           node.children[2] and node.children[2].value == 'RBRACE':

            instrucciones_node = node.children[1]
            self._visit(instrucciones_node)
        else: # Should not happen with correct grammar
            # self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de bloque inválida.")
            self._generic_visit(node) # Fallback to generic visit if structure is unexpected

    def _visit_instrucciones(self, node):
        if node.children and node.children[0].value != 'ε':
            # Has 'instruccion' and 'instrucciones'
            if len(node.children) > 0: # Should have at least instruccion
                 self._visit(node.children[0]) # Visit instruccion
            if len(node.children) > 1: # Check for recursive instrucciones
                 self._visit(node.children[1]) # Visit next instrucciones
        # Else: epsilon production, do nothing

    def _visit_instruccion(self, node):
        if not node.children or len(node.children) == 0:
            return

        first_child_of_instruccion = node.children[0]

        # Check if the first child is an ID node (lexeme) due to instruccion -> ID id_rhs_instruccion
        # This requires checking its type or assuming if not other instruction types, it's an ID.
        # For simplicity, we rely on the fact that other instruction types like 'declaracion', 'If', etc.
        # would have specific node.value. An ID node here would have its lexeme as node.value.
        # A more robust way would be to check the original token type if stored, or refine the dispatcher.

        # Assuming node.value for children are specific like 'declaracion', 'If', 'Print', 'Return', 'While', 'For', 'bloque'
        # or the ID lexeme itself if it's from ID id_rhs_instruccion

        is_id_first_child = first_child_of_instruccion.value not in [
            'declaracion', 'If', 'While', 'For', 'Return', 'Print', 'bloque' # Add other direct instruction types if any
        ]
        # This heuristic might need refinement if ID lexemes can clash with instruction keywords.
        # A better way: in parser, make Node for 'ID id_rhs_instruccion' be e.g. Node('assignment_or_call_stmt')

        if is_id_first_child and len(node.children) > 1: # Must be 'ID id_rhs_instruccion'
            id_node_lhs = first_child_of_instruccion
            id_rhs_node = node.children[1] # This should be Node('id_rhs_instruccion')

            if id_rhs_node and id_rhs_node.value == 'id_rhs_instruccion' and id_rhs_node.children:
                type_of_rhs = id_rhs_node.children[0].value # Should be EQUALS or llamada_func

                if type_of_rhs == 'EQUALS': # Assignment: id_rhs_instruccion -> EQUALS exp SEMI
                    var_name = id_node_lhs.value
                    var_lineno = id_node_lhs.lineno
                    print(f"DEBUG: _visit_instruccion (Assignment via ID EQUALS): Checking LHS ID '{var_name}' (line {var_lineno})")
                    symbol = self.symbol_table.lookup_symbol(var_name)
                    if symbol is None:
                        print(f"DEBUG: _visit_instruccion (Assignment via ID EQUALS): LHS ID '{var_name}' NOT FOUND.")
                        self.symbol_table.add_error(
                            f"Error semántico [línea {var_lineno}]: La variable '{var_name}' no ha sido declarada en este ámbito."
                        )
                    else:
                        print(f"DEBUG: _visit_instruccion (Assignment via ID EQUALS): LHS ID '{var_name}' FOUND: {symbol}")

                    if len(id_rhs_node.children) > 1 and id_rhs_node.children[1].value == 'exp':
                        exp_node = id_rhs_node.children[1]
                        if exp_node: self._visit(exp_node)
                    # SEMI is child 2, not visited for semantics here.

                elif type_of_rhs == 'llamada_func': # Function Call Statement: id_rhs_instruccion -> llamada_func SEMI
                    func_id_node = id_node_lhs
                    llamada_func_node = id_rhs_node.children[0] # This is Node('llamada_func')

                    print(f"DEBUG: _visit_instruccion (Function Call Stmt via ID llamada_func): Function name '{func_id_node.value}' (line {func_id_node.lineno})")

                    # Optional: Check if func_id_node.value is a declared function (if functions are in ST)
                    # symbol = self.symbol_table.lookup_symbol(func_id_node.value)
                    # if symbol is None or not symbol['type'].startswith('function'): # crude type check
                    #     self.symbol_table.add_error(f"Error: Función '{func_id_node.value}' no declarada.")

                    if llamada_func_node: self._visit(llamada_func_node) # To check arguments
                    # SEMI is child 1, not visited for semantics here.
                else:
                    # Unexpected structure for id_rhs_instruccion
                    # print(f"DEBUG: _visit_instruccion: Unexpected structure for id_rhs_instruccion child 0: {type_of_rhs}")
                    self._generic_visit(id_rhs_node)
            else:
                # Expected id_rhs_instruccion node not found or malformed
                # print(f"DEBUG: _visit_instruccion: id_rhs_node is missing or malformed for ID-led instruction.")
                self._generic_visit(node) # Fallback

        elif not is_id_first_child : # Standard instruction like declaracion, If, Print etc.
            self._visit(first_child_of_instruccion)

        else: # Fallback for other unexpected instruction structures
            # print(f"DEBUG: _visit_instruccion: Fallback for node {node.value}")
            self._generic_visit(node)
        # SEMI for assignments/calls is part of id_rhs_instruccion grammar,
        # SEMI for declaracion is handled by its own rule leading to _visit_declaracion.

    def _visit_declaracion(self, node):
        id_val = node.children[1].value if node.children and len(node.children) > 1 and hasattr(node.children[1], 'value') else 'N/A_ID_NODE'
        lin_val = node.children[1].lineno if node.children and len(node.children) > 1 and hasattr(node.children[1], 'lineno') else 'N/A_LINE'
        print(f"DEBUG: _visit_declaracion for ID '{id_val}' (line {lin_val}), current_function_name='{self.current_function_name}'")

        # declaracion -> tipo ID inicializacion
        # ID node (node.children[1]) has its .value as the lexeme, not "ID"
        if node.children and len(node.children) == 3 and \
           node.children[0] and node.children[0].value == 'tipo' and \
           node.children[1] and \
           node.children[2] and node.children[2].value == 'inicializacion':
            # node.children[1] is the ID node, its .value is the lexeme
            tipo_node = node.children[0]
            id_node = node.children[1]
            inicializacion_node = node.children[2]

            type_str = self._get_node_type_str(tipo_node)
            var_name = id_node.value
            var_lineno = id_node.lineno

            scope_attr_for_symbol = 'unknown_scope' # Fallback
            if self.current_function_name:
                scope_attr_for_symbol = self.current_function_name
            else:
                # This path implies a declaration is being processed not within a function scope
                # that was entered via _visit_funcion. This should be rare if grammar is C-like.
                self.symbol_table.add_error(
                    f"Error Interno [línea {var_lineno}]: Declaración local '{var_name}' procesada sin un nombre de función actual. Asumiendo 'global' para evitar error, pero esto es anómalo."
                )
                scope_attr_for_symbol = 'global' # Fallback to global to avoid crashing SymbolTable, but error is logged.


            self.symbol_table.add_symbol(var_name, type_str, var_lineno, scope_attr_for_symbol)

            # Visit the inicializacion part to handle expressions (for Step 4.4)
            self._visit(inicializacion_node)
        else: # Should not happen with correct grammar for declaracion
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de declaración inválida.")
            self._generic_visit(node)


    def _visit_inicializacion(self, node):
        # inicializacion -> EQUALS exp | ε
        if node.children and node.children[0].value != 'ε':
            if node.children[0].value == 'EQUALS': # Check for EQUALS
                 # Children: [Node('EQUALS'), Node('exp')]
                if len(node.children) == 2: # Make sure 'exp' exists
                    self._visit(node.children[1]) # Visit exp node
                # else: Malformed EQUALS without exp, could log error or rely on parser
            # else: could be an error if not epsilon and not EQUALS, but grammar should ensure this.
            # This path means it's not epsilon and not EQUALS, which shouldn't occur with valid grammar.
        # Else (epsilon or no children): do nothing for declaration part

    # def _visit_asignacion(self, node):
    #     # This method is now effectively deprecated for statement-level assignments.
    #     # Assignments like `ID EQUALS exp` as standalone statements are handled by
    #     # the new logic in _visit_instruccion for `instruccion -> ID id_rhs_instruccion`
    #     # where `id_rhs_instruccion -> EQUALS exp SEMI`.
    #     # This might still be called if 'asignacion' is used elsewhere (e.g. in For loops, pre-fix).
    #     # For now, commenting out to ensure it's not interfering.
    #     # print(f"DEBUG: _visit_asignacion called for node {node.value} - THIS SHOULD BE DEPRECATED FOR STATEMENTS")
    #     if node.children and len(node.children) == 3 and \
    #        node.children[0] and \
    #        node.children[1] and node.children[1].value == 'EQUALS' and \
    #        node.children[2] and node.children[2].value == 'exp':

    #         id_node = node.children[0]
    #         exp_node = node.children[2]
    #         var_name = id_node.value
    #         var_lineno = id_node.lineno

    #         print(f"DEBUG: _visit_asignacion (possibly from For): Checking LHS ID '{var_name}' (line {var_lineno}) for declaration.")
    #         symbol = self.symbol_table.lookup_symbol(var_name)
    #         if symbol is None:
    #             print(f"DEBUG: _visit_asignacion (possibly from For): LHS ID '{var_name}' NOT FOUND.")
    #             self.symbol_table.add_error(
    #                 f"Error semántico [línea {var_lineno}]: La variable '{var_name}' no ha sido declarada en este ámbito."
    #             )
    #         else:
    #             print(f"DEBUG: _visit_asignacion (possibly from For): LHS ID '{var_name}' FOUND: {symbol}")

    #         if exp_node: self._visit(exp_node)
    #     else:
    #         self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de asignación (old) inválida.")
    #         self._generic_visit(node)

    def _visit_for_assignment(self, node):
        # for_assignment -> ID EQUALS exp
        if node.children and len(node.children) == 3 and \
           node.children[0] and \
           node.children[1] and node.children[1].value == 'EQUALS' and \
           node.children[2] and node.children[2].value == 'exp':

            id_node = node.children[0] # This is the ID node
            exp_node = node.children[2]

            var_name = id_node.value # Lexeme
            var_lineno = id_node.lineno

            print(f"DEBUG: _visit_for_assignment: Checking LHS ID '{var_name}' (line {var_lineno}) for declaration.")
            symbol = self.symbol_table.lookup_symbol(var_name)
            if symbol is None:
                print(f"DEBUG: _visit_for_assignment: LHS ID '{var_name}' NOT FOUND.")
                self.symbol_table.add_error(
                    f"Error semántico [línea {var_lineno}]: La variable '{var_name}' no ha sido declarada en este ámbito."
                )
            else:
                print(f"DEBUG: _visit_for_assignment: LHS ID '{var_name}' FOUND: {symbol}")

            if exp_node: self._visit(exp_node) # Visit the RHS expression
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de for_assignment inválida.")
            self._generic_visit(node)


    # --- Expression visitors ---
    def _visit_exp(self, node): # exp -> E
        if node.children and len(node.children) > 0: self._visit(node.children[0])
        # else: error or epsilon, handle as per grammar for 'exp'

    def _visit_e(self, node): # E -> C E_rest
        if len(node.children) == 2:
            self._visit(node.children[0]) # Visit C
            self._visit(node.children[1]) # Visit E_rest
        # else: error in E structure

    def _visit_e_rest(self, node): # E_rest -> OR C E_rest | ε
        if node.children and node.children[0].value != 'ε':
            # Children: OR_OPERATOR_NODE, C_NODE, E_REST_NODE
            if len(node.children) == 3:
                 self._visit(node.children[1]) # Visit C
                 self._visit(node.children[2]) # Visit E_rest
            # else: error in E_rest structure (OR without all parts)

    def _visit_c(self, node): # C -> R C_rest
        if len(node.children) == 2:
            self._visit(node.children[0]) # Visit R
            self._visit(node.children[1]) # Visit C_rest
        # else: error in C structure

    def _visit_c_rest(self, node): # C_rest -> AND R C_rest | ε
        if node.children and node.children[0].value != 'ε':
            # Children: AND_OPERATOR_NODE, R_NODE, C_REST_NODE
            if len(node.children) == 3:
                self._visit(node.children[1]) # Visit R
                self._visit(node.children[2]) # Visit C_rest
            # else: error in C_rest structure

    def _visit_r(self, node): # R -> T R_rest
        if len(node.children) == 2:
            self._visit(node.children[0]) # Visit T
            self._visit(node.children[1]) # Visit R_rest
        # else: error in R structure

    def _visit_r_rest(self, node): # R_rest -> (EQ | NE | LT | GT | LE | GE) T R_rest | ε
        if node.children and node.children[0].value != 'ε':
            # Children: RELATIONAL_OPERATOR_NODE, T_NODE, R_REST_NODE
            if len(node.children) == 3:
                self._visit(node.children[1]) # Visit T
                self._visit(node.children[2]) # Visit R_rest
            # else: error in R_rest structure

    def _visit_t(self, node): # T -> F T_rest
        if len(node.children) == 2:
            self._visit(node.children[0]) # Visit F
            self._visit(node.children[1]) # Visit T_rest
        # else: error in T structure

    def _visit_t_rest(self, node): # T_rest -> (PLUS | MINUS) F T_rest | ε
        if node.children and node.children[0].value != 'ε':
            # Children: ADDITIVE_OPERATOR_NODE, F_NODE, T_REST_NODE
            if len(node.children) == 3:
                self._visit(node.children[1]) # Visit F
                self._visit(node.children[2]) # Visit T_rest
            # else: error in T_rest structure

    def _visit_f(self, node): # F -> A F_rest
        if len(node.children) == 2:
            self._visit(node.children[0]) # Visit A
            self._visit(node.children[1]) # Visit F_rest
        # else: error in F structure

    def _visit_f_rest(self, node): # F_rest -> (TIMES | DIVIDE | MOD) A F_rest | ε
        if node.children and node.children[0].value != 'ε':
            # Children: MULTIPLICATIVE_OPERATOR_NODE, A_NODE, F_REST_NODE
            if len(node.children) == 3:
                self._visit(node.children[1]) # Visit A
                self._visit(node.children[2]) # Visit F_rest
            # else: error in F_rest structure

    def _visit_a(self, node):
        # A -> LPAREN exp RPAREN | ID llamada_func | ID | INT_NUM | TRUE | FALSE | STRING
        # Note: Grammar from image seems to be `A -> ID | ID llamada_func | ...`
        # This implies `A` could have 1 child (ID) or 2 children (ID, llamada_func)
        if not node.children or len(node.children) == 0:
            print(f"DEBUG: _visit_a: Node 'A' (line {node.lineno if node else 'N/A'}) has no children.")
            return

        first_rhs_node = node.children[0]
        print(f"DEBUG: _visit_a: first_rhs_node.value = '{first_rhs_node.value}', type = {type(first_rhs_node.value)}, lineno = {first_rhs_node.lineno if hasattr(first_rhs_node, 'lineno') else 'N/A'}")

        if first_rhs_node.value == 'LPAREN':
            # LPAREN exp RPAREN
            if len(node.children) == 3 and node.children[1] and node.children[2] and node.children[2].value == 'RPAREN': # LPAREN, exp, RPAREN
                print(f"DEBUG: _visit_a: Visiting parenthesized expression.")
                self._visit(node.children[1]) # Visit exp
            else:
                self.symbol_table.add_error(f"Error semántico [línea {first_rhs_node.lineno if hasattr(first_rhs_node, 'lineno') else node.lineno}]: Estructura de paréntesis desbalanceada.")

        elif isinstance(first_rhs_node.value, (int, float, bool)):
            # This is a literal (e.g., INT_NUM, FLOAT_NUM, TRUE, FALSE whose values were converted by lexer/parser)
            print(f"DEBUG: _visit_a: Literal numeric or boolean '{first_rhs_node.value}' found. No action.")
            pass # No declaration check needed for literals.

        # Check for string literals explicitly if they are not converted to other types by lexer/parser
        # The grammar has A -> ID ... | STRING_LITERAL (implicitly via LEXEME_TERMINALS)
        # So, if first_rhs_node.value is a string, it could be an ID or a string literal.
        # We assume if LEXEME_TERMINALS converted 'STRING' type tokens, their value would be the string content.
        # A 'STRING' token type would be different from an 'ID' token type whose value is also a string.
        # This part relies on how parser sets node.value for ID vs other string-valued terminals.
        # For now, if it's a string and not LPAREN, it's treated as an ID.
        # This might need adjustment if 'STRING_LITERAL' nodes appear here with their string content as .value
        # and need to be distinguished from IDs.
        # The current parser's LEXEME_TERMINALS includes "STRING", so its value would be the string content.
        # However, an ID's value is also its string content.
        # A robust solution would be to check the *original token type* of first_rhs_node if available.
        # Lacking that, we use a heuristic: known keywords/types vs potential IDs.
        # The previous `is_id_node_structurally` was: `first_child.value not in ['LPAREN', 'INT_NUM', 'TRUE', 'FALSE', 'STRING']`
        # This was problematic because 'INT_NUM', 'TRUE', 'FALSE', 'STRING' are token TYPE names,
        # while first_child.value for these is the actual value (e.g., 10, True, "hello").

        # Refined logic: if it's not LPAREN and not an instance of int/float/bool, assume it's an ID (string).
        # String literals like "hello" would also fall into this 'else' if not handled separately.
        # If the grammar distinguishes A -> ID and A -> STRING_LITERAL, the node value might be 'ID' or 'STRING_LITERAL'
        # before lexeme replacement, or the lexeme itself after.
        # Given current AST construction, node.value is the lexeme for ID, and the content for STRING_LITERAL.
        # Let's assume any string value here that isn't 'LPAREN' is an ID to be looked up.
        # This means string literals would be incorrectly looked up.
        # This needs Node.original_token_type to be truly robust.
        # For now, let's stick to the provided logic and see.
        # The provided logic was:
        # is_id_node_structurally = first_child.value not in ['LPAREN', 'INT_NUM', 'TRUE', 'FALSE', 'STRING'] (problematic)

        # Corrected approach:
        # 1. Handle LPAREN
        # 2. Handle converted literals (int, float, bool from lexer)
        # 3. Assume other strings are IDs. This means string literals like "text" will be treated as IDs.
        #    This is a known limitation without original_token_type.
        elif isinstance(first_rhs_node.value, str):
            # This will treat string literals like "abc" as IDs if they reach here.
            # It also treats actual identifiers like 'myVar' as IDs.
            id_node = first_rhs_node
            var_name = id_node.value
            var_lineno = id_node.lineno

            print(f"DEBUG: _visit_a (ID branch): Checking usage of ID '{var_name}' (line {var_lineno})")
            symbol = self.symbol_table.lookup_symbol(var_name)
            if symbol is None:
                print(f"DEBUG: _visit_a (ID branch): ID '{var_name}' NOT FOUND in symbol table.")
                self.symbol_table.add_error(
                    f"Error semántico [línea {var_lineno}]: La variable '{var_name}' no ha sido declarada en este ámbito."
                )
            else:
                print(f"DEBUG: _visit_a (ID branch): ID '{var_name}' FOUND: {symbol}")

            # Check for function call part: A -> ID llamada_func
            if len(node.children) > 1 and node.children[1] and node.children[1].value == 'llamada_func':
                print(f"DEBUG: _visit_a (ID branch): Visiting llamada_func for '{var_name}'.")
                if node.children[1]: self._visit(node.children[1])
        else:
            # Unrecognized structure for 'A' node's first child or unexpected type
            print(f"DEBUG: _visit_a: Unrecognized structure or type for A's child: '{first_rhs_node.value}' type {type(first_rhs_node.value)}. Line: {first_rhs_node.lineno if hasattr(first_rhs_node, 'lineno') else 'N/A'}")
            self._generic_visit(node) # Fallback

    # --- Function call related basic traversal (arguments are expressions) ---
    def _visit_llamada_func(self, node):
        # llamada_func -> LPAREN lista_args RPAREN | ε (ε means it's just ID, not ID())
        # If called, it means this node exists. If its children[0] is epsilon, it's `ID` not `ID()`.
        # The grammar `A -> ID | ID llamada_func` means if `llamada_func` is present, it's `ID()`.
        # If `llamada_func` has children `LPAREN, lista_args, RPAREN`.
        if node.children and node.children[0].value != 'ε': # This epsilon is for `llamada_func -> ε` case
            if len(node.children) == 3 and node.children[0].value == 'LPAREN': # LPAREN, lista_args, RPAREN
                self._visit(node.children[1]) # Visit lista_args
            # else: error in llamada_func structure
        # If `llamada_func -> ε`, it means it was just an ID usage, not a call. No children to visit.


    def _visit_lista_args(self, node):
        # lista_args -> exp lista_args_rest | ε
        if node.children and node.children[0].value != 'ε':
            # Children: exp, lista_args_rest
            if len(node.children) == 2:
                self._visit(node.children[0]) # Visit exp
                self._visit(node.children[1]) # Visit lista_args_rest
            # else: error in lista_args structure

    def _visit_lista_args_rest(self, node):
        # lista_args_rest -> COMMA exp lista_args_rest | ε
        if node.children and node.children[0].value != 'ε':
            # Children: COMMA, exp, lista_args_rest
            if len(node.children) == 3:
                self._visit(node.children[1]) # Visit exp
                self._visit(node.children[2]) # Visit lista_args_rest
            # else: error in lista_args_rest structure

    def _visit_print(self, node):
        # Grammar for Print: Print -> PRINT LPAREN exp RPAREN SEMI
        # Node 'Print' (dispatched from _visit_instruccion)
        # Assuming children of Node('Print') are [PRINT_KW_NODE, LPAREN_NODE, EXP_NODE, RPAREN_NODE, SEMI_NODE]
        # Or, if grammar rule for instruccion is `Print_inst SEMI` and Print_inst is `PRINT LPAREN exp RPAREN`
        # then Node('Print') would have [PRINT_KW, LPAREN, exp, RPAREN]

        # Let's assume node.value is 'Print' (the non-terminal for the rule)
        # and its children are directly from its RHS in the grammar.
        # If Print -> PRINT LPAREN exp RPAREN (and SEMI is handled by instruccion)
        if len(node.children) == 4 and node.children[0].value == 'PRINT' and \
           node.children[1].value == 'LPAREN' and node.children[2].value == 'exp' and \
           node.children[3].value == 'RPAREN':
            self._visit(node.children[2]) # Visit the expression child
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de Print inválida.")
            self._generic_visit(node)


    def _visit_if(self, node): # If -> IF LPAREN exp RPAREN bloque Else
        if len(node.children) == 6 and node.children[0].value == 'IF' and \
           node.children[1].value == 'LPAREN' and node.children[2].value == 'exp' and \
           node.children[3].value == 'RPAREN' and node.children[4].value == 'bloque' and \
           node.children[5].value == 'Else':
            if node.children[2]: self._visit(node.children[2]) # Visit exp
            if node.children[4]: self._visit(node.children[4]) # Visit bloque
            if node.children[5]: self._visit(node.children[5]) # Visit Else
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de If inválida.")
            self._generic_visit(node)

    def _visit_else(self, node): # Else -> ELSE bloque | ε
        if node.children and node.children[0].value != 'ε':
            # Children: ELSE_KW_NODE, bloque_NODE
            if len(node.children) == 2 and node.children[0].value == 'ELSE' and node.children[1]:
                 self._visit(node.children[1]) # Visit bloque
            else:
                 self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de Else inválida.")
                 self._generic_visit(node)
        # Else: epsilon, do nothing

    def _visit_while(self, node): # While -> WHILE LPAREN exp RPAREN bloque
        if node.children and len(node.children) == 5 and node.children[0].value == 'WHILE' and \
           node.children[1].value == 'LPAREN' and node.children[2].value == 'exp' and \
           node.children[3].value == 'RPAREN' and node.children[4].value == 'bloque':
            if node.children[2]: self._visit(node.children[2]) # Visit exp
            if node.children[4]: self._visit(node.children[4]) # Visit bloque
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de While inválida.")
            self._generic_visit(node)

    def _visit_for(self, node): # For -> FOR LPAREN for_assignment SEMI exp SEMI for_assignment RPAREN bloque
        if node.children and len(node.children) == 9 and node.children[0].value == 'FOR' and \
           node.children[1].value == 'LPAREN' and node.children[2].value == 'for_assignment' and \
           node.children[3].value == 'SEMI' and node.children[4].value == 'exp' and \
           node.children[5].value == 'SEMI' and node.children[6].value == 'for_assignment' and \
           node.children[7].value == 'RPAREN' and node.children[8].value == 'bloque':
            if node.children[2]: self._visit(node.children[2]) # Visit for_assignment1
            if node.children[4]: self._visit(node.children[4]) # Visit exp
            if node.children[6]: self._visit(node.children[6]) # Visit for_assignment2
            if node.children[8]: self._visit(node.children[8]) # Visit bloque
        else:
            self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de For inválida.")
            self._generic_visit(node)

    def _visit_return(self, node): # Return -> RETURN exp_opt SEMI
        # If _visit_instruccion calls _visit(Node('Return')), then Node('Return')'s children are [RETURN_KW, exp_opt, SEMI]
        # or [RETURN_KW, exp_opt] if SEMI handled by instruccion.
        # Assuming Node('Return') has children [RETURN_KW, exp_opt, SEMI]
        if len(node.children) == 3 and node.children[0].value == 'RETURN' and \
           node.children[1].value == 'exp_opt' and node.children[2].value == 'SEMI':
            self._visit(node.children[1]) # visit exp_opt
        # Simplified: Assuming Node('Return') has one child 'exp_opt' if SEMI is not part of its direct rule
        elif len(node.children) == 1 and node.children[0].value == 'exp_opt': # Alternative if RETURN is the node value
             self._visit(node.children[0]) # visit exp_opt
        else:
            # This case handles if Return -> RETURN SEMI (empty return)
            if len(node.children) == 2 and node.children[0].value == 'RETURN' and node.children[1].value == 'SEMI':
                pass # Valid empty return if exp_opt can be completely absent
            else:
                self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de Return inválida.")
                self._generic_visit(node)


    def _visit_exp_opt(self, node): # exp_opt -> exp | ε
        if node.children and node.children[0].value != 'ε':
            if len(node.children) == 1 and node.children[0].value == 'exp':
                self._visit(node.children[0]) # visit exp
            else:
                self.symbol_table.add_error(f"Error semántico [línea {node.lineno if node else -1}]: Estructura de exp_opt inválida.")
                self._generic_visit(node)
        # Else: epsilon, do nothing

    # Add more _visit_xxx methods as needed for other non-terminals or specific terminals
    # that require special handling (e.g., _visit_declaracion, _visit_id for usage).

    def get_symbol_table_formatted(self):
        return self.symbol_table.get_formatted_symbol_table()

    def get_errors_formatted(self):
        return self.symbol_table.get_formatted_errors()

if __name__ == '__main__':
    # This part requires a mock AST or integration with the Parser to be truly testable.
    # For now, we can test if the class instantiates.

    # Mock Node class for basic testing if Parser.Node is not available
    class MockNode:
        def __init__(self, value, children=None, lineno=-1):
            self.value = value
            self.children = children if children else []
            self.lineno = lineno

    # Example Mock AST: programa -> funciones -> funcion (as global int x;) -> funciones (epsilon)
    #                      -> funcion (main() {}) -> funciones (epsilon)

    # Global var: int x;
    node_int = MockNode("INT", lineno=1)
    node_tipo_int = MockNode("tipo", [node_int], lineno=1)
    node_id_x = MockNode("ID", [], lineno=1) # Value would be 'x' after lexeme update
    node_id_x.value = 'x'
    node_epsilon_init = MockNode("ε", lineno=1)
    node_inicializacion_eps = MockNode("inicializacion", [node_epsilon_init], lineno=1)
    node_semi_global = MockNode("SEMI", lineno=1)
    node_func_rest_global = MockNode("funcion_rest", [node_inicializacion_eps, node_semi_global], lineno=1)
    global_var_decl_func_node = MockNode("funcion", [node_tipo_int, node_id_x, node_func_rest_global], lineno=1)

    # Main function: main() {}
    node_main_kw = MockNode("MAIN", lineno=2)
    node_lparen = MockNode("LPAREN", lineno=2)
    node_rparen = MockNode("RPAREN", lineno=2)
    node_lbrace = MockNode("LBRACE", lineno=2)
    node_rbrace = MockNode("RBRACE", lineno=2)
    node_instr_eps = MockNode("instrucciones", [MockNode("ε", lineno=2)], lineno=2)
    node_bloque_main = MockNode("bloque", [node_lbrace, node_instr_eps, node_rbrace], lineno=2)
    main_func_node = MockNode("funcion", [node_main_kw, node_lparen, node_rparen, node_bloque_main], lineno=2)

    # Funciones chain
    epsilon_funciones1 = MockNode("funciones", [MockNode("ε", lineno=3)], lineno=3)
    funciones_for_main = MockNode("funciones", [main_func_node, epsilon_funciones1], lineno=2)
    funciones_for_global_var = MockNode("funciones", [global_var_decl_func_node, funciones_for_main], lineno=1)

    # Programa root
    programa_node = MockNode("programa", [funciones_for_global_var], lineno=1)

    print("--- Basic SemanticAnalyzer Instantiation Test ---")
    analyzer = SemanticAnalyzer(programa_node)
    print("SemanticAnalyzer instantiated.")

    # Call analyze - it will only traverse due to placeholder visit methods
    print("\n--- Running analyze (expecting traversal via generic_visit or basic placeholders) ---")
    analyzer.analyze()
    print("analyze() completed.")

    print("\n--- Initial Symbol Table (should be empty or global only) ---")
    print(analyzer.get_symbol_table_formatted())

    print("\n--- Initial Errors (should be empty or 'No AST' if root was None) ---")
    print(analyzer.get_errors_formatted())

    print("\n--- Test with None AST ---")
    analyzer_none = SemanticAnalyzer(None)
    analyzer_none.analyze()
    print(analyzer_none.get_errors_formatted())
