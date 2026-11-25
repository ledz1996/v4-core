//   0x27cf:
B27cf:
cmp qword ptr [rsp+48], 10
jb Error
cmp qword ptr [rsp+48], 1023
ja Error
sub qword ptr [rbx+16], 142
jl Error
//       0x27d0: POP
//       0x27d1: POP
//       0x27d2: PUSH16 0xffffffffffffffffffffffffffffffff
//       0x27e3: PUSH1 0x3
//       0x27e5: DUP9
//       0x27e6: ADD
mov r12, qword ptr [rbp-288]
mov r13, qword ptr [rbp-280]
mov r14, qword ptr [rbp-272]
mov r15, qword ptr [rbp-264]
add r12, 3
adc r13, 0
adc r14, 0
adc r15, 0
//       0x27e7: SLOAD
mov qword ptr [rbp-64], r12
mov qword ptr [rbp-56], r13
mov qword ptr [rbp-48], r14
mov qword ptr [rbp-40], r15
lea rdx, qword ptr [rbp-64]
mov rdi, rbx
lea rsi, qword ptr [rbp-32]
vzeroupper
call qword ptr [ROD+1200]
//       0x27e8: AND
vpcmpeqd xmm0, xmm0, xmm0
vpand ymm0, ymm0, qword ptr [rbp-32]
//       0x27e9: SWAP8
//       0x27ea: DUP9
//       0x27eb: ISZERO
vptest ymm0, ymm0
//       0x27ec: PUSH2 0x291b
//     0x27ef: JumpI 378
jne L1134
vmovaps ymm1, qword ptr [rbp-320]
vmovaps qword ptr [rbp-64], ymm1
vmovaps qword ptr [rbp-320], ymm0
add qword ptr [rsp+48], -1
add rbp, -32
jmp B291b
L1134:
//   0x27f0:
cmp qword ptr [rsp+48], 1021
ja Error
sub qword ptr [rbx+16], 23
//       0x27f0: PUSH1 0x20
//       0x27f2: SWAP9
//       0x27f3: PUSH2 0x27fb
//       0x27f6: DUP8
//       0x27f7: PUSH2 0x30aa
//     0x27fa: Jump
vmovd xmm1, dword ptr [ROD+3408]
vmovaps qword ptr [rbp], ymm1
vmovaps qword ptr [rbp-32], ymm0
vmovaps ymm0, qword ptr [rbp-320]
vmovaps qword ptr [rbp-64], ymm0
vmovd xmm0, dword ptr [ROD+1368]
vmovaps qword ptr [rbp-320], ymm0
vmovaps ymm0, qword ptr [rbp-224]
vmovaps qword ptr [rbp+32], ymm0
add qword ptr [rsp+48], 2
add rbp, 64
jmp B30aa
//   0x27fb:
B27fb:
cmp qword ptr [rsp+48], 7
jb Error
cmp qword ptr [rsp+48], 1021
ja Error
sub qword ptr [rbx+16], 23
jl Error
//       0x27fc: PUSH0
//       0x27fd: SUB
xor r12d, r12d
xor r13d, r13d
xor r14d, r14d
xor r15d, r15d
sub r12, qword ptr [rbp-32]
sbb r13, qword ptr [rbp-24]
sbb r14, qword ptr [rbp-16]
sbb r15, qword ptr [rbp-8]
//       0x27fe: PUSH2 0x2806
//       0x2801: DUP8
//       0x2802: PUSH2 0x30aa
//     0x2805: Jump
vmovd xmm0, dword ptr [ROD+3412]
vmovaps qword ptr [rbp], ymm0
mov qword ptr [rbp-32], r12
mov qword ptr [rbp-24], r13
mov qword ptr [rbp-16], r14
mov qword ptr [rbp-8], r15
vmovaps ymm0, qword ptr [rbp-224]
vmovaps qword ptr [rbp+32], ymm0
add qword ptr [rsp+48], 2
add rbp, 64
jmp B30aa
//   0x2806:
B2806:
cmp qword ptr [rsp+48], 11
jb Error
cmp qword ptr [rsp+48], 1023
ja Error
sub qword ptr [rbx+16], 43
jl Error
//       0x2807: PUSH0
//       0x2808: SUB
xor r12d, r12d
xor r13d, r13d
xor r14d, r14d
xor r15d, r15d
sub r12, qword ptr [rbp-32]
sbb r13, qword ptr [rbp-24]
sbb r14, qword ptr [rbp-16]
sbb r15, qword ptr [rbp-8]
//       0x2809: PUSH16 0xffffffffffffffffffffffffffffffff
//       0x281a: AND
and r14, 0
and r15, 0
//       0x281b: SWAP1
//       0x281c: PUSH1 0x80
//       0x281e: SHL
mov r9, qword ptr [rbp-56]
mov r8, qword ptr [rbp-64]
xor r11d, r11d
xor r10d, r10d
//       0x281f: OR
or r10, r12
or r11, r13
or r8, r14
or r9, r15
//       0x2820: SWAP9
//       0x2821: DUP8
//       0x2822: PUSH2 0x2907
//     0x2825: JumpI 381
vmovaps ymm0, qword ptr [rbp-288]
vptest ymm0, ymm0
vmovaps ymm1, qword ptr [rbp-352]
vmovaps qword ptr [rbp-64], ymm1
mov qword ptr [rbp-352], r10
mov qword ptr [rbp-344], r11
mov qword ptr [rbp-336], r8
mov qword ptr [rbp-328], r9
mov rax, qword ptr [rsp+48]
lea rax, [rax-1]
lea rbp, [rbp-32]
mov qword ptr [rsp+48], rax
jne B2907
//   0x2826:
B2826:
cmp qword ptr [rsp+48], 7
jb Error
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 17
jl Error
//       0x2827: DUP7
//       0x2828: PUSH2 0x28f2
//     0x282b: JumpI 382
vmovaps ymm0, qword ptr [rbp-224]
vptest ymm0, ymm0
jne B28f2
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
//   0x291b:
B291b:
cmp qword ptr [rsp+48], 1022
ja Error
sub qword ptr [rbx+16], 14
jl Error
//       0x291c: PUSH32 0xa74f97ab00000000000000000000000000000000000000000000000000000000
//       0x293d: PUSH0
//       0x293e: MSTORE
cmp dword ptr [rbx+264], 32
jae L1143
mov rdi, 32
call qword ptr [ROD]
L1143:
mov rax, qword ptr [rbx+272]
vmovd xmm0, dword ptr [ROD+3464]
vmovups qword ptr [rax], ymm0
//       0x293f: PUSH1 0x4
//       0x2941: PUSH0
//     0x2942: Revert
mov qword ptr [rbx+256], 1
vpxor ymm0, ymm0, ymm0
vmovups qword ptr [rbx+192], ymm0
vmovd xmm1, dword ptr [ROD+1540]
vmovups qword ptr [rbx+224], ymm1
jmp ContractEpilogue
