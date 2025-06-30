import ply.lex as lex

# Palabras reservadas
reserved = {
    'int': 'INT',
    'float': 'FLOAT',
    'bool': 'BOOL',
    'string': 'STRING',
    'void': 'VOID',

    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'for': 'FOR',

    'main': 'MAIN',
    'return': 'RETURN',
    'print': 'PRINT',
    'true': 'TRUE',
    'false': 'FALSE'
}

tokens = [
    'ID', 'INT_NUM', 'FLOAT_NUM', 'STRING_LITERAL', # STRING_LITERAL ya está aquí
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MOD',
    'EQ', 'NE', 'LT', 'GT', 'LE', 'GE',
    'AND', 'OR', 'EQUALS',
    'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'COMMA', 'SEMI'
] + list(reserved.values())

# Operadores y símbolos
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MOD = r'%'
t_EQUALS = r'='
t_EQ = r'=='
t_NE = r'!='
t_LT = r'<'
t_GT = r'>'
t_LE = r'<='
t_GE = r'>='
t_AND = r'&&'
t_OR = r'\|\|'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COMMA = r','
t_SEMI = r';'

# ID antes de otros tokens
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')  # Si es palabra reservada, se reemplaza
    return t

# Otros tokens simples...
def t_FLOAT_NUM(t):
    r'((\d*\.\d+)|(\d+\.\d*))([eE][-+]?\d+)?|\d+[eE][-+]?\d+'
    t.value = float(t.value)
    return t

def t_INT_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_STRING_LITERAL(t):
    r'\"([^\\\n]|(\\.))*?\"'  # Maneja strings con escapes básicos, no saltos de línea dentro.
    t.value = t.value[1:-1]  # Remueve las comillas
    return t

# Ignorar espacios y tabs
t_ignore = ' \t'

def t_COMMENT(t):
    r'//.*|/\*([^*]|\*[^/])*\*/'
    pass  # Ignora los comentarios

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()
