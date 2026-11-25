// Differential test of holiman/uint256 (v1.3.2 and unreleased master de2a0381) against math/big,
// using the operand aliasing of the go-ethereum interpreter handlers (result written into the
// stack slot of the last operand). Usage: u256diff <seed> <randomPairs>
package main

import (
	"fmt"
	"math/big"
	"math/rand"
	"os"
	"strconv"

	a "u256old"
	b "u256new"
)

var M = new(big.Int).Lsh(big.NewInt(1), 256)
var H = new(big.Int).Lsh(big.NewInt(1), 255)

func w(x *big.Int) *big.Int { r := new(big.Int).Mod(x, M); return r }
func s(x *big.Int) *big.Int { // to signed
	if x.Cmp(H) >= 0 { return new(big.Int).Sub(x, M) }
	return new(big.Int).Set(x)
}
func b2i(c bool) *big.Int { if c { return big.NewInt(1) }; return big.NewInt(0) }

func ref(op string, x, y, m *big.Int) *big.Int {
	switch op {
	case "ADD": return w(new(big.Int).Add(x, y))
	case "SUB": return w(new(big.Int).Sub(x, y))
	case "MUL": return w(new(big.Int).Mul(x, y))
	case "DIV": if y.Sign() == 0 { return big.NewInt(0) }; return new(big.Int).Quo(x, y)
	case "MOD": if y.Sign() == 0 { return big.NewInt(0) }; return new(big.Int).Rem(x, y)
	case "SDIV": if y.Sign() == 0 { return big.NewInt(0) }; return w(new(big.Int).Quo(s(x), s(y)))
	case "SMOD": if y.Sign() == 0 { return big.NewInt(0) }; return w(new(big.Int).Rem(s(x), s(y)))
	case "ADDMOD": if m.Sign() == 0 { return big.NewInt(0) }; return new(big.Int).Mod(new(big.Int).Add(x, y), m)
	case "MULMOD": if m.Sign() == 0 { return big.NewInt(0) }; return new(big.Int).Mod(new(big.Int).Mul(x, y), m)
	case "EXP": return new(big.Int).Exp(x, y, M)
	case "SIGNEXTEND": // x = byte index, y = value
		if x.Cmp(big.NewInt(31)) >= 0 { return new(big.Int).Set(y) }
		bit := uint(x.Uint64()*8 + 7)
		mask := new(big.Int).Sub(new(big.Int).Lsh(big.NewInt(1), bit+1), big.NewInt(1))
		v := new(big.Int).And(y, mask)
		if v.Bit(int(bit)) == 1 { v.Or(v, new(big.Int).Xor(new(big.Int).Sub(M, big.NewInt(1)), mask)) }
		return v
	case "BYTE": if x.Cmp(big.NewInt(32)) >= 0 { return big.NewInt(0) }
		return new(big.Int).And(new(big.Int).Rsh(y, uint(8*(31-x.Uint64()))), big.NewInt(255))
	case "SHL": if x.Cmp(big.NewInt(256)) >= 0 { return big.NewInt(0) }; return w(new(big.Int).Lsh(y, uint(x.Uint64())))
	case "SHR": if x.Cmp(big.NewInt(256)) >= 0 { return big.NewInt(0) }; return new(big.Int).Rsh(y, uint(x.Uint64()))
	case "SAR": n := uint(255); if x.Cmp(big.NewInt(256)) < 0 { n = uint(x.Uint64()) }; return w(new(big.Int).Rsh(s(y), n))
	case "LT": return b2i(x.Cmp(y) < 0)
	case "GT": return b2i(x.Cmp(y) > 0)
	case "SLT": return b2i(s(x).Cmp(s(y)) < 0)
	case "SGT": return b2i(s(x).Cmp(s(y)) > 0)
	case "EQ": return b2i(x.Cmp(y) == 0)
	case "MULDIV": if m.Sign() == 0 { return big.NewInt(0) }; return w(new(big.Int).Quo(new(big.Int).Mul(x, y), m))
	}
	panic(op)
}

