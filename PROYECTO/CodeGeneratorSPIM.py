class CodeGeneratorSPIM:
    def __init__(self, ast_root, symbol_table):
        self.ast_root = ast_root
        self.symbol_table = symbol_table
        self.spim_code = []
        self.data_segment = []
        self.text_segment = []

        self.string_literals_map = {}
        self.next_string_label_id = 0

        self.temp_registers = [f"$t{i}" for i in range(10)] # $t0-$t9 for GPRs
        self.free_temps = self.temp_registers[:]
        self.used_temps_stack = []

        # FPU temporary registers (e.g., $f4-$f11, $f16-$f19 to avoid $f0 (return), $f12 (print arg))
        # SPIM typically offers $f0-$f31.
        self.fpu_temp_registers = [f"$f{i}" for i in range(4,12)] + [f"$f{i}" for i in range(13,20)]
        self.free_fpu_temps = self.fpu_temp_registers[:]
        self.used_fpu_temps_stack = []


        self.next_label_id = 0

        self.current_function_name = None
        self.current_function_return_label = None
        self.current_function_locals = {}
        self.current_function_params = {}
        self.current_stack_offset = 0
        self.param_stack_offset = 8

    def _add_to_data(self, directive):
        self.data_segment.append(f"    {directive}")

    def _add_to_text(self, instruction_or_label):
        if instruction_or_label.endswith(':'):
            self.text_segment.append(instruction_or_label)
        else:
            self.text_segment.append(f"    {instruction_or_label}")

    def _new_control_label(self, prefix="L_"):
        label = f"{prefix}{self.next_label_id}"
        self.next_label_id += 1
        return label

    def _new_string_label(self):
        label = f"str_{self.next_string_label_id}"
        self.next_string_label_id += 1
        return label

    def add_string_literal(self, string_value):
        if string_value in self.string_literals_map:
            return self.string_literals_map[string_value]

        label = self._new_string_label()
        self.string_literals_map[string_value] = label
        return label

    def get_temp_register(self):
        if not self.free_temps:
            # Basic spilling: if $s registers were used, could save one to stack.
            # For now, error out or reuse (less safe without careful liveness).
            raise Exception("Error: Ran out of general-purpose temporary registers.")
        reg = self.free_temps.pop(0)
        self.used_temps_stack.append(reg)
        return reg

    def release_temp_register(self, reg):
        if reg in self.used_temps_stack:
            self.used_temps_stack.remove(reg)
            self.free_temps.insert(0, reg)
            self.free_temps.sort()
        else:
            print(f"Warning: Attempted to release GPR {reg} not marked as used or already free.")

    def get_temp_fpu_register(self):
        if not self.free_fpu_temps:
            raise Exception("Error: Ran out of FPU temporary registers.")
        reg = self.free_fpu_temps.pop(0)
        self.used_fpu_temps_stack.append(reg)
        return reg

    def release_temp_fpu_register(self, reg):
        if reg in self.used_fpu_temps_stack:
            self.used_fpu_temps_stack.remove(reg)
            self.free_fpu_temps.insert(0, reg)
            self.free_fpu_temps.sort(key=lambda x: int(x[2:])) # Sort like $f4, $f5 ...
        else:
            print(f"Warning: Attempted to release FPU register {reg} not marked as used or already free.")


    def generate_code(self):
        self.spim_code = []
        self.data_segment = [".data"]
        self.text_segment = [".text", ".globl main"]

        if self.symbol_table.all_created_scopes_data:
            global_scope_symbols = self.symbol_table.all_created_scopes_data[0]['symbols']
            for name, attrs in global_scope_symbols.items():
                if not attrs['type'].startswith("FUNCTION"):
                    var_type = attrs['type']
                    if var_type == 'int' or var_type == 'bool':
                        self._add_to_data(f"{name}: .word 0")
                    elif var_type == 'float':
                        self._add_to_data(f"{name}: .float 0.0") # Initialize global floats to 0.0
                    elif var_type == 'string':
                        empty_str_label = self.add_string_literal("")
                        self._add_to_data(f"{name}: .word {empty_str_label}")
                    else:
                        self._add_to_data(f"# Unsupported global type: {var_type} for {name}")

        self._visit(self.ast_root)

        for string_val, label in self.string_literals_map.items():
            escaped_string = string_val.replace("\\", "\\\\").replace("\n", "\\n").replace("\t", "\\t").replace("\"", "\\\"")
            self._add_to_data(f"{label}: .asciiz \"{escaped_string}\"")

        self.spim_code.extend(self.data_segment)
        self.spim_code.append("")
        self.spim_code.extend(self.text_segment)

        return "\n".join(self.spim_code)

    def _visit(self, node):
        if node is None:
            return None

        node_type_str = str(node.value)

        if isinstance(node.value, int):
             method_name = '_visit_int_literal'
        elif isinstance(node.value, float):
             method_name = '_visit_float_literal' # Will return {'freg': ..., 'type': 'float'}
        else:
            sanitized_node_value = node_type_str.lower()
            sanitized_node_value = ''.join(c if c.isalnum() else '_' for c in sanitized_node_value)
            if sanitized_node_value == "eq": sanitized_node_value = "op_eq"
            elif sanitized_node_value == "ne": sanitized_node_value = "op_ne"
            elif sanitized_node_value == "lt": sanitized_node_value = "op_lt"
            elif sanitized_node_value == "le": sanitized_node_value = "op_le"
            elif sanitized_node_value == "gt": sanitized_node_value = "op_gt"
            elif sanitized_node_value == "ge": sanitized_node_value = "op_ge"

            if not sanitized_node_value or not sanitized_node_value[0].isalpha() and sanitized_node_value[0] != '_':
                 sanitized_node_value = "node_" + sanitized_node_value
            method_name = f'_visit_{sanitized_node_value}'

        visitor = getattr(self, method_name, self._generic_visit)
        return visitor(node)

    def _generic_visit(self, node):
        results = []
        for child in node.children:
            results.append(self._visit(child))
        # For non-expression nodes, the return value might not matter or be None.
        # For expression nodes, this might need to be smarter if results need combining.
        return results[0] if len(results) == 1 and results else results if results else None

    def _visit_programa(self, node):
        if node.children:
            self._visit(node.children[0])

    def _visit_funciones(self, node):
        if node.children and node.children[0].value != 'ε':
            self._visit(node.children[0])
            if len(node.children) > 1 and node.children[1].value == 'funciones':
                self._visit(node.children[1])

    def _visit_funcion(self, node):
        # ... (existing prologue setup, parameter offset calculation, local var offset calculation) ...
        # (This part remains largely the same as in Phase 5, ensuring param_names_ordered is used)
        func_name_node = None
        bloque_node = None
        is_main_func = False
        parametros_node = None

        if node.children[0].value == 'MAIN':
            if len(node.children) == 4:
                self.current_function_name = "main"
                bloque_node = node.children[3]
                is_main_func = True
            else:
                print(f"Error: Malformed MAIN function node: {node.value}")
                return
        elif node.children[0].value == 'tipo' and len(node.children) == 3:
            id_node = node.children[1]
            funcion_rest_node = node.children[2]
            if funcion_rest_node.children and len(funcion_rest_node.children) == 4 and \
               funcion_rest_node.children[0].value == 'LPAREN':
                self.current_function_name = id_node.value
                parametros_node = funcion_rest_node.children[1]
                bloque_node = funcion_rest_node.children[3]
                is_main_func = (self.current_function_name == "main")
            else:
                return
        else:
            print(f"Error: Unknown funcion structure processing: {node.value}")
            return

        if not self.current_function_name or not bloque_node:
            print(f"Error: Could not determine function name or block for function node processing.")
            return

        self._add_to_text(f"{self.current_function_name}:")
        self.current_function_locals.clear()
        self.current_function_params.clear()
        self.current_stack_offset = 0
        self.param_stack_offset = 8

        self._add_to_text(f"# --- Prologue for {self.current_function_name} ---")
        self._add_to_text("addi $sp, $sp, -4   # Allocate space for $ra")
        self._add_to_text("sw $ra, 0($sp)      # Save $ra")
        self._add_to_text("addi $sp, $sp, -4   # Allocate space for old $fp")
        self._add_to_text("sw $fp, 0($sp)      # Save old $fp")
        self._add_to_text("move $fp, $sp         # Set new $fp")

        local_vars_space = 0

        function_symbol_entry = self.symbol_table.lookup_symbol(self.current_function_name)
        if function_symbol_entry and 'param_names_ordered' in function_symbol_entry:
            for param_name in function_symbol_entry['param_names_ordered']:
                param_attrs = self.symbol_table.lookup_symbol(param_name, self.current_function_name)
                if param_attrs:
                    self.current_function_params[param_name] = self.param_stack_offset
                    self._add_to_text(f"# Param: {param_name} at {self.param_stack_offset}($fp)")
                    param_size = 4
                    if param_attrs['type'] == 'float': param_size = 4
                    self.param_stack_offset += param_size

        func_scope_symbols = None
        for scope_data_item in self.symbol_table.all_created_scopes_data:
            if scope_data_item['name'] == self.current_function_name:
                func_scope_symbols = scope_data_item['symbols']
                break

        if func_scope_symbols:
            for var_name, var_attrs in func_scope_symbols.items():
                is_parameter = var_name in self.current_function_params
                is_function_itself = var_attrs['type'].startswith("FUNCTION")

                if not is_parameter and not is_function_itself:
                    var_size = 4
                    if var_attrs['type'] == 'float': var_size = 4

                    local_vars_space += var_size
                    self.current_stack_offset -= var_size
                    self.current_function_locals[var_name] = self.current_stack_offset
                    self._add_to_text(f"# Local var: {var_name} at {self.current_stack_offset}($fp)")

        if local_vars_space > 0:
            self._add_to_text(f"addi $sp, $sp, -{local_vars_space}  # Allocate space for local variables")

        self._visit(bloque_node)

        self._add_to_text(f"# --- Epilogue for {self.current_function_name} ---")
        self.current_function_return_label = f"{self.current_function_name}_epilogue"
        self._add_to_text(f"{self.current_function_return_label}:")

        if local_vars_space > 0:
             self._add_to_text("move $sp, $fp         # Deallocate local variables")

        self._add_to_text("lw $fp, 0($sp)      # Restore old $fp")
        self._add_to_text("addi $sp, $sp, 4   # Deallocate space for old $fp")
        self._add_to_text("lw $ra, 0($sp)      # Restore $ra")
        self._add_to_text("addi $sp, $sp, 4   # Deallocate space for $ra")

        if is_main_func:
            self._add_to_text("# Exit program (end of main)")
            self._add_to_text("li $v0, 10")
            self._add_to_text("syscall")
        else:
            self._add_to_text(f"jr $ra              # Return to caller from {self.current_function_name}")

        self._add_to_text("")
        self.current_function_name = None
        self.current_function_locals.clear()
        self.current_function_params.clear()
        self.current_stack_offset = 0
        self.param_stack_offset = 8


    def _visit_bloque(self, node):
        if len(node.children) == 3 and node.children[1].value == 'instrucciones':
            self._visit(node.children[1])

    def _visit_instrucciones(self, node):
        if node.children and node.children[0].value != 'ε':
            self._visit(node.children[0])
            if len(node.children) > 1 and node.children[1].value == 'instrucciones':
                self._visit(node.children[1])

    def _visit_instruccion(self, node): # Refined for assignment AND function call statements
        first_child_node = node.children[0]
        is_assignment_or_call_stmt = False

        if len(node.children) == 2 and isinstance(first_child_node.value, str) and \
           node.children[1].value == 'id_rhs_instruccion':
            if self.symbol_table.lookup_symbol(first_child_node.value, self.current_function_name) or \
               self.symbol_table.lookup_symbol(first_child_node.value):
                is_assignment_or_call_stmt = True

        if is_assignment_or_call_stmt:
            id_node = first_child_node
            id_name = id_node.value
            id_rhs_instruccion_node = node.children[1]

            if id_rhs_instruccion_node.children[0].value == 'EQUALS': # Assignment
                exp_node = id_rhs_instruccion_node.children[1]
                eval_info = self._evaluate_expression(exp_node) # Returns {'reg': GPR, 'type': T} or {'freg': FPUreg, 'type': T} or {'value': L, 'type': T}

                if eval_info:
                    symbol_info = self.symbol_table.lookup_symbol(id_name, self.current_function_name)
                    if not symbol_info:
                         self._add_to_text(f"# Error: Assignment to undeclared variable '{id_name}'.")
                         # Release temp if any from eval_info
                         if 'reg' in eval_info and eval_info['reg'].startswith('$t'): self.release_temp_register(eval_info['reg'])
                         if 'freg' in eval_info and eval_info['freg'].startswith('$f'): self.release_temp_fpu_register(eval_info['freg'])
                         return

                    lhs_type = symbol_info['type']
                    rhs_type = eval_info['type']

                    # Handle type coercion: int = float (truncate), float = int (convert)
                    if lhs_type == 'int' and rhs_type == 'float':
                        # Truncate float to int: cvt.w.s $fd, $fs; mfc1 $td, $fd
                        fpu_src_reg = self._ensure_value_in_fpu_register(eval_info)
                        if fpu_src_reg:
                            temp_gpr = self.get_temp_register()
                            temp_fpu_for_cvt = self.get_temp_fpu_register() # Need a possibly different FPU reg for cvt.w.s result
                            self._add_to_text(f"cvt.w.s {temp_fpu_for_cvt}, {fpu_src_reg} # Convert float in {fpu_src_reg} to word in {temp_fpu_for_cvt}")
                            self._add_to_text(f"mfc1 {temp_gpr}, {temp_fpu_for_cvt}     # Move converted word to GPR {temp_gpr}")
                            self.release_temp_fpu_register(temp_fpu_for_cvt)
                            if fpu_src_reg.startswith('$f') and fpu_src_reg not in [temp_fpu_for_cvt]: self.release_temp_fpu_register(fpu_src_reg)
                            val_to_store_reg = temp_gpr
                            # Now val_to_store_reg (GPR) holds the integer part
                        else: # Error ensuring float in FPU reg
                            return
                    elif lhs_type == 'float' and rhs_type == 'int':
                        # Convert int to float: mtc1 $ts, $fd; cvt.s.w $fd, $fd
                        gpr_src_reg = self._ensure_value_in_register(eval_info) # Ensure int is in GPR
                        if gpr_src_reg:
                            val_to_store_freg = self.get_temp_fpu_register()
                            self._add_to_text(f"mtc1 {gpr_src_reg}, {val_to_store_freg}   # Move int from GPR {gpr_src_reg} to FPU {val_to_store_freg}")
                            self._add_to_text(f"cvt.s.w {val_to_store_freg}, {val_to_store_freg} # Convert word in FPU to float")
                            if gpr_src_reg.startswith('$t'): self.release_temp_register(gpr_src_reg)
                             # Now val_to_store_freg (FPU) holds the float
                        else: # Error ensuring int in GPR
                            return
                    elif lhs_type == 'float' and rhs_type == 'float':
                        val_to_store_freg = self._ensure_value_in_fpu_register(eval_info)
                        if not val_to_store_freg: return
                    else: # int = int, bool = bool, string = string (address)
                        val_to_store_reg = self._ensure_value_in_register(eval_info)
                        if not val_to_store_reg: return

                    # Store the (potentially coerced) value
                    if id_name in self.current_function_params:
                        offset = self.current_function_params[id_name]
                        if lhs_type == 'float': self._add_to_text(f"s.s {val_to_store_freg}, {offset}($fp)  # Store float to param '{id_name}'")
                        else: self._add_to_text(f"sw {val_to_store_reg}, {offset}($fp)  # Store to param '{id_name}'")
                    elif id_name in self.current_function_locals:
                        offset = self.current_function_locals[id_name]
                        if lhs_type == 'float': self._add_to_text(f"s.s {val_to_store_freg}, {offset}($fp)  # Store float to local '{id_name}'")
                        else: self._add_to_text(f"sw {val_to_store_reg}, {offset}($fp)  # Store to local '{id_name}'")
                    elif symbol_info.get('scope_attr') == 'global':
                        if lhs_type == 'float': self._add_to_text(f"s.s {val_to_store_freg}, {id_name}  # Store float to global '{id_name}'")
                        else: self._add_to_text(f"sw {val_to_store_reg}, {id_name}  # Store to global '{id_name}'")
                    else:
                         self._add_to_text(f"# Error: Variable '{id_name}' scope not identified for assignment.")

                    # Release temporary registers used for value or coercion
                    if 'val_to_store_reg' in locals() and val_to_store_reg and val_to_store_reg.startswith('$t'): self.release_temp_register(val_to_store_reg)
                    if 'val_to_store_freg' in locals() and val_to_store_freg and val_to_store_freg.startswith('$f'): self.release_temp_fpu_register(val_to_store_freg)

                else: # eval_info is None
                    self._add_to_text(f"# Error evaluating RHS expression for assignment to '{id_name}'.")

            elif id_rhs_instruccion_node.children[0].value == 'llamada_func':
                llamada_func_actual_node = id_rhs_instruccion_node.children[0]
                self._handle_function_call(id_name, llamada_func_actual_node, is_statement_call=True)
        else:
            self._visit(first_child_node)


    def _visit_print(self, node):
        # ... (remains mostly same, but ensure _ensure_value_in_register or _ensure_value_in_fpu_register is used)
        if len(node.children) == 4 and node.children[2].value == 'exp':
            exp_node = node.children[2]
            eval_info = self._evaluate_expression(exp_node)

            if eval_info:
                result_type = eval_info.get('type')

                if result_type == 'int' or result_type == 'bool':
                    val_reg = self._ensure_value_in_register(eval_info)
                    if val_reg:
                        self._add_to_text(f"move $a0, {val_reg}")
                        if val_reg.startswith('$t'): self.release_temp_register(val_reg)
                        self._add_to_text("li $v0, 1"); self._add_to_text("syscall")
                    else: self._add_to_text(f"# Error: Print could not get int/bool into GPR")
                elif result_type == 'string':
                    # String result from _evaluate_expression is either a label or address in GPR
                    if 'label' in eval_info:
                        self._add_to_text(f"la $a0, {eval_info['label']}")
                    elif 'reg' in eval_info:
                        self._add_to_text(f"move $a0, {eval_info['reg']}")
                        if eval_info['reg'].startswith('$t'): self.release_temp_register(eval_info['reg'])
                    else: self._add_to_text("# Error: String for print not in label or GPR")
                    self._add_to_text("li $v0, 4"); self._add_to_text("syscall")
                elif result_type == 'float':
                    fpu_val_reg = self._ensure_value_in_fpu_register(eval_info)
                    if fpu_val_reg:
                        self._add_to_text(f"mov.s $f12, {fpu_val_reg}")
                        if fpu_val_reg.startswith('$f') and fpu_val_reg != '$f12': self.release_temp_fpu_register(fpu_val_reg)
                        self._add_to_text(f"li $v0, 2"); self._add_to_text("syscall")
                    else: self._add_to_text(f"# Error: Print could not get float into FPU reg")
                else:
                    self._add_to_text(f"# Print for type {result_type} not fully implemented.")

                newline_label = self.add_string_literal("\\n")
                self._add_to_text(f"la $a0, {newline_label}")
                self._add_to_text("li $v0, 4"); self._add_to_text("syscall")
            else:
                self._add_to_text("# Error evaluating expression for print.")
        else:
            self._add_to_text("# Error: Malformed Print statement node.")


    def _ensure_value_in_fpu_register(self, eval_info):
        """Helper to load a float value into an FPU register."""
        if not eval_info or eval_info.get('type') != 'float':
            self._add_to_text(f"# Error: _ensure_value_in_fpu_register called with non-float or no info: {eval_info}")
            return None

        if 'freg' in eval_info: # Already in an FPU register
            return eval_info['freg']
        elif 'value' in eval_info: # Float literal
            freg = self.get_temp_fpu_register()
            self._add_to_text(f"li.s {freg}, {eval_info['value']}")
            return freg
        elif 'id_name' in eval_info: # Float variable
            var_name = eval_info['id_name']
            freg = self.get_temp_fpu_register()
            if var_name in self.current_function_params:
                offset = self.current_function_params[var_name]
                self._add_to_text(f"l.s {freg}, {offset}($fp)  # Load float param '{var_name}'")
            elif var_name in self.current_function_locals:
                offset = self.current_function_locals[var_name]
                self._add_to_text(f"l.s {freg}, {offset}($fp)  # Load float local '{var_name}'")
            else: # Global
                self._add_to_text(f"l.s {freg}, {var_name}  # Load float global '{var_name}'")
            return freg

        self._add_to_text(f"# Error: Cannot ensure float value is in FPU register for: {eval_info}")
        return None


    def _evaluate_expression(self, exp_node):
        return self._visit(exp_node)

    def _visit_exp(self, node):
        if node.children:
            return self._visit(node.children[0])
        return None

    def _visit_e(self, node): # E -> C E_rest (OR)
        if len(node.children) == 2:
            lhs_info = self._visit(node.children[0])
            if not lhs_info: return None
            return self._visit_e_rest(node.children[1], lhs_info)
        return None

    def _visit_e_rest(self, node, lhs_eval_info): # E_rest -> OR C E_rest | ε
        if node.children and node.children[0].value != 'ε': # OR C E_rest
            op_node = node.children[0] # Node('OR')
            # Ensure LHS is bool (0 or 1) in a GPR
            lhs_reg = self._ensure_value_in_register(lhs_eval_info)
            if not lhs_reg or lhs_eval_info.get('type') not in ['bool', 'int']:
                self._add_to_text("# Error: LHS of OR must be boolean/integer.")
                if lhs_reg and lhs_reg.startswith('$t'): self.release_temp_register(lhs_reg)
                return None

            rhs_eval_info = self._visit(node.children[1]) # Visit C for RHS
            if not rhs_eval_info:
                if lhs_reg.startswith('$t'): self.release_temp_register(lhs_reg)
                return None

            rhs_reg = self._ensure_value_in_register(rhs_eval_info)
            if not rhs_reg or rhs_eval_info.get('type') not in ['bool', 'int']:
                self._add_to_text("# Error: RHS of OR must be boolean/integer.")
                if lhs_reg.startswith('$t'): self.release_temp_register(lhs_reg)
                if rhs_reg and rhs_reg.startswith('$t'): self.release_temp_register(rhs_reg)
                return None

            self._add_to_text(f"or {lhs_reg}, {lhs_reg}, {rhs_reg}  # Logical OR")
            # Ensure result is 0 or 1 (optional, if `or` can produce other values with non-0/1 inputs)
            # self._add_to_text(f"snez {lhs_reg}, {lhs_reg} # Ensure 0 or 1 for boolean result")


            if rhs_reg.startswith('$t'): self.release_temp_register(rhs_reg)

            current_result_info = {'reg': lhs_reg, 'type': 'bool'}
            return self._visit_e_rest(node.children[2], current_result_info) # Pass to next E_rest
        return lhs_eval_info # Epsilon case

    def _visit_c(self, node): # C -> R C_rest (AND)
        if len(node.children) == 2:
            lhs_info = self._visit(node.children[0])
            if not lhs_info: return None
            return self._visit_c_rest(node.children[1], lhs_info)
        return None

    def _visit_c_rest(self, node, lhs_eval_info): # C_rest -> AND R C_rest | ε
        if node.children and node.children[0].value != 'ε': # AND R C_rest
            op_node = node.children[0] # Node('AND')
            lhs_reg = self._ensure_value_in_register(lhs_eval_info)
            if not lhs_reg or lhs_eval_info.get('type') not in ['bool', 'int']:
                self._add_to_text("# Error: LHS of AND must be boolean/integer.")
                if lhs_reg and lhs_reg.startswith('$t'): self.release_temp_register(lhs_reg)
                return None

            rhs_eval_info = self._visit(node.children[1]) # Visit R for RHS
            if not rhs_eval_info:
                if lhs_reg.startswith('$t'): self.release_temp_register(lhs_reg)
                return None

            rhs_reg = self._ensure_value_in_register(rhs_eval_info)
            if not rhs_reg or rhs_eval_info.get('type') not in ['bool', 'int']:
                self._add_to_text("# Error: RHS of AND must be boolean/integer.")
                if lhs_reg.startswith('$t'): self.release_temp_register(lhs_reg)
                if rhs_reg and rhs_reg.startswith('$t'): self.release_temp_register(rhs_reg)
                return None

            self._add_to_text(f"and {lhs_reg}, {lhs_reg}, {rhs_reg}  # Logical AND")
            # self._add_to_text(f"snez {lhs_reg}, {lhs_reg} # Ensure 0 or 1 for boolean result")

            if rhs_reg.startswith('$t'): self.release_temp_register(rhs_reg)

            current_result_info = {'reg': lhs_reg, 'type': 'bool'}
            return self._visit_c_rest(node.children[2], current_result_info)
        return lhs_eval_info


    def _visit_r(self, node): # R -> T R_rest (Relational Ops like EQ, LT, etc.)
        if len(node.children) == 2:
            lhs_info = self._visit(node.children[0]) # Result of T
            if not lhs_info: return None
            return self._visit_r_rest(node.children[1], lhs_info) # Pass to R_rest
        return None

    def _visit_r_rest(self, node, lhs_eval_info):
        # R_rest -> (EQ | NE | LT | GT | LE | GE) T R_rest | ε
        if node.children and node.children[0].value != 'ε': # Operator T R_rest
            op_node = node.children[0] # Node('EQ'), Node('LT'), etc.
            op_type_str = op_node.value.lower() # "eq", "lt"

            rhs_eval_info = self._visit(node.children[1]) # Evaluate T (RHS of comparison)
            if not rhs_eval_info:
                 # Release LHS if it was a temp GPR or FPU reg
                if 'reg' in lhs_eval_info and lhs_eval_info['reg'].startswith('$t'): self.release_temp_register(lhs_eval_info['reg'])
                if 'freg' in lhs_eval_info and lhs_eval_info['freg'].startswith('$f'): self.release_temp_fpu_register(lhs_eval_info['freg'])
                return None

            lhs_type = lhs_eval_info.get('type')
            rhs_type = rhs_eval_info.get('type')
            result_reg = self.get_temp_register() # For 0 or 1 result

            if (lhs_type == 'int' or lhs_type == 'bool') and \
               (rhs_type == 'int' or rhs_type == 'bool'):
                lhs_gpr = self._ensure_value_in_register(lhs_eval_info)
                rhs_gpr = self._ensure_value_in_register(rhs_eval_info)
                if not lhs_gpr or not rhs_gpr: # Error in loading
                    if lhs_gpr and lhs_gpr.startswith('$t'): self.release_temp_register(lhs_gpr)
                    if rhs_gpr and rhs_gpr.startswith('$t'): self.release_temp_register(rhs_gpr)
                    self.release_temp_register(result_reg)
                    return None

                # SPIM comparison instructions:
                comp_instr_map = {
                    "eq": "seq", "ne": "sne", "lt": "slt",
                    "le": "sle", "gt": "sgt", "ge": "sge"
                }
                spim_instr = comp_instr_map.get(op_type_str)
                if spim_instr:
                    self._add_to_text(f"{spim_instr} {result_reg}, {lhs_gpr}, {rhs_gpr}")
                else:
                    self._add_to_text(f"# Unknown integer comparison: {op_type_str}")
                    # Fallback or error

                if lhs_gpr.startswith('$t'): self.release_temp_register(lhs_gpr)
                if rhs_gpr.startswith('$t'): self.release_temp_register(rhs_gpr)

            elif lhs_type == 'float' and rhs_type == 'float':
                lhs_freg = self._ensure_value_in_fpu_register(lhs_eval_info)
                rhs_freg = self._ensure_value_in_fpu_register(rhs_eval_info)
                if not lhs_freg or not rhs_freg: # Error
                    if lhs_freg and lhs_freg.startswith('$f'): self.release_temp_fpu_register(lhs_freg)
                    if rhs_freg and rhs_freg.startswith('$f'): self.release_temp_fpu_register(rhs_freg)
                    self.release_temp_register(result_reg)
                    return None

                # c.eq.s, c.lt.s, c.le.s (no direct c.gt/ge, use inverse)
                # Sets FPU condition flag (e.g. flag 0)
                true_label = self._new_control_label("comp_true")
                end_comp_label = self._new_control_label("comp_end")

                if op_type_str == "eq": self._add_to_text(f"c.eq.s {lhs_freg}, {rhs_freg}")
                elif op_type_str == "ne": # Implement as NOT (c.eq.s then check false) or use two branches
                                     self._add_to_text(f"c.eq.s {lhs_freg}, {rhs_freg}"); # Check bc1f for NE
                elif op_type_str == "lt": self._add_to_text(f"c.lt.s {lhs_freg}, {rhs_freg}")
                elif op_type_str == "le": self._add_to_text(f"c.le.s {lhs_freg}, {rhs_freg}")
                elif op_type_str == "gt": self._add_to_text(f"c.lt.s {rhs_freg}, {lhs_freg}") # b > a is same as a < b
                elif op_type_str == "ge": self._add_to_text(f"c.le.s {rhs_freg}, {lhs_freg}") # b >= a is same as a <= b
                else: self._add_to_text(f"# Unknown float comparison: {op_type_str}")

                if op_type_str == "ne": # Special handling for NE with bc1f
                    self._add_to_text(f"bc1f {true_label}  # Branch if NOT equal (flag false)")
                else:
                    self._add_to_text(f"bc1t {true_label}  # Branch if condition true")

                self._add_to_text(f"li {result_reg}, 0          # False case")
                self._add_to_text(f"j {end_comp_label}")
                self._add_to_text(f"{true_label}:")
                self._add_to_text(f"li {result_reg}, 1          # True case")
                self._add_to_text(f"{end_comp_label}:")

                if lhs_freg.startswith('$f'): self.release_temp_fpu_register(lhs_freg)
                if rhs_freg.startswith('$f'): self.release_temp_fpu_register(rhs_freg)

            # Add int-float / float-int comparisons with coercion here if needed
            else:
                self._add_to_text(f"# Comparison between {lhs_type} and {rhs_type} not implemented.")
                # Release GPR/FPU temps if acquired
                self.release_temp_register(result_reg)
                return None # Error or unhandled types

            current_result_info = {'reg': result_reg, 'type': 'bool'}
            return self._visit_r_rest(node.children[2], current_result_info) # Pass to next R_rest
        return lhs_eval_info # Epsilon case


    def _visit_t(self, node): # T -> F T_rest (+, -)
        if len(node.children) == 2:
            lhs_info = self._visit(node.children[0])
            if not lhs_info: return None
            return self._visit_t_rest(node.children[1], lhs_info)
        return None

    def _ensure_value_in_register(self, eval_info): # GPR
        if not eval_info: return None
        if 'reg' in eval_info and eval_info['reg']: # Already in GPR
            return eval_info['reg']
        elif 'value' in eval_info: # Immediate int/bool
            if eval_info['type'] == 'int' or eval_info['type'] == 'bool':
                reg = self.get_temp_register()
                self._add_to_text(f"li {reg}, {eval_info['value']}")
                return reg
        elif 'id_name' in eval_info:
            var_name = eval_info['id_name']
            var_type = eval_info['type']
            reg = self.get_temp_register()

            # Determine if var is param, local, or global to load correctly
            # This logic needs to be robust using self.current_function_name for context
            symbol_details_scoped = self.symbol_table.lookup_symbol(var_name, self.current_function_name)

            if var_name in self.current_function_params:
                offset = self.current_function_params[var_name]
                self._add_to_text(f"lw {reg}, {offset}($fp)  # Load parameter '{var_name}'")
            elif var_name in self.current_function_locals:
                offset = self.current_function_locals[var_name]
                if var_type == 'int' or var_type == 'bool' or var_type == 'string':
                    self._add_to_text(f"lw {reg}, {offset}($fp)  # Load local var '{var_name}'")
                else: # e.g. float, should use FPU path
                    self._add_to_text(f"# GPR load for local var '{var_name}' of type {var_type} not supported here.")
                    self.release_temp_register(reg); return None
            elif symbol_details_scoped and symbol_details_scoped.get('scope_attr') == 'global':
                if var_type == 'int' or var_type == 'bool' or var_type == 'string':
                    self._add_to_text(f"lw {reg}, {var_name}  # Load global var '{var_name}'")
                else: # e.g. float
                    self._add_to_text(f"# GPR load for global var '{var_name}' of type {var_type} not supported here.")
                    self.release_temp_register(reg); return None
            else: # Not found or other issue
                self._add_to_text(f"# Error: Variable '{var_name}' not found for GPR load.")
                self.release_temp_register(reg); return None
            return reg

        # If eval_info was for a float in an FPU reg, this function shouldn't be called
        # or it should handle moving from FPU to GPR if that's intended (e.g. for int cast)
        self._add_to_text(f"# Error: Cannot ensure value is in GPR for: {eval_info}")
        if 'reg' in eval_info and eval_info['reg'].startswith('$t'): self.release_temp_register(eval_info['reg'])
        return None


    def _visit_t_rest(self, node, lhs_eval_info): # T_rest -> (PLUS | MINUS) F T_rest | ε
        if node.children and node.children[0].value != 'ε': # (PLUS | MINUS) F T_rest
            op_node = node.children[0]
            op_type_str = op_node.value.upper() # PLUS or MINUS

            rhs_eval_info = self._visit(node.children[1]) # Evaluate F (RHS)
            if not rhs_eval_info: # Error in RHS
                # Release LHS if temp
                if 'reg' in lhs_eval_info and lhs_eval_info['reg'].startswith('$t'): self.release_temp_register(lhs_eval_info['reg'])
                if 'freg' in lhs_eval_info and lhs_eval_info['freg'].startswith('$f'): self.release_temp_fpu_register(lhs_eval_info['freg'])
                return None

            lhs_type = lhs_eval_info.get('type')
            rhs_type = rhs_eval_info.get('type')
            result_info = None

            if (lhs_type == 'int' or lhs_type == 'bool') and (rhs_type == 'int' or rhs_type == 'bool'):
                lhs_gpr = self._ensure_value_in_register(lhs_eval_info)
                rhs_gpr = self._ensure_value_in_register(rhs_eval_info)
                if not lhs_gpr or not rhs_gpr: # Error loading to GPR
                    if lhs_gpr and lhs_gpr.startswith('$t'): self.release_temp_register(lhs_gpr)
                    if rhs_gpr and rhs_gpr.startswith('$t'): self.release_temp_register(rhs_gpr)
                    return None

                op_instr = "add" if op_type_str == 'PLUS' else "sub"
                self._add_to_text(f"{op_instr} {lhs_gpr}, {lhs_gpr}, {rhs_gpr}")
                if rhs_gpr.startswith('$t'): self.release_temp_register(rhs_gpr)
                result_info = {'reg': lhs_gpr, 'type': 'int'}

            elif lhs_type == 'float' and rhs_type == 'float':
                lhs_freg = self._ensure_value_in_fpu_register(lhs_eval_info)
                rhs_freg = self._ensure_value_in_fpu_register(rhs_eval_info)
                if not lhs_freg or not rhs_freg: # Error loading to FPU
                    if lhs_freg and lhs_freg.startswith('$f'): self.release_temp_fpu_register(lhs_freg)
                    if rhs_freg and rhs_freg.startswith('$f'): self.release_temp_fpu_register(rhs_freg)
                    return None

                fpu_op_instr = "add.s" if op_type_str == 'PLUS' else "sub.s"
                self._add_to_text(f"{fpu_op_instr} {lhs_freg}, {lhs_freg}, {rhs_freg}")
                if rhs_freg.startswith('$f'): self.release_temp_fpu_register(rhs_freg) # Release temp FPU reg for RHS
                result_info = {'freg': lhs_freg, 'type': 'float'}

            # Mixed type: float + int or int + float (promote int to float)
            elif (lhs_type == 'float' and rhs_type == 'int') or \
                 (lhs_type == 'int' and rhs_type == 'float'):

                fpu_op_instr = "add.s" if op_type_str == 'PLUS' else "sub.s"

                op1_freg = None
                op2_freg = None

                if lhs_type == 'float':
                    op1_freg = self._ensure_value_in_fpu_register(lhs_eval_info)
                else: # lhs is int, convert to float
                    lhs_gpr = self._ensure_value_in_register(lhs_eval_info)
                    if lhs_gpr:
                        op1_freg = self.get_temp_fpu_register()
                        self._add_to_text(f"mtc1 {lhs_gpr}, {op1_freg}")
                        self._add_to_text(f"cvt.s.w {op1_freg}, {op1_freg}")
                        if lhs_gpr.startswith('$t'): self.release_temp_register(lhs_gpr)
                    else: return None # Error

                if rhs_type == 'float':
                    op2_freg = self._ensure_value_in_fpu_register(rhs_eval_info)
                else: # rhs is int, convert to float
                    rhs_gpr = self._ensure_value_in_register(rhs_eval_info)
                    if rhs_gpr:
                        op2_freg = self.get_temp_fpu_register()
                        self._add_to_text(f"mtc1 {rhs_gpr}, {op2_freg}")
                        self._add_to_text(f"cvt.s.w {op2_freg}, {op2_freg}")
                        if rhs_gpr.startswith('$t'): self.release_temp_register(rhs_gpr)
                    else: # Error, release op1_freg if it was temp
                        if op1_freg and op1_freg.startswith('$f'): self.release_temp_fpu_register(op1_freg)
                        return None

                if not op1_freg or not op2_freg: # Should not happen if above logic is correct
                    if op1_freg and op1_freg.startswith('$f'): self.release_temp_fpu_register(op1_freg)
                    if op2_freg and op2_freg.startswith('$f'): self.release_temp_fpu_register(op2_freg)
                    return None

                self._add_to_text(f"{fpu_op_instr} {op1_freg}, {op1_freg}, {op2_freg}")
                if op2_freg.startswith('$f'): self.release_temp_fpu_register(op2_freg)
                result_info = {'freg': op1_freg, 'type': 'float'}
            else:
                self._add_to_text(f"# Unsupported types for {op_type_str}: {lhs_type}, {rhs_type}")
                # Release any temps acquired by _ensure_value_in_register
                return None

            return self._visit_t_rest(node.children[2], result_info) # Pass to next T_rest
        return lhs_eval_info # Epsilon case


    def _visit_f(self, node): # F -> A F_rest (*, / , %)
        if len(node.children) == 2:
            lhs_info = self._visit(node.children[0])
            if not lhs_info: return None
            return self._visit_f_rest(node.children[1], lhs_info)
        return None

    def _visit_f_rest(self, node, lhs_eval_info): # F_rest -> (TIMES | DIVIDE | MOD) A F_rest | ε
        if node.children and node.children[0].value != 'ε':
            op_node = node.children[0]
            op_type_str = op_node.value.upper() # TIMES, DIVIDE, MOD

            rhs_eval_info = self._visit(node.children[1]) # Evaluate A (RHS)
            if not rhs_eval_info:
                # Release LHS if temp
                if 'reg' in lhs_eval_info and lhs_eval_info['reg'].startswith('$t'): self.release_temp_register(lhs_eval_info['reg'])
                if 'freg' in lhs_eval_info and lhs_eval_info['freg'].startswith('$f'): self.release_temp_fpu_register(lhs_eval_info['freg'])
                return None

            lhs_type = lhs_eval_info.get('type')
            rhs_type = rhs_eval_info.get('type')
            result_info = None

            if (lhs_type == 'int' or lhs_type == 'bool') and (rhs_type == 'int' or rhs_type == 'bool'):
                lhs_gpr = self._ensure_value_in_register(lhs_eval_info)
                rhs_gpr = self._ensure_value_in_register(rhs_eval_info)
                if not lhs_gpr or not rhs_gpr: # Error loading
                    if lhs_gpr and lhs_gpr.startswith('$t'): self.release_temp_register(lhs_gpr)
                    if rhs_gpr and rhs_gpr.startswith('$t'): self.release_temp_register(rhs_gpr)
                    return None

                if op_type_str == 'TIMES':
                    self._add_to_text(f"mult {lhs_gpr}, {rhs_gpr}")
                    self._add_to_text(f"mflo {lhs_gpr}  # Result of multiplication in $lo")
                elif op_type_str == 'DIVIDE':
                    self._add_to_text(f"div {lhs_gpr}, {rhs_gpr}")
                    self._add_to_text(f"mflo {lhs_gpr}  # Quotient in $lo")
                elif op_type_str == 'MOD':
                    self._add_to_text(f"div {lhs_gpr}, {rhs_gpr}")
                    self._add_to_text(f"mfhi {lhs_gpr}  # Remainder in $hi")
                else: self._add_to_text(f"# Unknown GPR F_rest op: {op_type_str}")

                if rhs_gpr.startswith('$t'): self.release_temp_register(rhs_gpr)
                result_info = {'reg': lhs_gpr, 'type': 'int'}

            elif lhs_type == 'float' and rhs_type == 'float':
                lhs_freg = self._ensure_value_in_fpu_register(lhs_eval_info)
                rhs_freg = self._ensure_value_in_fpu_register(rhs_eval_info)
                if not lhs_freg or not rhs_freg: # Error
                    if lhs_freg and lhs_freg.startswith('$f'): self.release_temp_fpu_register(lhs_freg)
                    if rhs_freg and rhs_freg.startswith('$f'): self.release_temp_fpu_register(rhs_freg)
                    return None

                if op_type_str == 'TIMES': self._add_to_text(f"mul.s {lhs_freg}, {lhs_freg}, {rhs_freg}")
                elif op_type_str == 'DIVIDE': self._add_to_text(f"div.s {lhs_freg}, {lhs_freg}, {rhs_freg}")
                elif op_type_str == 'MOD': self._add_to_text(f"# MOD not directly supported for floats in SPIM like this")
                else: self._add_to_text(f"# Unknown FPU F_rest op: {op_type_str}")

                if rhs_freg.startswith('$f'): self.release_temp_fpu_register(rhs_freg)
                result_info = {'freg': lhs_freg, 'type': 'float'}

            # Mixed type float/int for *, /
            elif (lhs_type == 'float' and rhs_type == 'int') or \
                 (lhs_type == 'int' and rhs_type == 'float'):
                op1_freg, op2_freg = None, None
                temp_gpr_for_lhs_int = None # Keep track if we used a GPR for int that needs release
                temp_gpr_for_rhs_int = None

                if lhs_type == 'float': op1_freg = self._ensure_value_in_fpu_register(lhs_eval_info)
                else: # lhs is int
                    temp_gpr_for_lhs_int = self._ensure_value_in_register(lhs_eval_info)
                    if temp_gpr_for_lhs_int:
                        op1_freg = self.get_temp_fpu_register()
                        self._add_to_text(f"mtc1 {temp_gpr_for_lhs_int}, {op1_freg}")
                        self._add_to_text(f"cvt.s.w {op1_freg}, {op1_freg}")
                    else: return None

                if rhs_type == 'float': op2_freg = self._ensure_value_in_fpu_register(rhs_eval_info)
                else: # rhs is int
                    temp_gpr_for_rhs_int = self._ensure_value_in_register(rhs_eval_info)
                    if temp_gpr_for_rhs_int:
                        op2_freg = self.get_temp_fpu_register()
                        self._add_to_text(f"mtc1 {temp_gpr_for_rhs_int}, {op2_freg}")
                        self._add_to_text(f"cvt.s.w {op2_freg}, {op2_freg}")
                    else: # Error, release op1_freg if temp
                        if op1_freg and op1_freg.startswith('$f'): self.release_temp_fpu_register(op1_freg)
                        if temp_gpr_for_lhs_int and temp_gpr_for_lhs_int.startswith('$t'): self.release_temp_register(temp_gpr_for_lhs_int)
                        return None

                if not op1_freg or not op2_freg: # Should not happen
                    if op1_freg and op1_freg.startswith('$f'): self.release_temp_fpu_register(op1_freg)
                    if op2_freg and op2_freg.startswith('$f'): self.release_temp_fpu_register(op2_freg)
                    if temp_gpr_for_lhs_int and temp_gpr_for_lhs_int.startswith('$t'): self.release_temp_register(temp_gpr_for_lhs_int)
                    if temp_gpr_for_rhs_int and temp_gpr_for_rhs_int.startswith('$t'): self.release_temp_register(temp_gpr_for_rhs_int)
                    return None

                if op_type_str == 'TIMES': self._add_to_text(f"mul.s {op1_freg}, {op1_freg}, {op2_freg}")
                elif op_type_str == 'DIVIDE': self._add_to_text(f"div.s {op1_freg}, {op1_freg}, {op2_freg}")
                else: self._add_to_text(f"# MOD not supported for mixed float/int.")

                if temp_gpr_for_lhs_int and temp_gpr_for_lhs_int.startswith('$t'): self.release_temp_register(temp_gpr_for_lhs_int)
                if temp_gpr_for_rhs_int and temp_gpr_for_rhs_int.startswith('$t'): self.release_temp_register(temp_gpr_for_rhs_int)
                if op2_freg.startswith('$f'): self.release_temp_fpu_register(op2_freg)
                result_info = {'freg': op1_freg, 'type': 'float'}
            else:
                self._add_to_text(f"# Unsupported types for {op_type_str} in F_rest: {lhs_type}, {rhs_type}")
                return None

            return self._visit_f_rest(node.children[2], result_info) # Pass to next F_rest
        return lhs_eval_info # Epsilon case


    def _visit_a(self, node):
        atom = node.children[0]

        if atom.value == 'LPAREN':
            if len(node.children) == 3 and node.children[1].value == 'exp':
                return self._visit(node.children[1])
            else:
                self._add_to_text("# Error: Malformed parenthesized expression in A.")
                return None

        if isinstance(atom.value, int):
            return {'value': atom.value, 'type': 'int'}

        if isinstance(atom.value, str):
            if atom.value == "true":
                return {'value': 1, 'type': 'bool'}
            if atom.value == "false":
                return {'value': 0, 'type': 'bool'}

            is_func_call = len(node.children) > 1 and node.children[1].value == 'llamada_func'
            if not is_func_call:
                symbol_info = self.symbol_table.lookup_symbol(atom.value, self.current_function_name)
                if symbol_info:
                    return {'id_name': atom.value, 'type': symbol_info['type']}
                else:
                    label = self.add_string_literal(atom.value)
                    return {'label': label, 'type': 'string'}
            else:
                return self._handle_function_call(atom.value, node.children[1], is_statement_call=False)

        if isinstance(atom.value, float):
            # For an expression, load float literal into a temporary FPU register
            freg = self.get_temp_fpu_register()
            self._add_to_text(f"li.s {freg}, {atom.value}")
            return {'freg': freg, 'type': 'float'}

        self._add_to_text(f"# Unhandled atom in A: {atom.value} (type: {type(atom.value).__name__})")
        return None

    def _visit_int_literal(self, node_with_int_value): # Called by dispatcher
        return {'value': node_with_int_value.value, 'type': 'int'}

    def _visit_float_literal(self, node_with_float_value): # Called by dispatcher
        freg = self.get_temp_fpu_register()
        self._add_to_text(f"li.s {freg}, {node_with_float_value.value}")
        return {'freg': freg, 'type': 'float'}


    def _visit_declaracion(self, node):
        id_node = node.children[1]
        inicializacion_node = node.children[2]
        var_name = id_node.value

        if var_name in self.current_function_locals:
            if inicializacion_node.children and inicializacion_node.children[0].value != 'ε':
                exp_node = inicializacion_node.children[1]
                eval_info = self._evaluate_expression(exp_node)

                if eval_info:
                    var_symbol = self.symbol_table.lookup_symbol(var_name, self.current_function_name)
                    lhs_type = var_symbol['type'] if var_symbol else 'unknown'
                    rhs_type = eval_info.get('type')

                    offset = self.current_function_locals[var_name]

                    if lhs_type == 'float':
                        fpu_val_reg = self._ensure_value_in_fpu_register(eval_info) # Handles int->float coercion too
                        if fpu_val_reg:
                            self._add_to_text(f"s.s {fpu_val_reg}, {offset}($fp)  # Initialize local float var '{var_name}'")
                            if fpu_val_reg.startswith('$f'): self.release_temp_fpu_register(fpu_val_reg)
                        else: self._add_to_text(f"# Error getting float value for initializing '{var_name}'")
                    elif lhs_type == 'int' or lhs_type == 'bool' or lhs_type == 'string':
                        gpr_val_reg = self._ensure_value_in_register(eval_info) # Handles float->int coercion
                        if gpr_val_reg:
                            self._add_to_text(f"sw {gpr_val_reg}, {offset}($fp)  # Initialize local var '{var_name}'")
                            if gpr_val_reg.startswith('$t'): self.release_temp_register(gpr_val_reg)
                        else: self._add_to_text(f"# Error getting GPR value for initializing '{var_name}'")
                    else:
                         self._add_to_text(f"# Init for local var '{var_name}' of type {lhs_type} not fully done.")
                else:
                    self._add_to_text(f"# Error evaluating initialization expression for '{var_name}'.")

    def _visit_id_rhs_instruccion(self, node):
        pass

    def _visit_id(self, node):
        var_name = node.value
        symbol = self.symbol_table.lookup_symbol(var_name, self.current_function_name)
        if symbol:
            return {'id_name': var_name, 'type': symbol['type']}
        else:
            self._add_to_text(f"# Error: Undeclared ID '{var_name}' encountered by _visit_id.")
            return None

    def _visit_plus(self, node):
        return None
    def _visit_op_eq(self, node): return None # For operators if they become visitable nodes
    def _visit_op_ne(self, node): return None
    def _visit_op_lt(self, node): return None
    def _visit_op_le(self, node): return None
    def _visit_op_gt(self, node): return None
    def _visit_op_ge(self, node): return None


    def _visit_return(self, node):
        exp_opt_node = node.children[0] if node.children else None

        if exp_opt_node and exp_opt_node.children and exp_opt_node.children[0].value != 'ε':
            exp_node_to_eval = exp_opt_node.children[0]
            eval_info = self._evaluate_expression(exp_node_to_eval)
            if eval_info:
                result_type = eval_info.get('type')
                if result_type == 'int' or result_type == 'bool' or result_type == 'string':
                    val_reg = self._ensure_value_in_register(eval_info)
                    if val_reg:
                        self._add_to_text(f"move $v0, {val_reg}")
                        if val_reg.startswith('$t'): self.release_temp_register(val_reg)
                    else:
                         self._add_to_text("# Error: Could not get return value into a register for $v0")
                elif result_type == 'float':
                    fpu_val_reg = self._ensure_value_in_fpu_register(eval_info)
                    if fpu_val_reg:
                        self._add_to_text(f"mov.s $f0, {fpu_val_reg}")
                        if fpu_val_reg.startswith('$f') and fpu_val_reg != '$f0': self.release_temp_fpu_register(fpu_val_reg)
                    else:
                        self._add_to_text(f"# Error: Float return value not in FPU register from expression.")
                else:
                    self._add_to_text(f"# Error: Cannot get return value of type {result_type} into $v0/$f0.")
            else:
                self._add_to_text("# Error evaluating return expression.")

        if self.current_function_return_label:
            self._add_to_text(f"j {self.current_function_return_label}  # Jump to function epilogue")
        else:
             self._add_to_text(f"# Error: No return label for function {self.current_function_name}")


    def _handle_function_call(self, func_name, llamada_func_node, is_statement_call):
        self._add_to_text(f"# --- Call to function {func_name} ---")

        arg_nodes = []
        total_arg_size = 0

        if llamada_func_node.children and llamada_func_node.children[0].value != 'ε':
            lista_args_node = llamada_func_node.children[1]

            current_arg_list_part = lista_args_node
            while current_arg_list_part and current_arg_list_part.children and \
                  current_arg_list_part.children[0].value != 'ε':
                if current_arg_list_part.value == 'lista_args':
                    arg_nodes.append(current_arg_list_part.children[0])
                    current_arg_list_part = current_arg_list_part.children[1]
                elif current_arg_list_part.value == 'lista_args_rest':
                    arg_nodes.append(current_arg_list_part.children[1])
                    current_arg_list_part = current_arg_list_part.children[2]
                else: break

        self._add_to_text(f"# Evaluating and pushing arguments for {func_name}")
        # Store argument evaluation results temporarily if they involve FPU regs that need to be pushed by GPRs
        evaluated_args_for_stack = []
        for arg_exp_node in reversed(arg_nodes): # Evaluate in source order, then push in reverse
            eval_info = self._evaluate_expression(arg_exp_node)
            evaluated_args_for_stack.append(eval_info) # Store eval_info

        for eval_info in reversed(evaluated_args_for_stack): # Now push in reverse order
            if not eval_info:
                self._add_to_text(f"# Error evaluating argument for call to {func_name}")
                continue

            arg_type = eval_info.get('type')
            self._add_to_text(f"addi $sp, $sp, -4       # Make space for arg")
            if arg_type == 'float':
                fpu_reg = self._ensure_value_in_fpu_register(eval_info)
                if fpu_reg:
                    self._add_to_text(f"s.s {fpu_reg}, 0($sp)      # Push float arg for {func_name}")
                    if fpu_reg.startswith('$f') and fpu_reg != '$f0' and fpu_reg != '$f12': self.release_temp_fpu_register(fpu_reg)
                else: self._add_to_text(f"# Error getting float arg into FPU reg for {func_name}")
            else: # int, bool, string address
                gpr_reg = self._ensure_value_in_register(eval_info)
                if gpr_reg:
                    self._add_to_text(f"sw {gpr_reg}, 0($sp)      # Push arg for {func_name}")
                    if gpr_reg.startswith('$t'): self.release_temp_register(gpr_reg)
                else: self._add_to_text(f"# Error getting arg into GPR for {func_name}")
            total_arg_size += 4

        self._add_to_text(f"jal {func_name}                 # Call function")

        if total_arg_size > 0:
            self._add_to_text(f"addi $sp, $sp, {total_arg_size}  # Pop arguments for {func_name}")

        func_symbol_info = self.symbol_table.lookup_symbol(func_name)
        return_type = "void"
        if func_symbol_info and func_symbol_info['type'].startswith("FUNCTION"):
            type_part = func_symbol_info['type'].split(' -> ')[-1]
            type_mapping_simple = {'INT': 'int', 'FLOAT': 'float', 'BOOL': 'bool', 'STRING': 'string', 'VOID': 'void'}
            return_type = type_mapping_simple.get(type_part.upper(), "unknown_return_type")

        if is_statement_call or return_type == "void":
            return {'type': 'void'}
        else:
            if return_type == 'int' or return_type == 'bool' or return_type == 'string':
                dest_reg = self.get_temp_register()
                self._add_to_text(f"move {dest_reg}, $v0          # Move return value of {func_name} to temp")
                return {'reg': dest_reg, 'type': return_type}
            elif return_type == 'float':
                dest_freg = self.get_temp_fpu_register()
                self._add_to_text(f"mov.s {dest_freg}, $f0     # Move float return value")
                return {'freg': dest_freg, 'type': 'float'}
            else:
                self._add_to_text(f"# Unknown return type '{return_type}' for function {func_name} in expression")
                return {'type': 'unknown_return_type'}

    # --- Control Flow Visitors ---
    def _visit_if(self, node):
        if len(node.children) != 6:
            self._add_to_text("# Error: Malformed If statement node")
            return

        exp_node = node.children[2]
        bloque_if_node = node.children[4]
        else_node = node.children[5]

        else_label = self._new_control_label("if_else")
        end_if_label = self._new_control_label("if_end")

        cond_eval_info = self._evaluate_expression(exp_node)
        if not cond_eval_info:
            self._add_to_text("# Error evaluating If condition")
            return

        # For IF conditions, result must be boolean (0 or 1) in a GPR
        cond_gpr = self._ensure_value_in_register(cond_eval_info) # This handles float->int if cond was float comparison
        if not cond_gpr:
            self._add_to_text("# Error getting If condition into GPR")
            # Release FPU if cond_eval_info was float
            if 'freg' in cond_eval_info and cond_eval_info['freg'].startswith('$f'): self.release_temp_fpu_register(cond_eval_info['freg'])
            return

        self._add_to_text(f"beqz {cond_gpr}, {else_label}  # Branch to else if condition is false")
        if cond_gpr.startswith('$t'): self.release_temp_register(cond_gpr)

        self._visit(bloque_if_node)
        self._add_to_text(f"j {end_if_label}          # Jump to end of if-else")

        self._add_to_text(f"{else_label}:")
        self._visit(else_node)

        self._add_to_text(f"{end_if_label}:")


    def _visit_else(self, node):
        if node.children and node.children[0].value != 'ε':
            if len(node.children) == 2 and node.children[0].value.upper() == 'ELSE':
                bloque_node = node.children[1]
                self._visit(bloque_node)


    def _visit_while(self, node):
        if len(node.children) != 5:
            self._add_to_text("# Error: Malformed While statement node")
            return

        exp_node = node.children[2]
        bloque_node = node.children[4]

        start_while_label = self._new_control_label("while_start")
        end_while_label = self._new_control_label("while_end")

        self._add_to_text(f"{start_while_label}:")

        cond_eval_info = self._evaluate_expression(exp_node)
        if not cond_eval_info:
            self._add_to_text("# Error evaluating While condition")
            return

        cond_gpr = self._ensure_value_in_register(cond_eval_info) # Handles float comparisons returning 0/1 in GPR
        if not cond_gpr:
            self._add_to_text("# Error getting While condition into GPR")
            if 'freg' in cond_eval_info and cond_eval_info['freg'].startswith('$f'): self.release_temp_fpu_register(cond_eval_info['freg'])
            return

        self._add_to_text(f"beqz {cond_gpr}, {end_while_label}  # Branch to end if condition is false")
        if cond_gpr.startswith('$t'): self.release_temp_register(cond_gpr)

        self._visit(bloque_node)
        self._add_to_text(f"j {start_while_label}          # Jump back to while condition")

        self._add_to_text(f"{end_while_label}:")


    def _visit_for(self, node):
        if len(node.children) != 9:
            self._add_to_text("# Error: Malformed For statement node")
            return

        init_assignment_node = node.children[2]
        exp_node = node.children[4]
        update_assignment_node = node.children[6]
        bloque_node = node.children[8]

        for_start_label = self._new_control_label("for_start")
        for_update_label = self._new_control_label("for_update")
        for_end_label = self._new_control_label("for_end")

        self._visit(init_assignment_node)

        self._add_to_text(f"{for_start_label}:")
        if exp_node.value != 'ε':
            cond_eval_info = self._evaluate_expression(exp_node)
            if not cond_eval_info:
                self._add_to_text("# Error evaluating For loop condition")
                return
            cond_gpr = self._ensure_value_in_register(cond_eval_info)
            if not cond_gpr:
                self._add_to_text("# Error getting For condition into GPR")
                if 'freg' in cond_eval_info and cond_eval_info['freg'].startswith('$f'): self.release_temp_fpu_register(cond_eval_info['freg'])
                return
            self._add_to_text(f"beqz {cond_gpr}, {for_end_label}  # Exit for loop if condition false")
            if cond_gpr.startswith('$t'): self.release_temp_register(cond_gpr)

        self._visit(bloque_node)

        self._add_to_text(f"{for_update_label}:")
        self._visit(update_assignment_node)

        self._add_to_text(f"j {for_start_label}              # Jump back to for condition check")
        self._add_to_text(f"{for_end_label}:")


    def _visit_for_assignment(self, node): # Largely same as _visit_instruccion assignment part
        if len(node.children) != 3:
            self._add_to_text("# Error: Malformed for_assignment node")
            return

        id_node = node.children[0]
        exp_node = node.children[2]
        var_name = id_node.value

        eval_info = self._evaluate_expression(exp_node)
        if not eval_info:
            self._add_to_text(f"# Error evaluating RHS for for_assignment of '{var_name}'")
            return

        symbol_info = self.symbol_table.lookup_symbol(var_name, self.current_function_name)
        if not symbol_info:
            self._add_to_text(f"# Error: Variable '{var_name}' in for_assignment not declared.")
            if 'reg' in eval_info and eval_info['reg'].startswith('$t'): self.release_temp_register(eval_info['reg'])
            if 'freg' in eval_info and eval_info['freg'].startswith('$f'): self.release_temp_fpu_register(eval_info['freg'])
            return

        lhs_type = symbol_info['type']
        # Coercion and storing logic similar to _visit_instruccion assignment
        if lhs_type == 'float':
            val_to_store_freg = self._ensure_value_in_fpu_register(eval_info)
            if not val_to_store_freg: return
            if var_name in self.current_function_locals: self._add_to_text(f"s.s {val_to_store_freg}, {self.current_function_locals[var_name]}($fp)")
            elif var_name in self.current_function_params: self._add_to_text(f"s.s {val_to_store_freg}, {self.current_function_params[var_name]}($fp)")
            else: self._add_to_text(f"s.s {val_to_store_freg}, {var_name}") # Global
            if val_to_store_freg.startswith('$f'): self.release_temp_fpu_register(val_to_store_freg)
        else: # int, bool, string
            val_to_store_reg = self._ensure_value_in_register(eval_info)
            if not val_to_store_reg: return
            if var_name in self.current_function_locals: self._add_to_text(f"sw {val_to_store_reg}, {self.current_function_locals[var_name]}($fp)")
            elif var_name in self.current_function_params: self._add_to_text(f"sw {val_to_store_reg}, {self.current_function_params[var_name]}($fp)")
            else: self._add_to_text(f"sw {val_to_store_reg}, {var_name}") # Global
            if val_to_store_reg.startswith('$t'): self.release_temp_register(val_to_store_reg)


