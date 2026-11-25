// Runs DIV, MOD, SDIV, SMOD, ADDMOD, MULMOD (and two composites copied from the PoolManager source)
// through ruint exactly as revm-interpreter 15.2.0 / 25.0.3 call it. Input: records of
// 1 op byte + three 32 byte big endian words. Output: one 32 byte word per record.
use ruint::Uint;
use std::io::{Read, Write};
type U256 = Uint<256, 4>;

#[derive(PartialEq, Clone, Copy)]
enum Sign { Minus, Zero, Plus }
const MIN_NEG: U256 = U256::from_limbs([0, 0, 0, 0x8000000000000000]);
fn sign(v: &U256) -> Sign { if v.bit(255) { Sign::Minus } else if v.is_zero() { Sign::Zero } else { Sign::Plus } }
fn sign_compl(v: &mut U256) -> Sign { let s = sign(v); if s == Sign::Minus { *v = v.wrapping_neg(); } s }
fn remove_sign(v: &mut U256) { unsafe { v.as_limbs_mut()[3] &= 0x7FFF_FFFF_FFFF_FFFF; } }
// i256_div and i256_mod transcribed from revm-interpreter src/instructions/i256.rs (15.2.0 lines 80-130, 25.0.3 lines 92-143)
fn i256_div(mut first: U256, mut second: U256) -> U256 {
    let ss = sign_compl(&mut second);
    if ss == Sign::Zero { return U256::ZERO; }
    let fs = sign_compl(&mut first);
    if first == MIN_NEG && second == U256::from(1) { return MIN_NEG.wrapping_neg(); }
    let mut d = first / second;
    remove_sign(&mut d);
    if (fs == Sign::Minus && ss != Sign::Minus) || (ss == Sign::Minus && fs != Sign::Minus) { d.wrapping_neg() } else { d }
}
fn i256_mod(mut first: U256, mut second: U256) -> U256 {
    let fs = sign_compl(&mut first);
    if fs == Sign::Zero { return U256::ZERO; }
    let ss = sign_compl(&mut second);
    if ss == Sign::Zero { return U256::ZERO; }
    let mut r = first % second;
    remove_sign(&mut r);
    if fs == Sign::Minus { r.wrapping_neg() } else { r }
}
// arithmetic.rs handlers: div/rem guard zero, addmod/mulmod call ruint directly
fn div(a: U256, b: U256) -> U256 { if !b.is_zero() { a.wrapping_div(b) } else { b } }
fn rem(a: U256, b: U256) -> U256 { if !b.is_zero() { a.wrapping_rem(b) } else { b } }

fn main() {
    let mut inp = Vec::new();
    std::io::stdin().read_to_end(&mut inp).unwrap();
    let mut out = Vec::with_capacity(inp.len() / 97 * 32);
    for r in inp.chunks_exact(97) {
        let op = r[0];
        let a = U256::from_be_slice(&r[1..33]);
        let b = U256::from_be_slice(&r[33..65]);
        let c = U256::from_be_slice(&r[65..97]);
        let res = match op {
            0 => div(a, b),
            1 => rem(a, b),
            2 => i256_div(a, b),
            3 => i256_mod(a, b),
            4 => a.add_mod(b, c),
            5 => a.mul_mod(b, c),
            // 6: FullMath 512 bit product and remainder, src/libraries/FullMath.sol:32-37 and :73-75
            6 => {
                let mm = a.mul_mod(b, U256::MAX);
                let p0 = a.wrapping_mul(b);
                let p1 = mm.wrapping_sub(p0).wrapping_sub(U256::from((mm < p0) as u8));
                let rr = if c.is_zero() { U256::ZERO } else { a.mul_mod(b, c) };
                (p1 ^ rr).wrapping_add(p0)
            }
            // 7: UnsafeMath.divRoundingUp, src/libraries/UnsafeMath.sol
            7 => { let q = div(a, b); let m = rem(a, b); q.wrapping_add(U256::from((m > U256::ZERO) as u8)) }
            // 8: tripwire only, never in the vector file: calls reciprocal_mg10 directly to show the debug build checks d >= 2^63
            8 => U256::from(ruint::algorithms::div::reciprocal_mg10(a.as_limbs()[0])),
            _ => panic!("op"),
        };
        out.extend_from_slice(&res.to_be_bytes::<32>());
    }
    std::io::stdout().write_all(&out).unwrap();
}
