//   0x28f2:
B28f2:
cmp qword ptr [rsp+48], 12
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 250
jl Error
//       0x28f3: PUSH1 0x2
//       0x28f5: ADD
mov r12, qword ptr [rbp-32]
mov r13, qword ptr [rbp-24]
mov r14, qword ptr [rbp-16]
mov r15, qword ptr [rbp-8]
add r12, 2
adc r13, 0
adc r14, 0
adc r15, 0
//       0x28f6: SWAP1
//       0x28f7: DUP7
//       0x28f8: PUSH1 0x80
//       0x28fa: SHL
mov r9, qword ptr [rbp-216]
mov r8, qword ptr [rbp-224]
xor r11d, r11d
xor r10d, r10d
//       0x28fb: DIV
mov qword ptr [rbp], r10
mov qword ptr [rbp+8], r11
mov qword ptr [rbp+16], r8
mov qword ptr [rbp+24], r9
lea rsi, qword ptr [rbp]
lea rdx, qword ptr [rbp-64]
lea rdi, qword ptr [rbp-32]
vzeroupper
call qword ptr [ROD+2808]
//       0x28fc: DUP2
//       0x28fd: SLOAD
mov qword ptr [rbp-64], r12
mov qword ptr [rbp-56], r13
mov qword ptr [rbp-48], r14
mov qword ptr [rbp-40], r15
lea rdx, qword ptr [rbp-64]
mov rdi, rbx
lea rsi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+1200]
//       0x28fe: ADD
mov r10, qword ptr [rbp]
mov r11, qword ptr [rbp+8]
mov r8, qword ptr [rbp+16]
mov r9, qword ptr [rbp+24]
add r10, qword ptr [rbp-32]
adc r11, qword ptr [rbp-24]
adc r8, qword ptr [rbp-16]
adc r9, qword ptr [rbp-8]
//       0x28ff: SWAP1
//       0x2900: SSTORE
mov qword ptr [rbp-32], r10
mov qword ptr [rbp-24], r11
mov qword ptr [rbp-16], r8
mov qword ptr [rbp-8], r9
lea rsi, qword ptr [rbp-64]
lea rdx, qword ptr [rbp-32]
mov rdi, rbx
mov rcx, 17
vzeroupper
call qword ptr [ROD+1344]
//       0x2901: DUP10
//       0x2902: DUP1
//       0x2903: PUSH2 0x282c
//     0x2906: Jump
vmovaps ymm0, qword ptr [rbp-384]
vmovaps qword ptr [rbp-64], ymm0
vmovaps qword ptr [rbp-32], ymm0
jmp B282c
//   0x2907:
B2907:
cmp qword ptr [rsp+48], 8
jb Error
cmp qword ptr [rsp+48], 1020
ja Error
sub qword ptr [rbx+16], 247
jl Error
//       0x2908: PUSH1 0x1
//       0x290a: DUP2
//       0x290b: ADD
mov r12, qword ptr [rbp-32]
mov r13, qword ptr [rbp-24]
mov r14, qword ptr [rbp-16]
mov r15, qword ptr [rbp-8]
add r12, 1
adc r13, 0
adc r14, 0
adc r15, 0
//       0x290c: DUP3
//       0x290d: DUP10
//       0x290e: PUSH1 0x80
//       0x2910: SHL
mov r9, qword ptr [rbp-248]
mov r8, qword ptr [rbp-256]
xor r11d, r11d
xor r10d, r10d
//       0x2911: DIV
mov qword ptr [rbp+64], r10
mov qword ptr [rbp+72], r11
mov qword ptr [rbp+80], r8
mov qword ptr [rbp+88], r9
lea rsi, qword ptr [rbp+64]
lea rdx, qword ptr [rbp-64]
lea rdi, qword ptr [rbp+32]
vzeroupper
call qword ptr [ROD+2808]
//       0x2912: DUP2
//       0x2913: SLOAD
mov qword ptr [rbp], r12
mov qword ptr [rbp+8], r13
mov qword ptr [rbp+16], r14
mov qword ptr [rbp+24], r15
lea rdx, qword ptr [rbp]
mov rdi, rbx
lea rsi, qword ptr [rbp+64]
vzeroupper
call qword ptr [ROD+1200]
//       0x2914: ADD
mov r10, qword ptr [rbp+64]
mov r11, qword ptr [rbp+72]
mov r8, qword ptr [rbp+80]
mov r9, qword ptr [rbp+88]
add r10, qword ptr [rbp+32]
adc r11, qword ptr [rbp+40]
adc r8, qword ptr [rbp+48]
adc r9, qword ptr [rbp+56]
//       0x2915: SWAP1
//       0x2916: SSTORE
mov qword ptr [rbp+32], r10
mov qword ptr [rbp+40], r11
mov qword ptr [rbp+48], r8
mov qword ptr [rbp+56], r9
lea rsi, qword ptr [rbp]
lea rdx, qword ptr [rbp+32]
mov rdi, rbx
mov rcx, 11
vzeroupper
call qword ptr [ROD+1344]
//       0x2917: PUSH2 0x2826
//     0x291a: Jump
jmp B2826
//   0x4efe:
B4efe:
cmp qword ptr [rsp+48], 11
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 64
jl Error
//       0x4eff: PUSH1 0xc0
//       0x4f01: DUP12
//       0x4f02: ADD
mov r13, qword ptr [rbp-352]
mov r14, qword ptr [rbp-344]
mov r15, qword ptr [rbp-336]
mov r12, qword ptr [rbp-328]
add r13, 192
adc r14, 0
adc r15, 0
adc r12, 0
//       0x4f03: MLOAD
mov rax, r13
and r13, -268435456
or r12, r15
or r14, r13
or r12, r14
jnz Error
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L1562
call qword ptr [ROD]
L1562:
add rax, qword ptr [rbx+272]
movbe r12, qword ptr [rax]
movbe r15, qword ptr [rax+8]
movbe r14, qword ptr [rax+16]
movbe r13, qword ptr [rax+24]
//       0x4f04: PUSH1 0x80
//       0x4f06: SHL
xor r12d, r12d
xor r15d, r15d
//       0x4f07: DIV
mov qword ptr [rbp], r15
mov qword ptr [rbp+8], r12
mov qword ptr [rbp+16], r13
mov qword ptr [rbp+24], r14
lea rsi, qword ptr [rbp]
lea rdx, qword ptr [rbp-32]
lea rdi, qword ptr [rbp-32]
vzeroupper
call qword ptr [ROD+2808]
//       0x4f08: PUSH1 0xe0
//       0x4f0a: DUP12
//       0x4f0b: ADD
mov r15, qword ptr [rbp-352]
mov r12, qword ptr [rbp-344]
mov r13, qword ptr [rbp-336]
mov r14, qword ptr [rbp-328]
add r15, 224
adc r12, 0
adc r13, 0
adc r14, 0
//       0x4f0c: MLOAD
mov rax, r15
and r15, -268435456
or r14, r13
or r12, r15
or r14, r12
jnz Error
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L1563
call qword ptr [ROD]
L1563:
add rax, qword ptr [rbx+272]
movbe r14, qword ptr [rax]
movbe r13, qword ptr [rax+8]
movbe r12, qword ptr [rax+16]
movbe r15, qword ptr [rax+24]
//       0x4f0d: ADD
add r15, qword ptr [rbp-32]
adc r12, qword ptr [rbp-24]
adc r13, qword ptr [rbp-16]
adc r14, qword ptr [rbp-8]
//       0x4f0e: PUSH1 0xe0
//       0x4f10: DUP12
//       0x4f11: ADD
mov r10, qword ptr [rbp-352]
mov r11, qword ptr [rbp-344]
mov r8, qword ptr [rbp-336]
mov r9, qword ptr [rbp-328]
add r10, 224
adc r11, 0
adc r8, 0
adc r9, 0
//       0x4f12: MSTORE
mov rax, r10
and r10, -268435456
or r9, r8
or r11, r10
or r9, r11
jnz Error
lea rdi, byte ptr [rax+32]
cmp dword ptr [rbx+264], edi
jae L1564
call qword ptr [ROD]
L1564:
add rax, qword ptr [rbx+272]
movbe qword ptr [rax], r14
movbe qword ptr [rax+8], r13
movbe qword ptr [rax+16], r12
movbe qword ptr [rax+24], r15
//       0x4f13: PUSH0
//       0x4f14: PUSH2 0x4d79
//     0x4f17: Jump
vpxor ymm0, ymm0, ymm0
vmovaps qword ptr [rbp-32], ymm0
jmp B4d79
//   0x5129:
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 46
//       0x5129: DUP5
//       0x512a: PUSH1 0x60
//       0x512c: SHL
mov r14, qword ptr [rbp-208]
mov r13, qword ptr [rbp-216]
mov r12, qword ptr [rbp-224]
xor r15d, r15d
shld r14, r13, 32
shld r13, r12, 32
shl r12, 32
//       0x512d: PUSH16 0xffffffffffffffffffffffffffffffff
//       0x513e: DUP6
//       0x513f: AND
vpand ymm3, ymm0, qword ptr [ROD+2880]
//       0x5140: DUP1
//       0x5141: DUP3
//       0x5142: MOD
vmovaps qword ptr [rbp-32], ymm3
mov qword ptr [rbp-128], r15
mov qword ptr [rbp-120], r12
mov qword ptr [rbp-112], r13
mov qword ptr [rbp-104], r14
lea rsi, qword ptr [rbp-128]
lea rdx, qword ptr [rbp-32]
lea rdi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+5496]
//       0x5143: ISZERO
mov r10, qword ptr [rbp]
mov r11, qword ptr [rbp+8]
mov r8, qword ptr [rbp+16]
mov r9, qword ptr [rbp+24]
or r10, r11
or r8, r9
or r10, r8
//       0x5144: ISZERO
//       0x5145: SWAP2
//       0x5146: DIV
setne al
movzx eax, al
vmovd xmm0, eax
vmovaps qword ptr [rbp-96], ymm0
lea rsi, qword ptr [rbp-128]
lea rdx, qword ptr [rbp-32]
lea rdi, qword ptr [rbp-32]
vzeroupper
call qword ptr [ROD+2808]
//       0x5147: ADD
mov r15, qword ptr [rbp-32]
mov r12, qword ptr [rbp-24]
mov r13, qword ptr [rbp-16]
mov r14, qword ptr [rbp-8]
add r15, qword ptr [rbp-96]
adc r12, qword ptr [rbp-88]
adc r13, qword ptr [rbp-80]
adc r14, qword ptr [rbp-72]
//     FallThrough 809
vmovaps ymm0, qword ptr [rbp-64]
vmovaps qword ptr [rbp-128], ymm0
mov qword ptr [rbp-64], r15
mov qword ptr [rbp-56], r12
mov qword ptr [rbp-48], r13
mov qword ptr [rbp-40], r14
vmovaps ymm0, qword ptr [rbp-224]
vmovaps qword ptr [rbp-96], ymm0
add qword ptr [rsp+48], -1
add rbp, -32
//   0x5b16:
B5b16:
cmp qword ptr [rsp+48], 3
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 43
jl Error
//       0x5b17: SWAP1
//       0x5b18: DUP1
//       0x5b19: DUP3
//       0x5b1a: MOD
lea rsi, qword ptr [rbp-32]
lea rdx, qword ptr [rbp-64]
lea rdi, qword ptr [rbp]
vzeroupper
call qword ptr [ROD+5496]
//       0x5b1b: ISZERO
mov r13, qword ptr [rbp]
mov r15, qword ptr [rbp+8]
mov r14, qword ptr [rbp+16]
mov r12, qword ptr [rbp+24]
or r13, r15
or r14, r12
or r13, r14
//       0x5b1c: ISZERO
//       0x5b1d: SWAP2
//       0x5b1e: DIV
setne al
movzx eax, al
vmovd xmm0, eax
vmovaps qword ptr [rbp], ymm0
lea rsi, qword ptr [rbp-32]
lea rdx, qword ptr [rbp-64]
lea rdi, qword ptr [rbp-32]
vzeroupper
call qword ptr [ROD+2808]
//       0x5b1f: ADD
mov r13, qword ptr [rbp-32]
mov r15, qword ptr [rbp-24]
mov r14, qword ptr [rbp-16]
mov r12, qword ptr [rbp-8]
add r13, qword ptr [rbp]
adc r15, qword ptr [rbp+8]
adc r14, qword ptr [rbp+16]
adc r12, qword ptr [rbp+24]
//       0x5b20: SWAP1
//     0x5b21: Jump
mov r10, qword ptr [rbp-96]
mov r11, qword ptr [rbp-88]
mov r8, qword ptr [rbp-80]
mov r9, qword ptr [rbp-72]
mov qword ptr [rbp-96], r13
mov qword ptr [rbp-88], r15
mov qword ptr [rbp-80], r14
mov qword ptr [rbp-72], r12
add qword ptr [rsp+48], -2
add rbp, -64
cmp r10, 24009
jnb Error
or r11, r8
or r11, r9
jnz Error
lea rax, [JumpTable]
movsxd rcx, dword ptr [rax+r10*4]
add rax, rcx
jmp rax
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