// runA / runB mirror geth handlers: x popped, y (and m) peeked; result written into the last operand.
func runA(op string, X, Y, Mo *big.Int) *big.Int {
	var x, y, m a.Int
	x.SetFromBig(X); y.SetFromBig(Y); m.SetFromBig(Mo)
	switch op {
	case "ADD": y.Add(&x, &y)
	case "SUB": y.Sub(&x, &y)
	case "MUL": y.Mul(&x, &y)
	case "DIV": y.Div(&x, &y)
	case "MOD": y.Mod(&x, &y)
	case "SDIV": y.SDiv(&x, &y)
	case "SMOD": y.SMod(&x, &y)
	case "ADDMOD": m.AddMod(&x, &y, &m); return m.ToBig()
	case "MULMOD": m.MulMod(&x, &y, &m); return m.ToBig()
	case "EXP": y.Exp(&x, &y)
	case "SIGNEXTEND": y.ExtendSign(&y, &x)
	case "BYTE": y.Byte(&x)
	case "SHL": if x.LtUint64(256) { y.Lsh(&y, uint(x.Uint64())) } else { y.Clear() }
	case "SHR": if x.LtUint64(256) { y.Rsh(&y, uint(x.Uint64())) } else { y.Clear() }
	case "SAR": if x.GtUint64(256) || x.Eq(a.NewInt(256)) { if y.Sign() >= 0 { y.Clear() } else { y.SetAllOne() } } else { y.SRsh(&y, uint(x.Uint64())) }
	case "LT": if x.Lt(&y) { y.SetOne() } else { y.Clear() }
	case "GT": if x.Gt(&y) { y.SetOne() } else { y.Clear() }
	case "SLT": if x.Slt(&y) { y.SetOne() } else { y.Clear() }
	case "SGT": if x.Sgt(&y) { y.SetOne() } else { y.Clear() }
	case "EQ": if x.Eq(&y) { y.SetOne() } else { y.Clear() }
	case "MULDIV": var z a.Int; z.MulDivOverflow(&x, &y, &m); return z.ToBig()
	}
	return y.ToBig()
}
func runB(op string, X, Y, Mo *big.Int) *big.Int {
	var x, y, m b.Int
	x.SetFromBig(X); y.SetFromBig(Y); m.SetFromBig(Mo)
	switch op {
	case "ADD": y.Add(&x, &y)
	case "SUB": y.Sub(&x, &y)
	case "MUL": y.Mul(&x, &y)
	case "DIV": y.Div(&x, &y)
	case "MOD": y.Mod(&x, &y)
	case "SDIV": y.SDiv(&x, &y)
	case "SMOD": y.SMod(&x, &y)
	case "ADDMOD": m.AddMod(&x, &y, &m); return m.ToBig()
	case "MULMOD": m.MulMod(&x, &y, &m); return m.ToBig()
	case "EXP": y.Exp(&x, &y)
	case "SIGNEXTEND": y.ExtendSign(&y, &x)
	case "BYTE": y.Byte(&x)
	case "SHL": if x.LtUint64(256) { y.Lsh(&y, uint(x.Uint64())) } else { y.Clear() }
	case "SHR": if x.LtUint64(256) { y.Rsh(&y, uint(x.Uint64())) } else { y.Clear() }
	case "SAR": if x.GtUint64(256) || x.Eq(b.NewInt(256)) { if y.Sign() >= 0 { y.Clear() } else { y.SetAllOne() } } else { y.SRsh(&y, uint(x.Uint64())) }
	case "LT": if x.Lt(&y) { y.SetOne() } else { y.Clear() }
	case "GT": if x.Gt(&y) { y.SetOne() } else { y.Clear() }
	case "SLT": if x.Slt(&y) { y.SetOne() } else { y.Clear() }
	case "SGT": if x.Sgt(&y) { y.SetOne() } else { y.Clear() }
	case "EQ": if x.Eq(&y) { y.SetOne() } else { y.Clear() }
	case "MULDIV": var z b.Int; z.MulDivOverflow(&x, &y, &m); return z.ToBig()
	}
	return y.ToBig()
}

