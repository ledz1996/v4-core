// L-879: ruint 1.21.1 with its x86_64 paths (as built for Tempo's x86_64 release) versus the same
// crate with every target_arch = "x86_64" cfg in algorithms/mod.rs, div/reciprocal.rs and div/small.rs
// forced to the non-x86 branch, both against num-bigint, for the U256 operations evm2 calls.
use num_bigint::BigUint;
use num_traits::{Zero, One, ToPrimitive};
type A = ruint::Uint<256, 4>;
type B = ruint_fb::Uint<256, 4>;
type O = ruint_old::Uint<256, 4>;
fn big(l: &[u64; 4]) -> BigUint { let mut v = BigUint::zero(); for i in (0..4).rev() { v = (v << 64u32) + BigUint::from(l[i]); } v }
fn limbs(v: &BigUint) -> [u64; 4] { let m = (BigUint::one() << 256u32) - 1u32; let v = v & &m; let d = v.to_u64_digits(); let mut o=[0u64;4]; for (i,x) in d.iter().enumerate(){o[i]=*x;} o }
struct R(u64); impl R { fn n(&mut self)->u64 { self.0 ^= self.0<<13; self.0 ^= self.0>>7; self.0 ^= self.0<<17; self.0 } }
const E: [u64; 14] = [0,1,2,3,u64::MAX,u64::MAX-1,1<<63,(1<<63)-1,(1<<63)+1,0x5555555555555555,0xaaaaaaaaaaaaaaaa,1<<32,(1<<32)-1,0xffffffff00000001];
fn word(r: &mut R) -> [u64;4] {
    let mut w=[0u64;4];
    let len = (r.n()%5) as usize; // number of nonzero low limbs
    for i in 0..len { w[i] = match r.n()%4 { 0 => E[(r.n()%14) as usize], 1 => r.n() >> (r.n()%64), _ => r.n() }; }
    if r.n()%7==0 { for i in 0..4 { w[i]=!w[i]; } }
    w
}
fn main() {
    let n: u64 = std::env::args().nth(1).map(|s| s.parse().unwrap()).unwrap_or(2_000_000);
    let two256 = BigUint::one() << 256u32;
    let mut r = R(0x2545F4914F6CDD1D);
    let (mut cases, mut bad_x, mut bad_f, mut shaped, mut old_bad) = (0u64,0u64,0u64,0u64,0u64);
    let mut report = |name:&str, a:&[u64;4], b:&[u64;4], c:&[u64;4], x:[u64;4], f:[u64;4], want:[u64;4], bx:&mut u64, bf:&mut u64| {
        if x!=want { *bx+=1; if *bx<10 { println!("X86 MISMATCH {} {:x?} {:x?} {:x?} got {:x?} want {:x?}",name,a,b,c,x,want); } }
        if f!=want { *bf+=1; if *bf<10 { println!("FB MISMATCH {} {:x?} {:x?} {:x?} got {:x?} want {:x?}",name,a,b,c,f,want); } }
    };
    for it in 0..n {
        let a = word(&mut r); let b = word(&mut r); let mut c = word(&mut r);
        // every fourth case: the shape of the ruint 1.21.0 mul_mod fault, a 4-limb modulus whose top
        // two limbs equal those of the high half of a*b (quotient digit near the boundary)
        if it % 4 == 0 {
            let mut a = a; let mut b = b; a[3] |= 1 + (r.n() >> 1); b[3] |= 1 + (r.n() >> 1);
            let p = big(&a)*big(&b); let hi = limbs(&(p >> 256u32));
            if hi[3]!=0 { c[3]=hi[3]; c[2]=hi[2]; if r.n()%2==0 { c[1]=hi[1]; } shaped+=1; }
            let w = limbs(&((big(&a)*big(&b))%big(&c)));
            let o = *O::from_limbs(a).mul_mod(O::from_limbs(b),O::from_limbs(c)).as_limbs();
            if o != w { old_bad += 1; }
            let x = *A::from_limbs(a).mul_mod(A::from_limbs(b),A::from_limbs(c)).as_limbs();
            let f = *B::from_limbs(a).mul_mod(B::from_limbs(b),B::from_limbs(c)).as_limbs();
            if x != w { bad_x += 1; } if f != w { bad_f += 1; }
        }
        if it % 16 == 1 { c = [u64::MAX;4]; } // mulDiv's not(0) modulus
        let (ba,bb,bc) = (big(&a),big(&b),big(&c));
        let (xa,xb,xc) = (A::from_limbs(a),A::from_limbs(b),A::from_limbs(c));
        let (fa,fb,fc) = (B::from_limbs(a),B::from_limbs(b),B::from_limbs(c));
        // MULMOD, ADDMOD
        let w = if bc.is_zero() {[0;4]} else {limbs(&((&ba*&bb)%&bc))};
        report("mulmod",&a,&b,&c,*xa.mul_mod(xb,xc).as_limbs(),*fa.mul_mod(fb,fc).as_limbs(),w,&mut bad_x,&mut bad_f);
        let w = if bc.is_zero() {[0;4]} else {limbs(&((&ba+&bb)%&bc))};
        report("addmod",&a,&b,&c,*xa.add_mod(xb,xc).as_limbs(),*fa.add_mod(fb,fc).as_limbs(),w,&mut bad_x,&mut bad_f);
        // DIV and MOD (evm2 checks zero first)
        if !bb.is_zero() {
            report("div",&a,&b,&c,*xa.wrapping_div(xb).as_limbs(),*fa.wrapping_div(fb).as_limbs(),limbs(&(&ba/&bb)),&mut bad_x,&mut bad_f);
            report("rem",&a,&b,&c,*xa.wrapping_rem(xb).as_limbs(),*fa.wrapping_rem(fb).as_limbs(),limbs(&(&ba%&bb)),&mut bad_x,&mut bad_f);
        }
        // comparisons
        let lt = |x:bool| if x {[1,0,0,0]} else {[0;4]};
        report("lt",&a,&b,&c,lt(xa<xb),lt(fa<fb),lt(ba<bb),&mut bad_x,&mut bad_f);
        report("gt",&a,&b,&c,lt(xa>xb),lt(fa>fb),lt(ba>bb),&mut bad_x,&mut bad_f);
        report("eq",&a,&b,&c,lt(xa==xb),lt(fa==fb),lt(ba==bb),&mut bad_x,&mut bad_f);
        report("lt_self",&a,&a,&c,lt(xa<xa),lt(fa<fa),[0;4],&mut bad_x,&mut bad_f);
        report("iszero",&a,&b,&c,lt(xa.is_zero()),lt(fa.is_zero()),lt(ba.is_zero()),&mut bad_x,&mut bad_f);
        // shifts by the low byte of c (evm2 clamps whole-word shift amounts itself)
        let s = (c[0] % 300) as usize;
        let ws = if s>=256 {[0;4]} else {limbs(&(&ba << s))};
        let xs = if s>=256 {[0;4]} else {*(xa << s).as_limbs()}; let fs = if s>=256 {[0;4]} else {*(fa << s).as_limbs()};
        report("shl",&a,&b,&c,xs,fs,ws,&mut bad_x,&mut bad_f);
        let ws = if s>=256 {[0;4]} else {limbs(&(&ba >> s))};
        let xs = if s>=256 {[0;4]} else {*(xa >> s).as_limbs()}; let fs = if s>=256 {[0;4]} else {*(fa >> s).as_limbs()};
        report("shr",&a,&b,&c,xs,fs,ws,&mut bad_x,&mut bad_f);
        // MUL, ADD, SUB, EXP (small exponent to keep the reference cheap)
        report("mul",&a,&b,&c,*xa.wrapping_mul(xb).as_limbs(),*fa.wrapping_mul(fb).as_limbs(),limbs(&(&ba*&bb)),&mut bad_x,&mut bad_f);
        report("add",&a,&b,&c,*xa.wrapping_add(xb).as_limbs(),*fa.wrapping_add(fb).as_limbs(),limbs(&(&ba+&bb)),&mut bad_x,&mut bad_f);
        report("sub",&a,&b,&c,*xa.wrapping_sub(xb).as_limbs(),*fa.wrapping_sub(fb).as_limbs(),limbs(&((&ba+&two256)-&bb)),&mut bad_x,&mut bad_f);
        if it % 8 == 0 { let e = c[0]; let e2=[e,0,0,0];
            report("exp",&a,&e2,&c,*xa.wrapping_pow(A::from(e)).as_limbs(),*fa.wrapping_pow(B::from(e)).as_limbs(),limbs(&ba.modpow(&BigUint::from(e),&two256)),&mut bad_x,&mut bad_f); }
        cases += 1;
    }
    let _ = bc_unused();
    println!("iterations {} fault-shaped moduli {} x86 mismatches {} fallback mismatches {} ruint-1.21.0 mul_mod mismatches on shaped {}", cases, shaped, bad_x, bad_f, old_bad);
}
fn bc_unused() -> u64 { 0u64.to_u64().unwrap() }
