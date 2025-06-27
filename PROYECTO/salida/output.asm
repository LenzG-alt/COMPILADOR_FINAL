.data
    x: .word 0
    z: .word str_0
    y: .word 0
    str_0: .asciiz ""

.text
.globl main
main:
    # --- Prologue for main ---
    addi $sp, $sp, -4   # Allocate space for $ra
    sw $ra, 0($sp)      # Save $ra
    addi $sp, $sp, -4   # Allocate space for old $fp
    sw $fp, 0($sp)      # Save old $fp
    move $fp, $sp         # Set new $fp
    # --- Epilogue for main ---
main_epilogue:
    lw $fp, 0($sp)      # Restore old $fp
    addi $sp, $sp, 4   # Deallocate space for old $fp
    lw $ra, 0($sp)      # Restore $ra
    addi $sp, $sp, 4   # Deallocate space for $ra
    # Exit program (end of main)
    li $v0, 10
    syscall
    