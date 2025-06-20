import ply.lex as lex

# === Palabras reservadas ===
reserved = {
    # Tipos de datos
    'int': 'INT',
    'float': 'FLOAT',
    'bool': 'BOOL',
    'string': 'STRING',
    'void': 'VOID',
    
    # Estructuras de control
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'for': 'FOR',
    
    # Funciones y retorno
    'main': 'MAIN',
    'return': 'RETURN',
    'print': 'PRINT',
    
    # Valores booleanos
    'true': 'TRUE',
    'false': 'FALSE'
}

# === Todos los tokens ===
tokens = [
    # Identificadores y literales
    'ID', 
    'INT_NUM', 'FLOAT_NUM',
    'STRING_LITERAL',
    
    # Operadores aritméticos
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    
    # Operadores de comparación
    'EQ', 'NE', 'LT', 'GT', 'LE', 'GE',
    
    # Operadores lógicos
    'AND', 'OR',
    
    # Asignación
    'EQUALS',
    
    # Símbolos especiales
    'LPAREN', 'RPAREN',   # ( )
    'LBRACE', 'RBRACE',    # { }
    'COMMA', 'SEMI'        # , ;
] + list(reserved.values())

# === Reglas simples para símbolos ===
t_PLUS     = r'\+'
t_MINUS    = r'-'
t_TIMES    = r'\*'
t_DIVIDE   = r'/'
t_MOD      = r'%'
t_EQUALS   = r'='   # Asignación
t_EQ       = r'=='  # Igualdad
t_NE       = r'!='
t_LT       = r'<'
t_GT       = r'>'
t_LE       = r'<='
t_GE       = r'>='
t_AND      = r'&&'
t_OR       = r'\|\|'
t_LPAREN   = r'\('
t_RPAREN   = r'\)'
t_LBRACE   = r'\{'
t_RBRACE   = r'\}'
t_COMMA    = r','
t_SEMI     = r';'

# === Reglas complejas ===
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')  # Check for reserved words
    return t

def t_FLOAT_NUM(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_INT_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING_LITERAL(t):
    r'\"([^\\\"]|\\.)*\"'
    # Remover comillas y manejar secuencias de escape
    t.value = t.value[1:-1].replace('\\n', '\n').replace('\\t', '\t')
    return t

# === Ignorar espacios y comentarios ===
t_ignore = ' \t'

def t_COMMENT(t):
    r'//.*|\/\*(.|\n)*?\*\/'
    pass  # Los comentarios se ignoran

# === Contar líneas ===
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# === Manejo de errores mejorado ===
def t_error(t):
    error_msg = f"Error léxico en línea {t.lineno}: Carácter ilegal '{t.value[0]}'"
    line_start = t.lexer.lexdata.rfind('\n', 0, t.lexer.lexpos) + 1
    line_end = t.lexer.lexdata.find('\n', t.lexer.lexpos)
    if line_end < 0:
        line_end = len(t.lexer.lexdata)
    error_line = t.lexer.lexdata[line_start:line_end]
    marker = ' ' * (t.lexpos - line_start) + '^'
    
    with open("salida/errores_lexicos.txt", "a", encoding="utf-8") as error_file:
        error_file.write(f"{error_msg}\n{error_line}\n{marker}\n\n")
    
    t.lexer.skip(1)

lexer = lex.lex()