if __name__ == '__main__':
    class MockSymbolTable:
        def __init__(self):
            self.all_created_scopes_data = [
                {
                    'name': 'global',
                    'symbols': {
                        'g_var_int': {'type': 'int', 'line': 1, 'scope_attr': 'global'},
                        'g_var_float': {'type': 'float', 'line': 1, 'scope_attr': 'global'},
                        'message': {'type': 'string', 'line': 4, 'scope_attr': 'global'},
                        'add': {
                            'type': 'FUNCTION (INT, INT) -> INT', 'line': 5, 'scope_attr': 'global',
                            'param_types': ['int', 'int'], 'param_names_ordered': ['a', 'b']
                        },
                         'test': {
                            'type': 'FUNCTION () -> VOID', 'line': 10, 'scope_attr': 'global',
                            'param_types': [], 'param_names_ordered': []
                        },
                        'processFloat': {
                            'type': 'FUNCTION (FLOAT) -> FLOAT', 'line': 15, 'scope_attr': 'global',
                            'param_types': ['float'], 'param_names_ordered': ['x']
                        }
                    }
                },
                {
                    'name': 'main',
                    'symbols': {
                        'localVar1': {'type': 'int', 'line': 2, 'scope_attr': 'main'},
                        'res': {'type': 'int', 'line': 3, 'scope_attr': 'main'},
                        'f_res': {'type': 'float', 'line': 4, 'scope_attr': 'main'},
                        'myFloat': {'type': 'float', 'line': 5, 'scope_attr': 'main'}
                    }
                },
                {
                    'name': 'add',
                    'symbols': {
                        'a': {'type': 'int', 'line': 5, 'scope_attr': 'add'},
                        'b': {'type': 'int', 'line': 5, 'scope_attr': 'add'},
                        'sum_local': {'type': 'int', 'line': 6, 'scope_attr': 'add'}
                    }
                },
                 {
                    'name': 'test',
                    'symbols': { 'x': {'type': 'int', 'line': 11, 'scope_attr': 'test'} }
                },
                {
                    'name': 'processFloat',
                    'symbols': {
                        'x': {'type': 'float', 'line': 15, 'scope_attr': 'processFloat'}, # Param
                        'temp_f': {'type': 'float', 'line': 16, 'scope_attr': 'processFloat'} # Local
                    }
                }
            ]

        def lookup_symbol(self, name, current_scope_name=None):
            if current_scope_name:
                for scope_data in self.all_created_scopes_data:
                    if scope_data['name'] == current_scope_name:
                        if name in scope_data['symbols']:
                            return scope_data['symbols'][name]
            if self.all_created_scopes_data and name in self.all_created_scopes_data[0]['symbols']: # Check global
                 return self.all_created_scopes_data[0]['symbols'][name]
            return None

    class MockASTNode:
        def __init__(self, value, children=None, lineno=0):
            self.value = value
            self.children = children if children else []
            self.lineno = lineno

    # AST for testing Phase 6
    # float g_var_float;
    # float processFloat(float x) { float temp_f; temp_f = x * 2.0; return temp_f; }
    # main() { float myFloat; myFloat = 3.14; float f_res; f_res = processFloat(myFloat + 1); print(f_res); print(g_var_float); }

    ast = MockASTNode("programa", [ MockASTNode("funciones", [
        MockASTNode("funcion", [ # processFloat(float x)
            MockASTNode("tipo", [MockASTNode("FLOAT")]), MockASTNode("processFloat"),
            MockASTNode("funcion_rest", [
                MockASTNode("LPAREN"), MockASTNode("parametros", [MockASTNode("parametro", [MockASTNode("tipo", [MockASTNode("FLOAT")]), MockASTNode("x")])]), MockASTNode("RPAREN"),
                MockASTNode("bloque", [ MockASTNode("LBRACE"), MockASTNode("instrucciones", [
                    MockASTNode("instruccion", [MockASTNode("declaracion", [MockASTNode("tipo", [MockASTNode("FLOAT")]), MockASTNode("temp_f"), MockASTNode("inicializacion", [MockASTNode("ε")])])]),
                    MockASTNode("instrucciones", [
                        MockASTNode("instruccion", [ MockASTNode("temp_f"), MockASTNode("id_rhs_instruccion", [ MockASTNode("EQUALS"), # temp_f = x * 2.0
                            MockASTNode("exp", [MockASTNode("E",[MockASTNode("C",[MockASTNode("R",[MockASTNode("T",[
                                MockASTNode("F", [MockASTNode("A", [MockASTNode("x")])]), # x
                                MockASTNode("F_rest", [MockASTNode("TIMES"), MockASTNode("A",[MockASTNode(2.0)]), MockASTNode("F_rest", [MockASTNode("ε")]) ]) # * 2.0
                            ])])])])]), MockASTNode("SEMI")])
                        ]),
                        MockASTNode("instrucciones", [
                            MockASTNode("instruccion", [MockASTNode("Return", [MockASTNode("exp_opt", [MockASTNode("exp", [MockASTNode("E",[MockASTNode("C",[MockASTNode("R",[MockASTNode("T",[MockASTNode("F",[MockASTNode("A",[MockASTNode("temp_f")])])])])])])])])]),
                            MockASTNode("instrucciones", [MockASTNode("ε")])
                        ])
                    ])
                ]), MockASTNode("RBRACE")])
            ])
        ]),
        MockASTNode("funciones", [ MockASTNode("funcion", [ # main()
            MockASTNode("MAIN"), MockASTNode("LPAREN"), MockASTNode("RPAREN"),
            MockASTNode("bloque", [ MockASTNode("LBRACE"), MockASTNode("instrucciones", [
                MockASTNode("instruccion", [MockASTNode("declaracion", [MockASTNode("tipo", [MockASTNode("FLOAT")]), MockASTNode("myFloat"), MockASTNode("inicializacion", [MockASTNode("ε")])])]),
                MockASTNode("instrucciones", [
                    MockASTNode("instruccion", [MockASTNode("myFloat"), MockASTNode("id_rhs_instruccion", [MockASTNode("EQUALS"), MockASTNode("exp", [MockASTNode("E",[MockASTNode("C",[MockASTNode("R",[MockASTNode("T",[MockASTNode("F",[MockASTNode("A",[MockASTNode(3.14)])])])])])])]), MockASTNode("SEMI")])]), # myFloat = 3.14
                    MockASTNode("instrucciones", [
                        MockASTNode("instruccion", [MockASTNode("declaracion", [MockASTNode("tipo", [MockASTNode("FLOAT")]), MockASTNode("f_res"), MockASTNode("inicializacion", [MockASTNode("ε")])])]),
                        MockASTNode("instrucciones", [
                            MockASTNode("instruccion", [ MockASTNode("f_res"), MockASTNode("id_rhs_instruccion", [ MockASTNode("EQUALS"), # f_res = processFloat(myFloat + 1)  (int 1 should be coerced for +)
                                MockASTNode("exp", [MockASTNode("E",[MockASTNode("C",[MockASTNode("R",[MockASTNode("T",[MockASTNode("F",[
                                    MockASTNode("A", [MockASTNode("processFloat"), MockASTNode("llamada_func", [ MockASTNode("LPAREN"), MockASTNode("lista_args", [
                                        MockASTNode("exp", [MockASTNode("E",[MockASTNode("C",[MockASTNode("R",[MockASTNode("T",[ # myFloat + 1
                                            MockASTNode("F",[MockASTNode("A",[MockASTNode("myFloat")])]), # myFloat
                                            MockASTNode("T_rest", [MockASTNode("PLUS"), MockASTNode("F",[MockASTNode("A",[MockASTNode(1)])]), MockASTNode("T_rest",[MockASTNode("ε")])]) # + 1 (int)
                                        ])])])])])
                                    ]), MockASTNode("RPAREN")])])
                                ])])])])])])]), MockASTNode("SEMI")])
                            ]),
                            MockASTNode("instrucciones", [
                                MockASTNode("instruccion", [MockASTNode("Print", [MockASTNode("PRINT"), MockASTNode("LPAREN"), MockASTNode("exp", [MockASTNode("E",[MockASTNode("C",[MockASTNode("R",[MockASTNode("T",[MockASTNode("F",[MockASTNode("A",[MockASTNode("f_res")])])])])])])]), MockASTNode("RPAREN")])]), # print(f_res)
                                MockASTNode("instrucciones", [
                                     MockASTNode("instruccion", [MockASTNode("Print", [MockASTNode("PRINT"), MockASTNode("LPAREN"), MockASTNode("exp", [MockASTNode("E",[MockASTNode("C",[MockASTNode("R",[MockASTNode("T",[MockASTNode("F",[MockASTNode("A",[MockASTNode("g_var_float")])])])])])])]), MockASTNode("RPAREN")])]), # print(g_var_float)
                                    MockASTNode("instrucciones", [MockASTNode("ε")])
                                ])
                            ])
                        ])
                    ])
                ])
            ]), MockASTNode("RBRACE")])
        ]), MockASTNode("funciones", [MockASTNode("ε")])])
    ])]);

    st = MockSymbolTable()
    generator = CodeGeneratorSPIM(ast, st)

    spim_output = generator.generate_code()

    print("--- Generated SPIM Code (Phase 6 Test) ---")
    print(spim_output)
