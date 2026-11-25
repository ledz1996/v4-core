// Harness: holiman/uint256 as the go-ethereum family interpreters call it, against math/big.
package main

import (
	"fmt"
	"math/big"
	"math/rand"
	"os"

	"github.com/holiman/uint256"
)

var two256 = new(big.Int).Lsh(big.NewInt(1), 256)
var mask = new(big.Int).Sub(two256, big.NewInt(1))

func B(x *uint256.Int) *big.Int { return x.ToBig() }
func U(b *big.Int) uint256.Int {
	v := new(big.Int).And(b, mask)
	var z uint256.Int
	z.SetFromBig(v)
	return z
}
func sgn(b *big.Int) *big.Int { // two's complement to signed
	if b.Bit(255) == 1 {
		return new(big.Int).Sub(b, two256)
	}
	return new(big.Int).Set(b)
}

// copy of bor v2.12.0-beta core/vm/mulmod_memo.go
type modReciprocal struct {
	mod uint256.Int
	mu  [5]uint64
	ok  bool
}

func (mm *modReciprocal) mulmod(x, y, z *uint256.Int) {
	if z[3] != 0 {
		if !mm.ok || mm.mod != *z {
			mm.mod = *z
			mm.mu = uint256.Reciprocal(z)
			mm.ok = true
		}
		z.MulModWithReciprocal(x, y, z, &mm.mu)
		return
	}
	z.MulMod(x, y, z)
}

var rng = rand.New(rand.NewSource(20261125))
var edges []*big.Int

func init() {
	add := func(b *big.Int) { edges = append(edges, new(big.Int).And(b, mask)) }
	for k := 0; k <= 256; k++ {
		p := new(big.Int).Lsh(big.NewInt(1), uint(k))
		add(p)
		add(new(big.Int).Sub(p, big.NewInt(1)))
		add(new(big.Int).Add(p, big.NewInt(1)))
		add(new(big.Int).Sub(two256, p))
	}
	add(big.NewInt(0))
	for _, s := range []string{"fffd8963efd1fc6a506488495d951d5263988d26", "1000276a3", "4295128739", "1461446703485210103287273052203988822378723970342", "887272", "79228162514264337593543950336"} {
		b, _ := new(big.Int).SetString(s, 0)
		if b == nil {
			b, _ = new(big.Int).SetString(s, 16)
		}
		if b != nil {
			add(b)
			add(new(big.Int).Neg(b))
		}
	}
}
func rnd() *big.Int {
	switch rng.Intn(6) {
	case 0:
		return edges[rng.Intn(len(edges))]
	case 1: // limbs of 0 / all ones / random
		var w [4]uint64
		for i := range w {
			switch rng.Intn(3) {
			case 0:
				w[i] = 0
			case 1:
				w[i] = ^uint64(0)
			default:
				w[i] = rng.Uint64()
			}
		}
		var z uint256.Int = uint256.Int(w)
		return z.ToBig()
	case 2:
		n := uint(rng.Intn(257))
		b := new(big.Int).Rand(rng, new(big.Int).Lsh(big.NewInt(1), n+1))
		return b.And(b, mask)
	default:
		b := new(big.Int).Rand(rng, two256)
		return b
	}
}