func main() {
	seed, _ := strconv.ParseInt(os.Args[1], 10, 64)
	nrand, _ := strconv.Atoi(os.Args[2])
	r := rand.New(rand.NewSource(seed))
	var edges []*big.Int
	one := big.NewInt(1)
	for k := 0; k < 256; k++ {
		p := new(big.Int).Lsh(one, uint(k))
		edges = append(edges, p, w(new(big.Int).Sub(p, one)), w(new(big.Int).Add(p, one)), w(new(big.Int).Neg(p)))
	}
	for _, c := range []int64{0, 2, 3, 7, 31, 32, 33, 255, 256, 257, 887272, -887272, 887271, -887273, 4295128739} {
		edges = append(edges, w(big.NewInt(c)))
	}
	mx, _ := new(big.Int).SetString("1461446703485210103287273052203988822378723970342", 10) // TickMath MAX_SQRT_PRICE
	edges = append(edges, mx, new(big.Int).Sub(mx, one), new(big.Int).Lsh(one, 96), new(big.Int).Lsh(one, 128))
	rnd := func() *big.Int {
		switch r.Intn(4) {
		case 0: return edges[r.Intn(len(edges))]
		case 1: return new(big.Int).Rand(r, M)
		case 2: return new(big.Int).Rand(r, new(big.Int).Lsh(one, uint(1+r.Intn(256))))
		default: // limb patterns
			v := new(big.Int)
			for i := 0; i < 4; i++ { v.Lsh(v, 64); v.Or(v, new(big.Int).SetUint64([]uint64{0, 1, ^uint64(0), 1 << 63, r.Uint64(), ^uint64(0) - 1}[r.Intn(6)])) }
			return v
		}
	}
	ops := []string{"ADD", "SUB", "MUL", "DIV", "MOD", "SDIV", "SMOD", "ADDMOD", "MULMOD", "EXP", "SIGNEXTEND", "BYTE", "SHL", "SHR", "SAR", "LT", "GT", "SLT", "SGT", "EQ", "MULDIV"}
	cnt := map[string]int{}; badA := map[string]int{}; badB := map[string]int{}; shown := 0
	check := func(op string, x, y, m *big.Int) {
		e := ref(op, x, y, m); cnt[op]++
		ra := runA(op, x, y, m); rb := runB(op, x, y, m)
		if ra.Cmp(e) != 0 { badA[op]++; if shown < 20 { fmt.Printf("v1.3.2 %s x=%x y=%x m=%x got %x want %x\n", op, x, y, m, ra, e); shown++ } }
		if rb.Cmp(e) != 0 { badB[op]++; if shown < 20 { fmt.Printf("master %s x=%x y=%x m=%x got %x want %x\n", op, x, y, m, rb, e); shown++ } }
	}
	small := func() *big.Int { return big.NewInt(int64(r.Intn(300))) }
	// edge x edge for two-operand ops
	for _, op := range ops {
		if op == "ADDMOD" || op == "MULMOD" || op == "MULDIV" || op == "EXP" { continue }
		for _, x := range edges { for _, y := range edges {
			xx := x
			if op == "SIGNEXTEND" || op == "BYTE" || op == "SHL" || op == "SHR" || op == "SAR" { if r.Intn(4) != 0 { xx = small() } }
			check(op, xx, y, big.NewInt(0))
		} }
	}
	for i := 0; i < nrand; i++ {
		for _, op := range ops {
			x, y, m := rnd(), rnd(), rnd()
			if op == "EXP" && r.Intn(2) == 0 { y = big.NewInt(int64(r.Intn(300))) }
			if op == "SIGNEXTEND" || op == "BYTE" || op == "SHL" || op == "SHR" || op == "SAR" { if r.Intn(2) == 0 { x = small() } }
			if (op == "MULMOD" || op == "MULDIV") && r.Intn(3) == 0 { m = new(big.Int).Sub(M, one) } // FullMath modulus
			check(op, x, y, m)
		}
	}
	tot := 0; for _, v := range cnt { tot += v }
	fmt.Printf("vectors %d per-op %v\nmismatch v1.3.2 %v\nmismatch master %v\n", tot, cnt, badA, badB)
}
