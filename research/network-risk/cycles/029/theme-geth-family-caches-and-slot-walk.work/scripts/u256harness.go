// Runs vectors through holiman/uint256 exactly as go-ethereum core/vm/instructions.go calls it
// (operand aliasing included: y.Div(x, y), z.MulMod(x, y, z), z.AddMod(x, y, z), num.ExtendSign(num, back) ...).
// Input lines: "<op> <a hex> <b hex> <c hex>", output lines: result hex. Analysis tool only.
package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/holiman/uint256"
)

func h(s string) *uint256.Int { v, err := uint256.FromHex(s); if err != nil { panic(s) }; return v }

func main() {
	sc := bufio.NewScanner(os.Stdin)
	sc.Buffer(make([]byte, 1<<20), 1<<20)
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for sc.Scan() {
		f := strings.Fields(sc.Text())
		op := f[0]
		x, y, z := h(f[1]), h(f[2]), h(f[3])
		var r *uint256.Int
		switch op {
		case "DIV": y.Div(x, y); r = y
		case "SDIV": y.SDiv(x, y); r = y
		case "MOD": y.Mod(x, y); r = y
		case "SMOD": y.SMod(x, y); r = y
		case "ADDMOD": z.AddMod(x, y, z); r = z
		case "MULMOD": z.MulMod(x, y, z); r = z
		case "EXP": y.Exp(x, y); r = y
		case "SIGNEXTEND": y.ExtendSign(y, x); r = y
		case "LT": r = new(uint256.Int); if x.Lt(y) { r.SetOne() }
		case "GT": r = new(uint256.Int); if x.Gt(y) { r.SetOne() }
		case "SLT": r = new(uint256.Int); if x.Slt(y) { r.SetOne() }
		case "SGT": r = new(uint256.Int); if x.Sgt(y) { r.SetOne() }
		case "EQ": r = new(uint256.Int); if x.Eq(y) { r.SetOne() }
		case "BYTE": y.Byte(x); r = y
		case "SHL": if x.LtUint64(256) { y.Lsh(y, uint(x.Uint64())) } else { y.Clear() }; r = y
		case "SHR": if x.LtUint64(256) { y.Rsh(y, uint(x.Uint64())) } else { y.Clear() }; r = y
		case "SAR":
			if x.GtUint64(256) { if y.Sign() >= 0 { y.Clear() } else { y.SetAllOne() } } else { y.SRsh(y, uint(x.Uint64())) }
			r = y
		case "MUL": y.Mul(x, y); r = y
		case "ADD": y.Add(x, y); r = y
		case "SUB": y.Sub(x, y); r = y
		case "MULDIV": // FullMath-style quotient of the 512 bit product, low 256 bits
			q, _ := new(uint256.Int).MulDivOverflow(x, y, z); r = q
		case "BYTES32": // WriteToSlice into a 32 byte buffer and back (memory, return data)
			var b [32]byte; x.WriteToSlice(b[:]); r = new(uint256.Int).SetBytes(b[:])
		case "PAD20": // WriteToSlice into a 20 byte buffer (address conversion)
			var b [20]byte; x.WriteToSlice(b[:]); r = new(uint256.Int).SetBytes(b[:])
		default:
			panic(op)
		}
		fmt.Fprintf(w, "%x\n", r.ToBig())
	}
}