func main() {
	N := 2000000
	if len(os.Args) > 1 {
		fmt.Sscan(os.Args[1], &N)
	}
	bad := map[string]int{}
	cnt := map[string]int{}
	report := func(op string, a, b, c, got, want *big.Int) {
		bad[op]++
		if bad[op] <= 3 {
			fmt.Printf("MISMATCH %s a=%x b=%x c=%x got=%x want=%x\n", op, a, b, c, got, want)
		}
	}
	var memo modReciprocal
	full := new(big.Int).Set(mask)
	for i := 0; i < N; i++ {
		a, b, c := rnd(), rnd(), rnd()
		// shape of FullMath: modulus 2^256-1, and denominators near the high half of the product
		switch rng.Intn(4) {
		case 0:
			c = full
		case 1:
			p := new(big.Int).Mul(a, b)
			hi := new(big.Int).Rsh(p, 256)
			if hi.Sign() > 0 {
				// c with the same top limbs as hi, random low limbs, forced full width
				cc := new(big.Int).Set(hi)
				low := new(big.Int).Rand(rng, new(big.Int).Lsh(big.NewInt(1), 128))
				cc.Rsh(cc, 128).Lsh(cc, 128).Or(cc, low)
				cc.SetBit(cc, 255, 1)
				c = cc
			}
		}
		x, y, z := U(a), U(b), U(c)
		// MULMOD: stock and memo, interpreter aliasing (z is modulus and destination)
		{
			var want *big.Int
			if c.Sign() == 0 {
				want = big.NewInt(0)
			} else {
				want = new(big.Int).Mod(new(big.Int).Mul(a, b), c)
			}
			zz := z
			zz.MulMod(&x, &y, &zz)
			cnt["MULMOD"]++
			if B(&zz).Cmp(want) != 0 {
				report("MULMOD", a, b, c, B(&zz), want)
			}
			zm := z
			memo.mulmod(&x, &y, &zm)
			cnt["MULMOD_MEMO"]++
			if B(&zm).Cmp(want) != 0 {
				report("MULMOD_MEMO", a, b, c, B(&zm), want)
			}
			// ADDMOD
			za := z
			za.AddMod(&x, &y, &za)
			var wa *big.Int
			if c.Sign() == 0 {
				wa = big.NewInt(0)
			} else {
				wa = new(big.Int).Mod(new(big.Int).Add(a, b), c)
			}
			cnt["ADDMOD"]++
			if B(&za).Cmp(wa) != 0 {
				report("ADDMOD", a, b, c, B(&za), wa)
			}
		}
		// DIV, MOD: y.Div(&x, y)
		{
			yy := y
			yy.Div(&x, &yy)
			w := big.NewInt(0)
			if b.Sign() != 0 {
				w = new(big.Int).Div(a, b)
			}
			cnt["DIV"]++
			if B(&yy).Cmp(w) != 0 {
				report("DIV", a, b, nil, B(&yy), w)
			}
			ym := y
			ym.Mod(&x, &ym)
			w = big.NewInt(0)
			if b.Sign() != 0 {
				w = new(big.Int).Mod(a, b)
			}
			cnt["MOD"]++
			if B(&ym).Cmp(w) != 0 {
				report("MOD", a, b, nil, B(&ym), w)
			}
			// SDIV, SMOD (truncation toward zero, remainder sign of dividend)
			sa, sb := sgn(a), sgn(b)
			ys := y
			ys.SDiv(&x, &ys)
			w = big.NewInt(0)
			if sb.Sign() != 0 {
				w = new(big.Int).Quo(sa, sb)
			}
			wu := U(w)
			cnt["SDIV"]++
			if ys != wu {
				report("SDIV", a, b, nil, B(&ys), B(&wu))
			}
			yr := y
			yr.SMod(&x, &yr)
			w = big.NewInt(0)
			if sb.Sign() != 0 {
				w = new(big.Int).Rem(sa, sb)
			}
			wu = U(w)
			cnt["SMOD"]++
			if yr != wu {
				report("SMOD", a, b, nil, B(&yr), B(&wu))
			}
		}
		// EXP: exponent.Exp(&base, exponent)
		if i%4 == 0 {
			e := y
			if rng.Intn(2) == 0 {
				e.SetUint64(uint64(rng.Intn(300)))
			}
			eb := B(&e)
			ee := e
			ee.Exp(&x, &ee)
			w := new(big.Int).Exp(a, eb, two256)
			cnt["EXP"]++
			if B(&ee).Cmp(w) != 0 {
				report("EXP", a, eb, nil, B(&ee), w)
			}
		}
		// shifts, byte, signextend with small operands as the interpreter passes them
		{
			n := uint(rng.Intn(260))
			v := y
			if n < 256 {
				v.Lsh(&v, n)
			} else {
				v.Clear()
			}
			w := new(big.Int).And(new(big.Int).Lsh(b, n), mask)
			cnt["SHL"]++
			if B(&v).Cmp(w) != 0 {
				report("SHL", b, big.NewInt(int64(n)), nil, B(&v), w)
			}
			v = y
			if n < 256 {
				v.Rsh(&v, n)
			} else {
				v.Clear()
			}
			w = new(big.Int).Rsh(b, n)
			cnt["SHR"]++
			if B(&v).Cmp(w) != 0 {
				report("SHR", b, big.NewInt(int64(n)), nil, B(&v), w)
			}
			v = y
			if n < 256 {
				v.SRsh(&v, n)
			} else if v.Sign() >= 0 {
				v.Clear()
			} else {
				v.SetAllOne()
			}
			wu := U(new(big.Int).Rsh(sgn(b), n))
			cnt["SAR"]++
			if v != wu {
				report("SAR", b, big.NewInt(int64(n)), nil, B(&v), B(&wu))
			}
			th := uint256.NewInt(uint64(rng.Intn(40)))
			v = y
			v.Byte(th)
			wb := big.NewInt(0)
			if th.Uint64() < 32 {
				wb = new(big.Int).And(new(big.Int).Rsh(b, uint(8*(31-th.Uint64()))), big.NewInt(255))
			}
			cnt["BYTE"]++
			if B(&v).Cmp(wb) != 0 {
				report("BYTE", b, B(th), nil, B(&v), wb)
			}
			back := uint256.NewInt(uint64(rng.Intn(40)))
			v = y
			v.ExtendSign(&v, back)
			ws := new(big.Int).Set(b)
			if back.Uint64() < 31 {
				bits := uint(8*back.Uint64() + 8)
				low := new(big.Int).And(b, new(big.Int).Sub(new(big.Int).Lsh(big.NewInt(1), bits), big.NewInt(1)))
				if low.Bit(int(bits-1)) == 1 {
					low.Sub(low, new(big.Int).Lsh(big.NewInt(1), bits))
				}
				ws = new(big.Int).And(low, mask)
			}
			cnt["SIGNEXTEND"]++
			if B(&v).Cmp(ws) != 0 {
				report("SIGNEXTEND", b, B(back), nil, B(&v), ws)
			}
		}
		// comparisons
		{
			cnt["CMP"]++
			if x.Lt(&y) != (a.Cmp(b) < 0) || x.Gt(&y) != (a.Cmp(b) > 0) || x.Slt(&y) != (sgn(a).Cmp(sgn(b)) < 0) || x.Sgt(&y) != (sgn(a).Cmp(sgn(b)) > 0) || x.Eq(&y) != (a.Cmp(b) == 0) {
				report("CMP", a, b, nil, nil, nil)
			}
		}
	}
	fmt.Println("counts", cnt)
	fmt.Println("mismatches", bad)
}
