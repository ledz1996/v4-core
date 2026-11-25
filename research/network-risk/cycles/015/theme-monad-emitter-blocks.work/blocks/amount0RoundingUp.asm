//   0x5c91:
B5c91:
cmp qword ptr [rsp+48], 3
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 26
jl Error
//       0x5c92: SWAP2
//       0x5c93: SWAP1
//       0x5c94: DUP2
//       0x5c95: ISZERO
vmovaps ymm0, qword ptr [rbp-96]
vptest ymm0, ymm0
//       0x5c96: PUSH2 0x5d02
//     0x5c99: JumpI 897
jne L1627
vmovaps ymm1, qword ptr [rbp-32]
vmovaps qword ptr [rbp-96], ymm1
vmovaps ymm1, qword ptr [rbp-64]
vmovaps qword ptr [rbp-32], ymm1
vmovaps qword ptr [rbp-64], ymm0
jmp B5d02
L1627:
//   0x5c9a:
cmp qword ptr [rsp+48], 1020
ja Error
sub qword ptr [rbx+16], 86
//       0x5c9a: PUSH28 0xffffffffffffffffffffffffffffffff000000000000000000000000
//       0x5cb7: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0x5ccc: SWAP2
//       0x5ccd: PUSH1 0x60
//       0x5ccf: SHL
mov r12, qword ptr [rbp-48]
mov r14, qword ptr [rbp-56]
mov r15, qword ptr [rbp-64]
xor r13d, r13d
shld r12, r14, 32
shld r14, r15, 32
shl r15, 32
//       0x5cd0: AND
and r13, 0
and r15, qword ptr [ROD+6152]
and r12, qword ptr [ROD+6168]
//       0x5cd1: SWAP3
//       0x5cd2: AND
vmovaps ymm1, qword ptr [ROD+1152]
vpand ymm1, ymm1, qword ptr [rbp-32]
//       0x5cd3: SWAP2
//       0x5cd4: DUP3
//       0x5cd5: DUP3
//       0x5cd6: MUL
vmovaps qword ptr [rbp-64], ymm1
lea rsi, qword ptr [rbp-96]
lea rdx, qword ptr [rbp-64]
lea rdi, qword ptr [rbp]
call qword ptr [ROD+4608]
//       0x5cd7: SWAP2
//       0x5cd8: DUP4
//       0x5cd9: DUP4
//       0x5cda: DUP4
//       0x5cdb: GT
mov r10, qword ptr [rbp]
mov r11, qword ptr [rbp+8]
mov r8, qword ptr [rbp+16]
mov r9, qword ptr [rbp+24]
cmp r10, r13
sbb r11, r15
sbb r8, r14
sbb r9, r12
//       0x5cdc: SWAP2
//       0x5cdd: DUP5
//       0x5cde: DIV
setb al
movzx eax, al
vmovd xmm2, eax
vmovaps qword ptr [rbp-32], ymm2
lea rsi, qword ptr [rbp]
lea rdx, qword ptr [rbp-96]
lea rdi, qword ptr [rbp+64]
vzeroupper
call qword ptr [ROD+2808]
//       0x5cdf: EQ
mov r10, qword ptr [rbp+64]
mov r11, qword ptr [rbp+72]
mov r8, qword ptr [rbp+80]
mov r9, qword ptr [rbp+88]
xor r10, qword ptr [rbp-64]
xor r11, qword ptr [rbp-56]
xor r8, qword ptr [rbp-48]
xor r9, qword ptr [rbp-40]
or r10, r11
or r8, r9
or r10, r8
//       0x5ce0: AND
sete al
movzx eax, al
vmovd xmm0, eax
vpand ymm0, ymm0, qword ptr [rbp-32]
//       0x5ce1: ISZERO
vptest ymm0, ymm0
//       0x5ce2: PUSH2 0x5cf5
//     0x5ce5: JumpI 898
jne L1628
mov qword ptr [rbp-32], r13
mov qword ptr [rbp-24], r15
mov qword ptr [rbp-16], r14
mov qword ptr [rbp-8], r12
vmovaps ymm0, qword ptr [rbp-64]
vmovaps qword ptr [rbp-96], ymm0
vmovq xmm0, qword ptr [rbp]
vmovq xmm1, qword ptr [rbp+16]
vpinsrq xmm0, xmm0, qword ptr [rbp+8], 1
vpinsrq xmm1, xmm1, qword ptr [rbp+24], 1
vinserti128 ymm0, ymm0, xmm1, 1
vmovaps qword ptr [rbp-64], ymm0
jmp B5cf5
L1628:
//   0x5ce6:
sub qword ptr [rbx+16], 32
//       0x5ce6: PUSH2 0x364f
//       0x5ce9: SWAP3
//       0x5cea: PUSH2 0x5030
//       0x5ced: SWAP3
//       0x5cee: DUP3
//       0x5cef: SUB
mov r10, r13
mov r11, r15
mov r8, r14
mov r9, r12
sub r13, qword ptr [rbp]
sbb r15, qword ptr [rbp+8]
sbb r14, qword ptr [rbp+16]
sbb r12, qword ptr [rbp+24]
//       0x5cf0: SWAP2
//       0x5cf1: PUSH2 0x5c68
//     0x5cf4: Jump
mov qword ptr [rbp+32], r10
mov qword ptr [rbp+40], r11
mov qword ptr [rbp+48], r8
mov qword ptr [rbp+56], r9
vmovaps ymm0, qword ptr [rbp-64]
vmovaps qword ptr [rbp], ymm0
vmovd xmm0, dword ptr [ROD+5428]
vmovaps qword ptr [rbp-64], ymm0
mov qword ptr [rbp-32], r13
mov qword ptr [rbp-24], r15
mov qword ptr [rbp-16], r14
mov qword ptr [rbp-8], r12
vmovd xmm0, dword ptr [ROD+3836]
vmovaps qword ptr [rbp-96], ymm0
add qword ptr [rsp+48], 2
add rbp, 64
jmp B5c68
//   0x5cf5:
B5cf5:
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 15
jl Error
//       0x5cf6: PUSH4 0xf5c787f1
//       0x5cfb: PUSH0
//       0x5cfc: MSTORE
cmp dword ptr [rbx+264], 32
jae L1629
mov rdi, 32
call qword ptr [ROD]
L1629:
mov rax, qword ptr [rbx+272]
vmovaps ymm0, qword ptr [ROD+6496]
vmovups qword ptr [rax], ymm0
//       0x5cfd: PUSH1 0x4
//       0x5cff: PUSH1 0x1c
//     0x5d01: Revert
mov qword ptr [rbx+256], 1
vmovd xmm0, dword ptr [ROD+4492]
vmovups qword ptr [rbx+192], ymm0
vmovd xmm1, dword ptr [ROD+1540]
vmovups qword ptr [rbx+224], ymm1
jmp ContractEpilogue
//   0x5d02:
B5d02:
cmp qword ptr [rsp+48], 4
jb Error
sub qword ptr [rbx+16], 16
jl Error
//       0x5d03: POP
//       0x5d04: POP
//       0x5d05: SWAP1
//     0x5d06: Jump
mov r13, qword ptr [rbp-128]
mov r15, qword ptr [rbp-120]
mov r14, qword ptr [rbp-112]
mov r12, qword ptr [rbp-104]
vmovaps ymm0, qword ptr [rbp-96]
vmovaps qword ptr [rbp-128], ymm0
add qword ptr [rsp+48], -3
add rbp, -96
cmp r13, 24009
jnb Error
or r15, r14
or r15, r12
jnz Error
lea rax, [JumpTable]
movsxd rcx, dword ptr [rax+r13*4]
add rax, rcx
jmp rax
//   0x5d07:
B5d07:
cmp qword ptr [rsp+48], 3
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 26
jl Error
//       0x5d08: SWAP1
//       0x5d09: SWAP2
//       0x5d0a: DUP1
//       0x5d0b: ISZERO
vmovaps ymm0, qword ptr [rbp-96]
vptest ymm0, ymm0
//       0x5d0c: PUSH2 0x5d95
//     0x5d0f: JumpI 902
jne L1630
vmovaps ymm1, qword ptr [rbp-64]
vmovaps qword ptr [rbp-96], ymm1
vmovaps ymm1, qword ptr [rbp-32]
vmovaps qword ptr [rbp-64], ymm1
vmovaps qword ptr [rbp-32], ymm0
jmp B5d95
L1630:
//   0x5d10:
cmp qword ptr [rsp+48], 1017
ja Error
sub qword ptr [rbx+16], 61
//       0x5d10: PUSH20 0xffffffffffffffffffffffffffffffffffffffff
//       0x5d25: PUSH28 0xffffffffffffffffffffffffffffffff000000000000000000000000
//       0x5d42: DUP2
//       0x5d43: SWAP5
//       0x5d44: PUSH1 0x60
//       0x5d46: SHL
mov r12, qword ptr [rbp-48]
mov r14, qword ptr [rbp-56]
mov r15, qword ptr [rbp-64]
xor r13d, r13d
shld r12, r14, 32
shld r14, r15, 32
shl r15, 32
//       0x5d47: AND
and r13, 0
and r15, qword ptr [ROD+6152]
and r12, qword ptr [ROD+6168]
//       0x5d48: SWAP3
//       0x5d49: AND
vmovaps ymm1, qword ptr [ROD+1152]
vpand ymm2, ymm1, qword ptr [rbp-32]
//       0x5d4a: DUP1
//       0x5d4b: DUP3
//       0x5d4c: MUL
vmovaps qword ptr [rbp], ymm2
lea rsi, qword ptr [rbp-96]
lea rdx, qword ptr [rbp]
lea rdi, qword ptr [rbp+32]
call qword ptr [ROD+4608]
//       0x5d4d: DUP2
//       0x5d4e: PUSH2 0x5d57
//       0x5d51: DUP5
//       0x5d52: DUP4
//       0x5d53: PUSH2 0x4922
//     0x5d56: Jump
vmovd xmm3, dword ptr [ROD+6104]
vmovaps qword ptr [rbp+96], ymm3
vmovq xmm3, qword ptr [rbp+32]
vmovq xmm4, qword ptr [rbp+48]
vpinsrq xmm3, xmm3, qword ptr [rbp+40], 1
vpinsrq xmm4, xmm4, qword ptr [rbp+56], 1
vinserti128 ymm3, ymm3, xmm4, 1
vmovaps qword ptr [rbp+160], ymm3
vmovaps qword ptr [rbp+64], ymm2
vmovaps qword ptr [rbp-32], ymm0
vmovaps qword ptr [rbp+128], ymm0
mov qword ptr [rbp-64], r13
mov qword ptr [rbp-56], r15
mov qword ptr [rbp-48], r14
mov qword ptr [rbp-40], r12
vmovaps qword ptr [rbp-96], ymm1
add qword ptr [rsp+48], 6
add rbp, 192
jmp B4922
//   0x5d57:
B5d57:
cmp qword ptr [rsp+48], 2
jb Error
sub qword ptr [rbx+16], 17
jl Error
//       0x5d58: EQ
vmovaps ymm0, qword ptr [rbp-32]
vpxor ymm0, ymm0, qword ptr [rbp-64]
vptest ymm0, ymm0
//       0x5d59: PUSH2 0x5d7d
//     0x5d5c: JumpI 904
mov rax, qword ptr [rsp+48]
lea rax, [rax-2]
lea rbp, [rbp-64]
mov qword ptr [rsp+48], rax
je B5d7d
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
//   0x5d7d:
B5d7d:
cmp qword ptr [rsp+48], 4
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 29
jl Error
//       0x5d7e: DUP4
//       0x5d7f: ADD
mov r13, qword ptr [rbp-128]
mov r15, qword ptr [rbp-120]
mov r14, qword ptr [rbp-112]
mov r12, qword ptr [rbp-104]
add r13, qword ptr [rbp-32]
adc r15, qword ptr [rbp-24]
adc r14, qword ptr [rbp-16]
adc r12, qword ptr [rbp-8]
//       0x5d80: DUP4
//       0x5d81: DUP2
//       0x5d82: LT
mov r10, r13
mov r11, r15
mov r8, r14
mov r9, r12
cmp r13, qword ptr [rbp-128]
sbb r15, qword ptr [rbp-120]
sbb r14, qword ptr [rbp-112]
sbb r12, qword ptr [rbp-104]
//       0x5d83: PUSH2 0x5d5d
//     0x5d86: JumpI 908
jae L1631
mov qword ptr [rbp-32], r10
mov qword ptr [rbp-24], r11
mov qword ptr [rbp-16], r8
mov qword ptr [rbp-8], r9
jmp B5d5d
L1631:
//   0x5d87:
sub qword ptr [rbx+16], 22
//       0x5d87: SWAP2
//       0x5d88: POP
//       0x5d89: PUSH2 0x5d91
//       0x5d8c: SWAP3
//       0x5d8d: PUSH2 0x5c68
//     0x5d90: Jump
vmovaps ymm0, qword ptr [rbp-128]
vmovaps qword ptr [rbp-32], ymm0
vmovd xmm0, dword ptr [ROD+6532]
vmovaps qword ptr [rbp-128], ymm0
mov qword ptr [rbp-96], r10
mov qword ptr [rbp-88], r11
mov qword ptr [rbp-80], r8
mov qword ptr [rbp-72], r9
jmp B5c68
//   0x5d91:
B5d91:
cmp qword ptr [rsp+48], 3
jb Error
sub qword ptr [rbx+16], 15
jl Error
//       0x5d92: AND
vmovaps ymm0, qword ptr [rbp-32]
vpand ymm0, ymm0, qword ptr [rbp-64]
//       0x5d93: SWAP1
//     0x5d94: Jump
mov r13, qword ptr [rbp-96]
mov r15, qword ptr [rbp-88]
mov r14, qword ptr [rbp-80]
mov r12, qword ptr [rbp-72]
vmovaps qword ptr [rbp-96], ymm0
add qword ptr [rsp+48], -2
add rbp, -64
cmp r13, 24009
jnb Error
or r15, r14
or r15, r12
jnz Error
lea rax, [JumpTable]
movsxd rcx, dword ptr [rax+r13*4]
add rax, rcx
jmp rax
//   0x5d95:
B5d95:
cmp qword ptr [rsp+48], 4
jb Error
sub qword ptr [rbx+16], 19
jl Error
//       0x5d96: POP
//       0x5d97: SWAP1
//       0x5d98: POP
//       0x5d99: SWAP1
//     0x5d9a: Jump
mov r13, qword ptr [rbp-128]
mov r15, qword ptr [rbp-120]
mov r14, qword ptr [rbp-112]
mov r12, qword ptr [rbp-104]
vmovaps ymm0, qword ptr [rbp-64]
vmovaps qword ptr [rbp-128], ymm0
add qword ptr [rsp+48], -3
add rbp, -96
cmp r13, 24009
jnb Error
or r15, r14
or r15, r12
jnz Error
lea rax, [JumpTable]
movsxd rcx, dword ptr [rax+r13*4]
add rax, rcx
jmp rax
