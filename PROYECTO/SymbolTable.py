class SymbolTable:
    def __init__(self):
        # Each scope_item is a dictionary: {'name': scope_context_name_str, 'symbols': {symbol_name_str: attribute_dict}}
        # attribute_dict: {'type': type_str, 'line': line_int, 'scope_attr': value_for_ambito_column_str, 'param_types': list_of_strings_or_None}
        self.scope_stack = [{'name': 'global', 'symbols': {}}] # Current stack for lookups
        self.all_created_scopes_data = [self.scope_stack[0]] # Persistent list of all scopes for reporting
        self.errors = []

    def enter_scope(self, scope_context_name):
        # scope_context_name is the actual name of the scope being entered, e.g., 'main', 'myFunction'
        if not scope_context_name:
            # Fallback, though ideally a meaningful name should always be provided
            scope_context_name = f"scope_{len(self.scope_stack)}" # Use scope_stack for unique naming if needed

        new_scope_symbols_dict = {}
        new_scope_data_for_stack = {'name': scope_context_name, 'symbols': new_scope_symbols_dict}

        self.scope_stack.append(new_scope_data_for_stack)
        self.all_created_scopes_data.append(new_scope_data_for_stack)


    def exit_scope(self):
        if len(self.scope_stack) > 1: # Cannot pop the global scope
            return self.scope_stack.pop()
        else:
            # This case should ideally not be reached if scope management is correct
            self.add_error("System Error: Attempted to exit global scope.")
            return None

    def add_symbol(self, name, type_val, lineno, declared_in_scope_name_attr, param_types=None):
        # declared_in_scope_name_attr is the string that will appear in the 'Ámbito' column of the symbol table,
        # e.g., "global" for global variables, or the function's name like "main" for local variables.
        # param_types: list of strings for parameter types if symbol is a function, else None.
        current_scope_data_on_stack = self.scope_stack[-1]
        current_symbols_dict = current_scope_data_on_stack['symbols']
        # current_scope_context = current_scope_data_on_stack['name'] # Actual name of the current scope level

        if name in current_symbols_dict:
            existing_symbol = current_symbols_dict[name]
            # Use declared_in_scope_name_attr for the error message as it's contextually what the user sees for Ámbito
            self.add_error(
                f"Error semántico [línea {lineno}]: El símbolo '{name}' ya ha sido declarado en el ámbito '{declared_in_scope_name_attr}' en la línea {existing_symbol['line']}."
            )
        else:
            symbol_entry = {
                'type': type_val,
                'line': lineno,
                'scope_attr': declared_in_scope_name_attr
            }
            if param_types is not None: # It's a function, store its parameter types
                symbol_entry['param_types'] = param_types

            current_symbols_dict[name] = symbol_entry


    def lookup_symbol(self, name):
        # Iterates from current scope outwards to global, using the active scope_stack
        for scope_data in reversed(self.scope_stack):
            if name in scope_data['symbols']:
                return scope_data['symbols'][name] # Returns the attribute dictionary
        return None

    def add_error(self, message):
        # Assumes 'message' is already fully formatted as per error reporting requirements
        self.errors.append(message)

    def get_formatted_symbol_table(self):
        output_lines = ["=== Tabla de Símbolos ==="]

        # Iterate over all_created_scopes_data to report all symbols from all scopes
        for scope_data in self.all_created_scopes_data:
            scope_context_name = scope_data['name'] # Actual name of the scope, e.g., 'global', 'main'

            if scope_context_name == 'global':
                output_lines.append("\nGlobales:")
            else:
                output_lines.append(f"\nLocales en '{scope_context_name}':")

            output_lines.append("| Nombre | Tipo | Ámbito       | Línea |")
            output_lines.append("|--------|------|--------------|-------|")

            symbols_in_scope = scope_data['symbols']
            if not symbols_in_scope:
                # Example: output_lines.append("| (sin símbolos en este ámbito) |      |              |       |")
                pass # No symbols, just print the header for this scope
            else:
                for name, attrs in symbols_in_scope.items():
                    # 'scope_attr' was stored during add_symbol, intended for 'Ámbito' column
                    ambito_display = attrs.get('scope_attr', scope_context_name) # Fallback to scope_context_name if scope_attr missing
                    output_lines.append(f"| {name:<6} | {attrs.get('type', 'N/A'):<4} | {ambito_display:<12} | {str(attrs.get('line', -1)):<5} |")

        return "\n".join(output_lines)

    def get_formatted_errors(self):
        output_lines = ["=== Errores Semánticos ==="]
        if not self.errors:
            output_lines.append("No se encontraron errores semánticos.")
        else:
            for i, error_msg in enumerate(self.errors):
                output_lines.append(f"{i+1}. {error_msg}")
        return "\n".join(output_lines)

