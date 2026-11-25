push rbp
push rbx
push r12
push r13
push r14
push r15
mov rbx, rdi
mov rbp, rsi
mov [rbx+312], rsp
sub rsp, 120
mov qword ptr [rsp+48], 0
//   0x00:
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 30
//       0x00: PUSH1 0x0
//       0x02: CALLDATALOAD
vpxor ymm0, ymm0, ymm0
mov rdi, qword ptr [rbx+144]
mov esi, dword ptr [rbx+168]
cmp rsi, 32
jl L4
vmovups ymm15, byte ptr [rdi]
L5:
vpermq ymm0, ymm15, 27
vpshufb ymm0, ymm0, qword ptr [ROD+32]
L3:
//       0x03: PUSH1 0x40
//       0x05: CALLDATALOAD
vpxor ymm1, ymm1, ymm1
mov rdi, qword ptr [rbx+144]
mov esi, dword ptr [rbx+168]
add rdi, 64
sub rsi, 64
cmp rsi, 32
jl L7
vmovups ymm15, byte ptr [rdi]
L8:
vpermq ymm1, ymm15, 27
vpshufb ymm1, ymm1, qword ptr [ROD+32]
L6:
//       0x06: ADD
vmovaps qword ptr [rbp], ymm1
mov r12, qword ptr [rbp]
mov r13, qword ptr [rbp+8]
mov r14, qword ptr [rbp+16]
mov r15, qword ptr [rbp+24]
vmovaps qword ptr [rbp+32], ymm0
add r12, qword ptr [rbp+32]
adc r13, qword ptr [rbp+40]
adc r14, qword ptr [rbp+48]
adc r15, qword ptr [rbp+56]
//       0x07: CALLDATALOAD
vpxor ymm0, ymm0, ymm0
mov rax, r12
and r12, qword ptr [ROD+8]
or r15, r14
or r13, r12
or r15, r13
jnz L9
mov rdi, qword ptr [rbx+144]
mov esi, dword ptr [rbx+168]
add rdi, rax
sub rsi, rax
cmp rsi, 32
jl L10
vmovups ymm15, byte ptr [rdi]
L11:
vpermq ymm0, ymm15, 27
vpshufb ymm0, ymm0, qword ptr [ROD+32]
L9:
//       0x08: PUSH1 0x0
//       0x0a: MSTORE
cmp dword ptr [rbx+264], 32
jae L12
mov rdi, 32
call qword ptr [ROD+16]
L12:
mov rax, qword ptr [rbx+272]
vpermq ymm1, ymm0, 27
vpshufb ymm1, ymm1, qword ptr [ROD+32]
vmovups qword ptr [rax], ymm1
//       0x0b: PUSH1 0x20
//       0x0d: PUSH1 0x0
//     0x0f: Return
mov qword ptr [rbx+256], 0
vpxor ymm0, ymm0, ymm0
vmovups qword ptr [rbx+192], ymm0
vmovd xmm1, dword ptr [ROD+24]
vmovups qword ptr [rbx+224], ymm1
jmp ContractEpilogue
align 16
ContractEpilogue:
vzeroupper
add rsp, 120
pop r15
pop r14
pop r13
pop r12
pop rbx
pop rbp
ret
L4:
call qword ptr [ROD]
jmp L5
L7:
call qword ptr [ROD]
jmp L8
L10:
call qword ptr [ROD]
jmp L11
align 16
Error:
mov qword ptr [rbx+256], 2
short jmp ContractEpilogue
align 4
.section ro {#1}
ROD:
.db 0xC0, 0x92, 0xB0, 0x04, 0x56, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0xFF, 0x10, 0x25, 0xAF, 0x04, 0x56, 0x55, 0x00, 0x00, 0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0x00, 0x0F, 0x0E, 0x0D, 0x0C, 0x0B, 0x0A, 0x09, 0x08, 0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0x00, 0x0F, 0x0E, 0x0D, 0x0C, 0x0B, 0x0A, 0x09, 0x08
