//   0x5d5d:
B5d5d:
cmp qword ptr [rsp+48], 4
jb Error
cmp qword ptr [rsp+48], 1021
ja Error
sub qword ptr [rbx+16], 29
jl Error
//       0x5d5e: POP
//       0x5d5f: SWAP1
//       0x5d60: PUSH2 0x5d6c
//       0x5d63: PUSH2 0x5d71
//       0x5d66: SWAP3
//       0x5d67: DUP5
//       0x5d68: PUSH2 0x4922
//     0x5d6b: Jump
vmovaps ymm0, qword ptr [rbp-64]
vmovaps qword ptr [rbp], ymm0
vmovaps ymm0, qword ptr [rbp-96]
vmovaps qword ptr [rbp-64], ymm0
vmovd xmm0, dword ptr [ROD+6108]
vmovaps qword ptr [rbp-96], ymm0
vmovd xmm0, dword ptr [ROD+6528]
vmovaps qword ptr [rbp-32], ymm0
vmovaps ymm0, qword ptr [rbp-128]
vmovaps qword ptr [rbp+32], ymm0
add qword ptr [rsp+48], 2
add rbp, 64
jmp B4922
//   0x5d6c:
B5d6c:
cmp qword ptr [rsp+48], 1023
ja Error
sub qword ptr [rbx+16], 12
jl Error
//       0x5d6d: PUSH2 0x2ffa
//     0x5d70: Jump
jmp B2ffa
//   0x5d71:
B5d71:
cmp qword ptr [rsp+48], 4
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 43
jl Error
//       0x5d72: DUP1
//       0x5d73: DUP3
//       0x5d74: MOD
lea rsi, qword ptr [rbp-64]
lea rdx, qword ptr [rbp-32]
lea rdi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+5496]
//       0x5d75: ISZERO
mov r13, qword ptr [rbp]
mov r15, qword ptr [rbp+8]
mov r14, qword ptr [rbp+16]
mov r12, qword ptr [rbp+24]
or r13, r15
or r14, r12
or r13, r14
//       0x5d76: ISZERO
//       0x5d77: SWAP2
//       0x5d78: DIV
setne al
movzx eax, al
vmovd xmm0, eax
vmovaps qword ptr [rbp], ymm0
lea rsi, qword ptr [rbp-64]
lea rdx, qword ptr [rbp-32]
lea rdi, qword ptr [rbp-32]
vzeroupper
call qword ptr [ROD+2808]
//       0x5d79: ADD
mov r13, qword ptr [rbp-32]
mov r15, qword ptr [rbp-24]
mov r14, qword ptr [rbp-16]
mov r12, qword ptr [rbp-8]
add r13, qword ptr [rbp]
adc r15, qword ptr [rbp+8]
adc r14, qword ptr [rbp+16]
adc r12, qword ptr [rbp+24]
//       0x5d7a: AND
and r13, qword ptr [rbp-96]
and r15, qword ptr [rbp-88]
and r14, qword ptr [rbp-80]
and r12, qword ptr [rbp-72]
//       0x5d7b: SWAP1
//     0x5d7c: Jump
mov r10, qword ptr [rbp-128]
mov r11, qword ptr [rbp-120]
mov r8, qword ptr [rbp-112]
mov r9, qword ptr [rbp-104]
mov qword ptr [rbp-128], r13
mov qword ptr [rbp-120], r15
mov qword ptr [rbp-112], r14
mov qword ptr [rbp-104], r12
add qword ptr [rsp+48], -3
add rbp, -96
cmp r10, 24009
jnb Error
or r11, r8
or r11, r9
jnz Error
lea rax, [JumpTable]
movsxd rcx, dword ptr [rax+r10*4]
add rax, rcx
jmp rax
