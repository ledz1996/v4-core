package main

// OpCode values as in erigon execution/vm/opcodes.go (and the Yellow Paper).
type OpCode byte

const (
	JUMPDEST OpCode = 0x5b
	PUSH1    OpCode = 0x60
)
