// L-621: ruint 1.20.0 algorithms/mod.rs sub_x86_64 (lines 159-174) versus sub_fallback (176-191),
// copied verbatim apart from cfg attributes, and the lt/cmp built on them (mod.rs 101-144),
// compared with a schoolbook reference on 4-limb (256 bit) operands.
use core::arch::x86_64::_subborrow_u64;
use std::cmp::Ordering;
fn borrowing_sub(lhs: u64, rhs: u64, borrow: bool) -> (u64, bool) {
    let (result, borrow_1) = lhs.overflowing_sub(rhs);
    let (result, borrow_2) = result.overflowing_sub(borrow as u64);
    (result, borrow_1 | borrow_2)
}
fn sub_x86_64(a: &[u64], b: &[u64]) -> (u64, bool) {
    let mut borrow = 0; let mut acc = 0;
    for i in 0..a.len() { let mut x = 0; unsafe { borrow = _subborrow_u64(borrow, a[i], b[i], &mut x); } acc |= x; }
    (acc, borrow != 0)
}
fn sub_fallback(a: &[u64], b: &[u64]) -> (u64, bool) {
    let mut borrow = false; let mut acc = 0;
    for i in 0..a.len() { let x; (x, borrow) = borrowing_sub(a[i], b[i], borrow); acc |= x; }
    unsafe { core::ptr::write_volatile(&mut acc, acc) };
    (acc, borrow)
}
fn cmp_with(f: fn(&[u64],&[u64])->(u64,bool), a:&[u64], b:&[u64]) -> Ordering { let (r,o)=f(a,b); if r==0 {Ordering::Equal} else if o {Ordering::Less} else {Ordering::Greater} }
fn reference(a:&[u64;4], b:&[u64;4]) -> Ordering { for i in (0..4).rev() { if a[i]!=b[i] { return a[i].cmp(&b[i]); } } Ordering::Equal }
struct R(u64); impl R { fn n(&mut self)->u64 { self.0 ^= self.0<<13; self.0 ^= self.0>>7; self.0 ^= self.0<<17; self.0 } }
fn main() {
    let edges: Vec<u64> = vec![0,1,2,u64::MAX,u64::MAX-1,1<<63,(1<<63)-1,(1<<63)+1,0x5555555555555555,0xaaaaaaaaaaaaaaaa,1<<32,(1<<32)-1];
    let mut r = R(0x9e3779b97f4a7c15); let mut n:u64=0; let mut bad:u64=0;
    let mut check = |a:[u64;4], b:[u64;4]| {
        let x = sub_x86_64(&a,&b); let y = sub_fallback(&a,&b);
        let rf = reference(&a,&b);
        if x != y || cmp_with(sub_x86_64,&a,&b) != rf || cmp_with(sub_fallback,&a,&b) != rf { bad += 1; }
        n += 1;
    };
    // all 4-limb words built from edge limbs, against a random edge partner and against itself
    let e = edges.len();
    for i in 0..e.pow(4) { let mut a=[0u64;4]; let mut k=i; for l in 0..4 { a[l]=edges[k%e]; k/=e; }
        check(a,a);
        for _ in 0..40 { let mut b=[0u64;4]; for l in 0..4 { b[l]=edges[(r.n() as usize)%e]; } check(a,b); check(b,a); }
        let mut b=a; let l=(r.n()%4) as usize; b[l]=b[l].wrapping_add(1); check(a,b); check(b,a);
    }
    for _ in 0..20_000_000u64 { let a=[r.n(),r.n(),r.n(),r.n()]; let mut b=[r.n(),r.n(),r.n(),r.n()];
        let m=r.n()%5; for l in (m as usize)..4 { b[l]=a[l]; } check(a,b); }
    println!("cases {} mismatches {}", n, bad);
}
