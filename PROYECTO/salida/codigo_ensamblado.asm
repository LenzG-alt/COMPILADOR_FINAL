.data
newline_char: .asciiz "\n"  # Para saltos de línea en print
  g_func_test: .word 77  # Global int
  L_float_lit_3: .float 1.003000  # Literal float 1.003
  L_float_lit_12: .float 2.200000  # Literal float 2.2
  L_float_lit_13: .float 2.200000  # Literal float 2.2

.text
.globl main

func_v_v:  # Definición de función 'func_v_v'
  # Prólogo de func_v_v
  addiu $sp, $sp, -8   # Espacio para guardar $ra y $fp antiguos
  sw $ra, 4($sp)        # Guardar dirección de retorno $ra
  sw $fp, 0($sp)        # Guardar frame pointer antiguo
  move $fp, $sp         # Nuevo frame pointer
  # Inicio Print: evaluando expresión en línea 7
  li $t0, 1001  # Cargar entero literal 1001
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Asignación: g_func_test = ...
  li $t0, 88  # Cargar entero literal 88
  sw $t0, g_func_test  # Guardar entero/puntero en global 'g_func_test'
  # Fin Asignación: g_func_test
epilogo_func_v_v1:
  # Epílogo de func_v_v
  lw $fp, 0($sp)        # Restaurar $fp antiguo
  lw $ra, 4($sp)        # Restaurar $ra original
  addiu $sp, $sp, 8   # Liberar espacio de $ra y $fp guardados
  jr $ra                # Retorno de func_v_v

func_i_ii:  # Definición de función 'func_i_ii'
  # Prólogo de func_i_ii
  addiu $sp, $sp, -8   # Espacio para guardar $ra y $fp antiguos
  sw $ra, 4($sp)        # Guardar dirección de retorno $ra
  sw $fp, 0($sp)        # Guardar frame pointer antiguo
  move $fp, $sp         # Nuevo frame pointer
  addiu $sp, $sp, -4  # Espacio para locales
  # Inicio Print: evaluando expresión en línea 13
  li $t0, 1002  # Cargar entero literal 1002
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Print: evaluando expresión en línea 14
  lw $t0, 8($fp)  # Cargar local/param variable 'p1'
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Print: evaluando expresión en línea 15
  lw $t0, 12($fp)  # Cargar local/param variable 'p2'
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Declaración de local 'resultado' de tipo int en offset -4($fp)
  # Inicio Asignación: resultado = ...
  lw $t0, 8($fp)  # Cargar local/param variable 'p1'
  lw $t1, 12($fp)  # Cargar local/param variable 'p2'
  # Operación PLUS (int y int)
  add $t0, $t0, $t1  # Suma int: $t0 = $t0 + $t1
  lw $t1, g_func_test   # Cargar global variable 'g_func_test'
  # Operación PLUS (int y int)
  add $t0, $t0, $t1  # Suma int: $t0 = $t0 + $t1
  sw $t0, -4($fp)  # Guardar entero/puntero en local 'resultado'
  # Fin Asignación: resultado
  lw $t0, -4($fp)  # Cargar local/param variable 'resultado'
epilogo_func_i_ii2:
  # Epílogo de func_i_ii
  move $sp, $fp          # $sp apunta a $fp/$ra guardados
  lw $fp, 0($sp)        # Restaurar $fp antiguo
  lw $ra, 4($sp)        # Restaurar $ra original
  addiu $sp, $sp, 8   # Liberar espacio de $ra y $fp guardados
  jr $ra                # Retorno de func_i_ii

