// Harness: compares erigon v3.8.1 codeBitmapSSE4 and codeBitmapGeneric with an independent scalar
// JUMPDEST rule on given bytecode files and on random and constructed byte strings.
package main

import (
	"encoding/hex"
	"fmt"
	"math/rand"
	"os"
	"strings"
)

func ref(code []byte) []bool {
	r := make([]bool, len(code))
	for pc := 0; pc < len(code); pc++ {
		op := code[pc]
		if op >= 0x60 && op <= 0x7f {
			pc += int(op) - 0x5f
		} else if op == 0x5b {
			r[pc] = true
		}
	}
	return r
}

func check(code []byte, name string) int {
	want := ref(code)
	bad := 0
	for _, f := range []struct {
		n string
		g func([]byte) bitvec
	}{{"sse4", codeBitmapSSE4}, {"generic", codeBitmapGeneric}} {
		b := f.g(code)
		for i := range code {
			if b.isJumpdest(uint64(i)) != want[i] {
				if bad < 5 {
					fmt.Printf("MISMATCH %s %s len %d pos %d want %v\n", name, f.n, len(code), i, want[i])
				}
				bad++
			}
		}
		// bits beyond len must be zero
		for i := len(code); i < len(b)*64; i++ {
			if b.isJumpdest(uint64(i)) {
				if bad < 5 {
					fmt.Printf("TAILBIT %s %s len %d pos %d\n", name, f.n, len(code), i)
				}
				bad++
			}
		}
	}
	return bad
}

func main() {
	total, bad := 0, 0
	for _, p := range os.Args[1:] {
		raw, _ := os.ReadFile(p)
		code, err := hex.DecodeString(strings.TrimPrefix(strings.TrimSpace(string(raw)), "0x"))
		if err != nil {
			panic(err)
		}
		n := check(code, p)
		fmt.Printf("file %s len %d jumpdests %d mismatches %d\n", p, len(code), cnt(ref(code)), n)
		bad += n
		total++
		// every suffix and prefix cut of the file, to move the 32-byte step boundaries
		for k := 0; k < 96; k++ {
			bad += check(code[k:], p)
			bad += check(code[:len(code)-k], p)
			total += 2
		}
	}
	rng := rand.New(rand.NewSource(24024))
	alpha := []byte{0x5b, 0x5b, 0x60, 0x61, 0x6f, 0x7e, 0x7f, 0x5f, 0x80, 0xff, 0x00, 0x56, 0x57, 0x5a, 0x5c}
	for t := 0; t < 400000; t++ {
		n := rng.Intn(300)
		c := make([]byte, n)
		mode := t % 4
		for i := range c {
			switch mode {
			case 0:
				c[i] = byte(rng.Intn(256))
			case 1:
				c[i] = alpha[rng.Intn(len(alpha))]
			case 2:
				if rng.Intn(3) == 0 {
					c[i] = byte(0x60 + rng.Intn(32))
				} else {
					c[i] = 0x5b
				}
			default:
				c[i] = byte(0x5a + rng.Intn(0x28)) // 0x5a..0x81, around both push edges
			}
		}
		bad += check(c, "rand")
		total++
	}
	// every single push opcode at every offset inside a field of JUMPDESTs
	for n := 0; n <= 130; n++ {
		for op := 0x5f; op <= 0x80; op++ {
			for pos := 0; pos < n; pos++ {
				c := make([]byte, n)
				for i := range c {
					c[i] = 0x5b
				}
				c[pos] = byte(op)
				bad += check(c, "single")
				total++
			}
		}
	}
	fmt.Printf("cases %d mismatches %d\n", total, bad)
}

func cnt(b []bool) int {
	n := 0
	for _, x := range b {
		if x {
			n++
		}
	}
	return n
}
