//   0x25d3:
cmp qword ptr [rsp+48], 1
jb Error
cmp qword ptr [rsp+48], 1021
ja Error
sub qword ptr [rbx+16], 20
//       0x25d3: PUSH2 0x7a2
//       0x25d6: PUSH1 0x20
//       0x25d8: SWAP2
//       0x25d9: PUSH2 0x342d
//     0x25dc: Jump
vmovaps ymm0, qword ptr [rbp-32]
vmovaps qword ptr [rbp+32], ymm0
vmovd xmm0, dword ptr [ROD+1368]
vmovaps qword ptr [rbp-32], ymm0
vmovd xmm0, dword ptr [ROD+1648]
vmovaps qword ptr [rbp], ymm0
add qword ptr [rsp+48], 2
add rbp, 64
jmp B342d
//   0x2ad6:
cmp qword ptr [rsp+48], 1020
ja Error
sub qword ptr [rbx+16], 19
//       0x2ad6: PUSH1 0x20
//       0x2ad8: PUSH2 0x7a2
//       0x2adb: CALLER
movbe r14d, dword ptr [rbx+60]
movbe r13, qword ptr [rbx+64]
movbe r12, qword ptr [rbx+72]
xor r15d, r15d
//       0x2adc: PUSH2 0x342d
//     0x2adf: Jump
mov qword ptr [rbp+64], r12
mov qword ptr [rbp+72], r13
mov qword ptr [rbp+80], r14
mov qword ptr [rbp+88], r15
vmovd xmm0, dword ptr [ROD+1648]
vmovaps qword ptr [rbp+32], ymm0
vmovd xmm0, dword ptr [ROD+1368]
vmovaps qword ptr [rbp], ymm0
add qword ptr [rsp+48], 3
add rbp, 96
jmp B342d
//   0x2b4b:
cmp qword ptr [rsp+48], 2
jb Error
cmp qword ptr [rsp+48], 1018
ja Error
sub qword ptr [rbx+16], 26
//       0x2b4b: PUSH2 0xe2f
//       0x2b4e: SWAP3
//       0x2b4f: PUSH2 0x2b67
//       0x2b52: PUSH2 0x2b5a
//       0x2b55: DUP5
//       0x2b56: PUSH2 0x30aa
//     0x2b59: Jump
vmovd xmm0, dword ptr [ROD+3496]
vmovaps qword ptr [rbp+96], ymm0
vmovd xmm0, dword ptr [ROD+3500]
vmovaps qword ptr [rbp+64], ymm0
vmovaps ymm0, qword ptr [rbp-64]
vmovaps qword ptr [rbp+32], ymm0
vmovd xmm0, dword ptr [ROD+2016]
vmovaps qword ptr [rbp-64], ymm0
vmovaps ymm0, qword ptr [rbp-32]
vmovaps ymm1, qword ptr [rbp]
vmovaps qword ptr [rbp], ymm0
vmovaps qword ptr [rbp-32], ymm1
vmovaps qword ptr [rbp+128], ymm1
add qword ptr [rsp+48], 5
add rbp, 160
jmp B30aa
//   0x2b5a:
B2b5a:
cmp qword ptr [rsp+48], 3
jb Error
cmp qword ptr [rsp+48], 1021
ja Error
sub qword ptr [rbx+16], 33
jl Error
//       0x2b5b: PUSH0
//       0x2b5c: SUB
xor r12d, r12d
xor r13d, r13d
xor r14d, r14d
xor r15d, r15d
sub r12, qword ptr [rbp-32]
sbb r13, qword ptr [rbp-24]
sbb r14, qword ptr [rbp-16]
sbb r15, qword ptr [rbp-8]
//       0x2b5d: PUSH1 0xf
//       0x2b5f: SIGNEXTEND
mov r14, r13
sar r14, 63
mov r15, r14
//       0x2b60: CALLER
movbe r8d, dword ptr [rbx+60]
movbe r11, qword ptr [rbx+64]
movbe r10, qword ptr [rbx+72]
xor r9d, r9d
//       0x2b61: SWAP1
//       0x2b62: DUP4
//       0x2b63: PUSH2 0x30f0
//     0x2b66: Jump
mov qword ptr [rbp], r12
mov qword ptr [rbp+8], r13
mov qword ptr [rbp+16], r14
mov qword ptr [rbp+24], r15
mov qword ptr [rbp-32], r10
mov qword ptr [rbp-24], r11
mov qword ptr [rbp-16], r8
mov qword ptr [rbp-8], r9
vmovaps ymm0, qword ptr [rbp-96]
vmovaps qword ptr [rbp+32], ymm0
add qword ptr [rsp+48], 2
add rbp, 64
jmp B30f0
//   0x2b67:
B2b67:
cmp qword ptr [rsp+48], 1023
ja Error
sub qword ptr [rbx+16], 12
jl Error
//       0x2b68: PUSH2 0x31f8
//     0x2b6b: Jump
jmp B31f8