func_f_ff:  # Definición de función 'func_f_ff'
  # Prólogo de func_f_ff
  addiu $sp, $sp, -8   # Espacio para guardar $ra y $fp antiguos
  sw $ra, 4($sp)        # Guardar dirección de retorno $ra
  sw $fp, 0($sp)        # Guardar frame pointer antiguo
  move $fp, $sp         # Nuevo frame pointer
  addiu $sp, $sp, -4  # Espacio para locales
  # Inicio Print: evaluando expresión en línea 23
  l.s $f4, L_float_lit_3 # Cargar float literal a $f4
  # Print: valor de tipo 'float' en registro '$f4'
  mov.s $f12, $f4 # Mover float a $f12 para imprimir
  li $v0, 2             # Syscall para imprimir float
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Print: evaluando expresión en línea 24
  l.s $f4, 8($fp)  # Cargar local/param variable 'fp1'
  # Print: valor de tipo 'float' en registro '$f4'
  mov.s $f12, $f4 # Mover float a $f12 para imprimir
  li $v0, 2             # Syscall para imprimir float
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Print: evaluando expresión en línea 25
  l.s $f4, 12($fp)  # Cargar local/param variable 'fp2'
  # Print: valor de tipo 'float' en registro '$f4'
  mov.s $f12, $f4 # Mover float a $f12 para imprimir
  li $v0, 2             # Syscall para imprimir float
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Declaración de local 'res_f' de tipo float en offset -4($fp)
  # Inicio Asignación: res_f = ...
  l.s $f4, 8($fp)  # Cargar local/param variable 'fp1'
  l.s $f5, 12($fp)  # Cargar local/param variable 'fp2'
  # Operación TIMES (float y float)
  mul.s $f4, $f4, $f5 # Mult float: $f4 = $f4 * $f5
  s.s $f4, -4($fp)  # Guardar float en local 'res_f'
  # Fin Asignación: res_f
  l.s $f4, -4($fp)  # Cargar local/param variable 'res_f'
epilogo_func_f_ff4:
  # Epílogo de func_f_ff
  move $sp, $fp          # $sp apunta a $fp/$ra guardados
  lw $fp, 0($sp)        # Restaurar $fp antiguo
  lw $ra, 4($sp)        # Restaurar $ra original
  addiu $sp, $sp, 8   # Liberar espacio de $ra y $fp guardados
  jr $ra                # Retorno de func_f_ff

func_b_bi:  # Definición de función 'func_b_bi'
  # Prólogo de func_b_bi
  addiu $sp, $sp, -8   # Espacio para guardar $ra y $fp antiguos
  sw $ra, 4($sp)        # Guardar dirección de retorno $ra
  sw $fp, 0($sp)        # Guardar frame pointer antiguo
  move $fp, $sp         # Nuevo frame pointer
  # Inicio Print: evaluando expresión en línea 33
  li $t0, 1004  # Cargar entero literal 1004
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Print: evaluando expresión en línea 34
  lw $t0, 8($fp)  # Cargar local/param variable 'bp1'
  # Print: valor de tipo 'bool' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Print: evaluando expresión en línea 35
  lw $t0, 12($fp)  # Cargar local/param variable 'ip1'
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print

  # Inicio IF en línea 36
  lw $t0, 8($fp)  # Cargar local/param variable 'bp1'
  # Inicio expresión entre paréntesis
  lw $t1, 12($fp)  # Cargar local/param variable 'ip1'
  li $t2, 10  # Cargar entero literal 10
  # Comparación GT: $t1 vs $t2
  sgt $t1, $t1, $t2
  # Fin expresión entre paréntesis, resultado en $t1
  # Operación AND: $t0 = $t0 and $t1
  and $t0, $t0, $t1
  beq $t0, $zero, L_endif_6  # Salta si la condición es falsa (0)
  # Rama THEN del IF en línea 36
  li $t0, 1  # Cargar literal true (1)
L_endif_6:  # Etiqueta final del IF-ELSE
  # Fin IF en línea 36
  li $t0, 0  # Cargar literal false (0)
epilogo_func_b_bi7:
  # Epílogo de func_b_bi
  lw $fp, 0($sp)        # Restaurar $fp antiguo
  lw $ra, 4($sp)        # Restaurar $ra original
  addiu $sp, $sp, 8   # Liberar espacio de $ra y $fp guardados
  jr $ra                # Retorno de func_b_bi