if __name__ == '__main__':
    # Basic Test for SymbolTable
    st = SymbolTable()

    # Adding global symbols
    # For globals, the scope_context_name is 'global', and the declared_in_scope_name_attr (for Ámbito column) is also 'global'
    # Test scenario:
    # global: g_var1, g_var2
    # main scope: l_var_main, g_var1 (shadows)
    # foo scope: l_var_foo, g_var2 (shadows)

    # Adding global symbols
    st.add_symbol('g_var1', 'int', 1, 'global') # Added to scope_stack[0] and all_created_scopes_data[0]
    st.add_symbol('g_var2', 'float', 2, 'global')

    # Entering 'main' function scope
    st.enter_scope('main') # 'main' scope added to scope_stack and all_created_scopes_data
    # Symbols added to scope_stack[-1] (main's symbol dict)
    st.add_symbol('l_var_main', 'int', 5, 'main')
    st.add_symbol('g_var1', 'char', 6, 'main')     # Local 'g_var1' shadows global in 'main'
    st.add_symbol('l_var_main', 'bool', 7, 'main') # Error: Redefinition

    # Entering another function scope 'foo'
    st.enter_scope('foo') # 'foo' scope added to scope_stack and all_created_scopes_data
    st.add_symbol('l_var_foo', 'string', 10, 'foo')
    st.add_symbol('g_var2', 'int', 11, 'foo')      # Local 'g_var2' shadows global in 'foo'

    # Test lookup from the deepest scope ('foo') - uses scope_stack
    print("--- Lookups from 'foo' scope (uses scope_stack) ---")
    # Should find 'g_var1' from 'main' (shadows global 'g_var1')
    found_g_var1_in_foo = st.lookup_symbol('g_var1')
    if found_g_var1_in_foo:
        print(f"Found 'g_var1': Type={found_g_var1_in_foo['type']}, Ámbito={found_g_var1_in_foo['scope_attr']}, Line={found_g_var1_in_foo['line']}")

    # Should find 'l_var_foo' from 'foo'
    found_l_var_foo_in_foo = st.lookup_symbol('l_var_foo')
    if found_l_var_foo_in_foo:
        print(f"Found 'l_var_foo': Type={found_l_var_foo_in_foo['type']}, Ámbito={found_l_var_foo_in_foo['scope_attr']}, Line={found_l_var_foo_in_foo['line']}")

    # Exit 'foo' scope (pops from scope_stack, data remains in all_created_scopes_data)
    st.exit_scope()

    print("\n--- Lookups after exiting 'foo' (now in 'main' scope - uses scope_stack) ---")
    # Should find 'g_var1' from 'main'
    found_g_var1_in_main = st.lookup_symbol('g_var1')
    if found_g_var1_in_main:
         print(f"Found 'g_var1': Type={found_g_var1_in_main['type']}, Ámbito={found_g_var1_in_main['scope_attr']}, Line={found_g_var1_in_main['line']}")

    # 'l_var_foo' should not be found from 'main' scope via lookup_symbol
    found_l_var_foo_in_main = st.lookup_symbol('l_var_foo')
    print(f"Looking up 'l_var_foo' (from main): {found_l_var_foo_in_main}") # Expected: None

    # Exit 'main' scope
    st.exit_scope()

    print("\n--- Final Symbol Table (uses all_created_scopes_data) ---")
    # This will print global, then main's symbols, then foo's symbols
    print(st.get_formatted_symbol_table())

    print("\n--- Final Errors ---")
    print(st.get_formatted_errors())

    print("\n--- Lookups from global scope (uses scope_stack, which is now just global) ---")
    # Should find the original global 'g_var1'
    found_g_var1_global = st.lookup_symbol('g_var1')
    if found_g_var1_global:
         print(f"Found 'g_var1': Type={found_g_var1_global['type']}, Ámbito={found_g_var1_global['scope_attr']}, Line={found_g_var1_global['line']}")

    # 'l_var_main' should not be found from global scope via lookup_symbol
    found_l_var_main_global = st.lookup_symbol('l_var_main')
    print(f"Looking up 'l_var_main' (from global): {found_l_var_main_global}") # Expected: None
