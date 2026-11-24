use rfb::Uint as F;
use rx::Uint as X;
type UF = F<256, 4>;
type UX = X<256, 4>;
struct Rng(u64);
impl Rng { fn next(&mut self) -> u64 { self.0 ^= self.0 << 13; self.0 ^= self.0 >> 7; self.0 ^= self.0 << 17; self.0 } }
fn edge(r: &mut Rng) -> [u64; 4] {
    let mut l = [0u64; 4];
    let k = r.next() % 12;
    for i in 0..4 {
        let m = r.next() % 8;
        l[i] = match m { 0 => 0, 1 => u64::MAX, 2 => 1u64 << (r.next() % 64), 3 => (1u64 << 63), 4 => u64::MAX - (r.next() % 4), 5 => r.next() >> (r.next() % 64), _ => r.next() };
    }
    // trim to a random number of limbs so short operands occur
    let n = (k % 5) as usize;
    for i in n..4 { if k > 4 { break; } l[i] = 0; }
    l
}
fn main() {
    let n: u64 = std::env::args().nth(1).unwrap().parse().unwrap();
    let mut r = Rng(0x9e3779b97f4a7c15);
    let mut bad = 0u64;
    let mut counts = [0u64; 8];
    for _ in 0..n {
        let (a, b, c) = (edge(&mut r), edge(&mut r), edge(&mut r));
        let (fa, fb, fc) = (UF::from_limbs(a), UF::from_limbs(b), UF::from_limbs(c));
        let (xa, xb, xc) = (UX::from_limbs(a), UX::from_limbs(b), UX::from_limbs(c));
        let res: [([u64;4],[u64;4]); 8] = [
            (if fb.is_zero() { [0;4] } else { *fa.wrapping_div(fb).as_limbs() }, if xb.is_zero() { [0;4] } else { *xa.wrapping_div(xb).as_limbs() }),
            (if fb.is_zero() { [0;4] } else { *fa.wrapping_rem(fb).as_limbs() }, if xb.is_zero() { [0;4] } else { *xa.wrapping_rem(xb).as_limbs() }),
            (*fa.mul_mod(fb, fc).as_limbs(), *xa.mul_mod(xb, xc).as_limbs()),
            (*fa.mul_mod(fb, UF::MAX).as_limbs(), *xa.mul_mod(xb, UX::MAX).as_limbs()),
            (*fa.add_mod(fb, fc).as_limbs(), *xa.add_mod(xb, xc).as_limbs()),
            (*fa.wrapping_mul(fb).as_limbs(), *xa.wrapping_mul(xb).as_limbs()),
            (*(fa << (b[0] as usize % 300)).as_limbs(), *(xa << (b[0] as usize % 300)).as_limbs()),
            (*fa.arithmetic_shr(b[0] as usize % 300).as_limbs(), *xa.arithmetic_shr(b[0] as usize % 300).as_limbs()),
        ];
        for (i, (p, q)) in res.iter().enumerate() {
            counts[i] += 1;
            if p != q { bad += 1; if bad < 20 { println!("MISMATCH op{} a={:x?} b={:x?} c={:x?} fb={:x?} x86={:x?}", i, a, b, c, p, q); } }
        }
        // independent check of the fallback division: q*b + r == a and r < b
        if !fb.is_zero() {
            let q = fa.wrapping_div(fb); let rr = fa.wrapping_rem(fb);
            if !(rr < fb && q.wrapping_mul(fb).wrapping_add(rr) == fa) { bad += 1; if bad < 20 { println!("DIVCHECK a={:x?} b={:x?}", a, b); } }
        }
    }
    println!("cases {} per-op {:?} mismatches {}", n, counts, bad);
}