func_caller:  # Definición de función 'func_caller'
  # Prólogo de func_caller
  addiu $sp, $sp, -8   # Espacio para guardar $ra y $fp antiguos
  sw $ra, 4($sp)        # Guardar dirección de retorno $ra
  sw $fp, 0($sp)        # Guardar frame pointer antiguo
  move $fp, $sp         # Nuevo frame pointer
  addiu $sp, $sp, -4  # Espacio para locales
  # Inicio Print: evaluando expresión en línea 44
  li $t0, 1005  # Cargar entero literal 1005
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Declaración de local 'y' de tipo int en offset -4($fp)
  # Inicio Asignación: y = ...
  # Inicio llamada a función 'func_i_ii'
    # Evaluando argumento 1 para 'func_i_ii'
  lw $t0, 8($fp)  # Cargar local/param variable 'x'
    # Evaluando argumento 2 para 'func_i_ii'
  lw $t1, 8($fp)  # Cargar local/param variable 'x'
  li $t2, 2  # Cargar entero literal 2
  # Operación TIMES (int y int)
  mult $t1, $t2     # Mult int: $t1 * $t2
  mflo $t1            # Resultado en $t1
    # Pasando argumentos a 'func_i_ii'
  move $a0, $t0  # Pasar arg 1 ($t0) a $a0
  move $a1, $t1  # Pasar arg 2 ($t1) a $a1
  jal func_i_ii      # Llamar a la función 'func_i_ii'
  move $t0, $v0 # Mover resultado de 'func_i_ii' desde $v0
  # Fin llamada a función 'func_i_ii', retorno en $t0
  lw $t1, g_func_test   # Cargar global variable 'g_func_test'
  # Operación PLUS (int y int)
  add $t0, $t0, $t1  # Suma int: $t0 = $t0 + $t1
  sw $t0, -4($fp)  # Guardar entero/puntero en local 'y'
  # Fin Asignación: y
  lw $t0, -4($fp)  # Cargar local/param variable 'y'
epilogo_func_caller8:
  # Epílogo de func_caller
  move $sp, $fp          # $sp apunta a $fp/$ra guardados
  lw $fp, 0($sp)        # Restaurar $fp antiguo
  lw $ra, 4($sp)        # Restaurar $ra original
  addiu $sp, $sp, 8   # Liberar espacio de $ra y $fp guardados
  jr $ra                # Retorno de func_caller

func_early_return:  # Definición de función 'func_early_return'
  # Prólogo de func_early_return
  addiu $sp, $sp, -8   # Espacio para guardar $ra y $fp antiguos
  sw $ra, 4($sp)        # Guardar dirección de retorno $ra
  sw $fp, 0($sp)        # Guardar frame pointer antiguo
  move $fp, $sp         # Nuevo frame pointer
  # Inicio Print: evaluando expresión en línea 52
  li $t0, 1006  # Cargar entero literal 1006
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print

  # Inicio IF en línea 53
  lw $t0, 8($fp)  # Cargar local/param variable 'val'
  li $t1, 0  # Cargar entero literal 0
  # Comparación LT: $t0 vs $t1
  slt $t0, $t0, $t1
  beq $t0, $zero, L_endif_10  # Salta si la condición es falsa (0)
  # Rama THEN del IF en línea 53
  li $t0, 1  # Cargar entero literal 1
L_endif_10:  # Etiqueta final del IF-ELSE
  # Fin IF en línea 53
  # Inicio Print: evaluando expresión en línea 56
  lw $t0, 8($fp)  # Cargar local/param variable 'val'
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  lw $t0, 8($fp)  # Cargar local/param variable 'val'
  li $t1, 2  # Cargar entero literal 2
  # Operación TIMES (int y int)
  mult $t0, $t1     # Mult int: $t0 * $t1
  mflo $t0            # Resultado en $t0
epilogo_func_early_return11:
  # Epílogo de func_early_return
  lw $fp, 0($sp)        # Restaurar $fp antiguo
  lw $ra, 4($sp)        # Restaurar $ra original
  addiu $sp, $sp, 8   # Liberar espacio de $ra y $fp guardados
  jr $ra                # Retorno de func_early_return

main:
  # Prólogo de main
  addiu $sp, $sp, -4   # Espacio para guardar $fp antiguo
  sw $fp, 0($sp)        # Guardar frame pointer antiguo
  move $fp, $sp         # Nuevo frame pointer
  addiu $sp, $sp, -12  # Espacio para locales
  # Declaración de local 'res_i' de tipo int en offset -4($fp)
  # Declaración de local 'res_f' de tipo float en offset -8($fp)
  # Declaración de local 'res_b' de tipo bool en offset -12($fp)
  # Inicio Print: evaluando expresión en línea 66
  li $t0, 80000  # Cargar entero literal 80000
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio llamada a función (statement): func_f_ff
    # Evaluando argumento 1 para 'func_f_ff'
  l.s $f4, L_float_lit_12 # Cargar float literal a $f4
    # Evaluando argumento 2 para 'func_f_ff'
  l.s $f5, L_float_lit_13 # Cargar float literal a $f5
    # Pasando argumentos a 'func_f_ff'
  mov.s $f12, $f4  # Pasar arg float 1 ($f4) a $f12
  jal func_f_ff      # Llamar a la función 'func_f_ff'
  mov.s $f4, $f0 # Mover resultado float de 'func_f_ff' desde $f0
  # Fin llamada a función (statement): func_f_ff
  # Inicio llamada a función (statement): func_v_v
    # Pasando argumentos a 'func_v_v'
  jal func_v_v      # Llamar a la función 'func_v_v'
  # Fin llamada a función (statement): func_v_v
  # Inicio Print: evaluando expresión en línea 70
  lw $t0, g_func_test   # Cargar global variable 'g_func_test'
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Asignación: res_i = ...
  # Inicio llamada a función 'func_i_ii'
    # Evaluando argumento 1 para 'func_i_ii'
  li $t0, 10  # Cargar entero literal 10
    # Evaluando argumento 2 para 'func_i_ii'
  li $t1, 20  # Cargar entero literal 20
    # Pasando argumentos a 'func_i_ii'
  move $a0, $t0  # Pasar arg 1 ($t0) a $a0
  move $a1, $t1  # Pasar arg 2 ($t1) a $a1
  jal func_i_ii      # Llamar a la función 'func_i_ii'
  move $t0, $v0 # Mover resultado de 'func_i_ii' desde $v0
  # Fin llamada a función 'func_i_ii', retorno en $t0
  sw $t0, -4($fp)  # Guardar entero/puntero en local 'res_i'
  # Fin Asignación: res_i
  # Inicio Print: evaluando expresión en línea 74
  lw $t0, -4($fp)  # Cargar local/param variable 'res_i'
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Print: evaluando expresión en línea 77
  l.s $f4, -8($fp)  # Cargar local/param variable 'res_f'
  # Print: valor de tipo 'float' en registro '$f4'
  mov.s $f12, $f4 # Mover float a $f12 para imprimir
  li $v0, 2             # Syscall para imprimir float
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Asignación: res_b = ...
  # Inicio llamada a función 'func_b_bi'
    # Evaluando argumento 1 para 'func_b_bi'
  li $t0, 1  # Cargar literal true (1)
    # Evaluando argumento 2 para 'func_b_bi'
  li $t1, 15  # Cargar entero literal 15
    # Pasando argumentos a 'func_b_bi'
  move $a0, $t0  # Pasar arg 1 ($t0) a $a0
  move $a1, $t1  # Pasar arg 2 ($t1) a $a1
  jal func_b_bi      # Llamar a la función 'func_b_bi'
  move $t0, $v0 # Mover resultado de 'func_b_bi' desde $v0
  # Fin llamada a función 'func_b_bi', retorno en $t0
  sw $t0, -12($fp)  # Guardar entero/puntero en local 'res_b'
  # Fin Asignación: res_b
  # Inicio Print: evaluando expresión en línea 81
  lw $t0, -12($fp)  # Cargar local/param variable 'res_b'
  # Print: valor de tipo 'bool' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Asignación: res_b = ...
  # Inicio llamada a función 'func_b_bi'
    # Evaluando argumento 1 para 'func_b_bi'
  li $t0, 1  # Cargar literal true (1)
    # Evaluando argumento 2 para 'func_b_bi'
  li $t1, 5  # Cargar entero literal 5
    # Pasando argumentos a 'func_b_bi'
  move $a0, $t0  # Pasar arg 1 ($t0) a $a0
  move $a1, $t1  # Pasar arg 2 ($t1) a $a1
  jal func_b_bi      # Llamar a la función 'func_b_bi'
  move $t0, $v0 # Mover resultado de 'func_b_bi' desde $v0
  # Fin llamada a función 'func_b_bi', retorno en $t0
  sw $t0, -12($fp)  # Guardar entero/puntero en local 'res_b'
  # Fin Asignación: res_b
  # Inicio Print: evaluando expresión en línea 83
  lw $t0, -12($fp)  # Cargar local/param variable 'res_b'
  # Print: valor de tipo 'bool' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Asignación: res_i = ...
  # Inicio llamada a función 'func_caller'
    # Evaluando argumento 1 para 'func_caller'
  li $t0, 5  # Cargar entero literal 5
    # Pasando argumentos a 'func_caller'
  move $a0, $t0  # Pasar arg 1 ($t0) a $a0
  jal func_caller      # Llamar a la función 'func_caller'
  move $t0, $v0 # Mover resultado de 'func_caller' desde $v0
  # Fin llamada a función 'func_caller', retorno en $t0
  sw $t0, -4($fp)  # Guardar entero/puntero en local 'res_i'
  # Fin Asignación: res_i
  # Inicio Print: evaluando expresión en línea 90
  lw $t0, -4($fp)  # Cargar local/param variable 'res_i'
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Asignación: res_i = ...
  # Inicio llamada a función 'func_early_return'
    # Evaluando argumento 1 para 'func_early_return'
  li $t0, 5  # Cargar entero literal 5
    # Pasando argumentos a 'func_early_return'
  move $a0, $t0  # Pasar arg 1 ($t0) a $a0
  jal func_early_return      # Llamar a la función 'func_early_return'
  move $t0, $v0 # Mover resultado de 'func_early_return' desde $v0
  # Fin llamada a función 'func_early_return', retorno en $t0
  sw $t0, -4($fp)  # Guardar entero/puntero en local 'res_i'
  # Fin Asignación: res_i
  # Inicio Print: evaluando expresión en línea 94
  lw $t0, -4($fp)  # Cargar local/param variable 'res_i'
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Asignación: res_i = ...
  # Inicio llamada a función 'func_early_return'
    # Evaluando argumento 1 para 'func_early_return'
  li $t0, 7  # Cargar entero literal 7
    # Pasando argumentos a 'func_early_return'
  move $a0, $t0  # Pasar arg 1 ($t0) a $a0
  jal func_early_return      # Llamar a la función 'func_early_return'
  move $t0, $v0 # Mover resultado de 'func_early_return' desde $v0
  # Fin llamada a función 'func_early_return', retorno en $t0
  sw $t0, -4($fp)  # Guardar entero/puntero en local 'res_i'
  # Fin Asignación: res_i
  # Inicio Print: evaluando expresión en línea 97
  lw $t0, -4($fp)  # Cargar local/param variable 'res_i'
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print
  # Inicio Print: evaluando expresión en línea 99
  li $t0, 80001  # Cargar entero literal 80001
  # Print: valor de tipo 'int' en registro '$t0'
  move $a0, $t0    # Preparar para imprimir int/bool
  li $v0, 1           # Syscall para imprimir entero
  syscall               # Ejecutar print
  la $a0, newline_char  # Cargar dirección de newline
  li $v0, 4             # Syscall para imprimir string (newline)
  syscall               # Ejecutar print de newline
  # Fin Print

  # Fin de main
  move $sp, $fp          # Liberar locales, $sp apunta a $fp guardado
  lw $fp, 0($sp)        # Restaurar $fp antiguo
  addiu $sp, $sp, 4   # Liberar espacio de $fp guardado
  li $v0, 10            # Syscall para terminar programa
  syscall