// L-582: every x86 branch of evm2's jump destination scan at rev 35aa3280 (crates/evm2/src/bytecode/
// analysis.rs and analysis/x86.rs, copied unchanged except visibility and the std feature switch)
// run on this CPU, which has SSE4.1, AVX2 and AVX-512 VBMI, against a spec reference.
mod op { pub const JUMPDEST: u8 = 0x5b; pub const PUSH1: u8 = 0x60; }
mod analysis;
use analysis::{analyze_scalar, x86};

fn reference(code: &[u8]) -> Vec<bool> {
    let mut v = vec![false; code.len()]; let mut i = 0;
    while i < code.len() { let b = code[i]; if b == 0x5b { v[i] = true; i += 1 } else if (0x60..=0x7f).contains(&b) { i += (b - 0x5f) as usize + 1 } else { i += 1 } }
    v
}
fn bits(code: &[u8], t: &[u8]) -> Vec<bool> { (0..code.len()).map(|i| t[i / 8] >> (i % 8) & 1 == 1).collect() }
fn run(code: &[u8], k: u8) -> Vec<bool> {
    let mut t = vec![0u8; code.len() / 8 + 16];
    let pc = if code.len() < 16 { 0 } else { unsafe { match k { 0 => 0, 1 => x86::analyze_sse41(code, &mut t), 2 => x86::analyze_avx2(code, &mut t), 3 => x86::analyze_avx512vbmi(code, &mut t), _ => x86::analyze(code, &mut t) } } };
    analyze_scalar(code, &mut t, pc);
    bits(code, &t)
}
struct R(u64); impl R { fn n(&mut self) -> u64 { self.0 ^= self.0 << 13; self.0 ^= self.0 >> 7; self.0 ^= self.0 << 17; self.0 } }
fn main() {
    assert!(is_x86_feature_detected!("avx512vbmi") && is_x86_feature_detected!("avx2") && is_x86_feature_detected!("sse4.1"));
    let mut cases = 0u64; let mut bad = [0u64; 5]; let mut first: Vec<String> = vec![];
    let mut check = |code: &[u8], tag: &str| {
        let r = reference(code); cases += 1;
        for k in 0..5u8 { if run(code, k) != r { bad[k as usize] += 1; if first.len() < 10 { first.push(format!("{tag} kernel {k} len {}", code.len())); } } }
    };
    let pm = std::fs::read("pm_tempo.bin").unwrap();
    check(&pm, "poolmanager");
    for cut in 0..pm.len().min(4096) { check(&pm[cut..], "pm-suffix"); }
    // PUSHn whose data holds 0x5b at every lane, placed at every offset within a 64 and 128 byte window
    for n in 1..=32u8 { for off in 0..130usize { for tail in [0usize, 1, 15, 16, 17, 31, 32, 33, 63, 64, 65] {
        let mut c = vec![0x5bu8; off]; c.push(0x5f + n); c.extend(std::iter::repeat(0x5b).take(n as usize)); c.extend(std::iter::repeat(0x5b).take(tail));
        check(&c, "push-lanes");
        let mut d = vec![0x00u8; off]; d.push(0x5f + n); d.extend(std::iter::repeat(0x5b).take(n as usize)); d.extend(std::iter::repeat(0x5b).take(tail));
        check(&d, "push-lanes0");
        let mut e = c.clone(); e.truncate(off + 1 + (n as usize) / 2); check(&e, "truncated");
    } } }
    // chained pushes that carry across block borders
    let mut r = R(0x5b5b_1234_abcd_ef01);
    for _ in 0..300_000 {
        let len = 16 + (r.n() % 600) as usize; let mut c = Vec::with_capacity(len);
        let mode = r.n() % 4;
        while c.len() < len { let x = r.n(); let b = match mode { 0 => x as u8, 1 => if x % 3 == 0 { 0x5b } else { 0x60 + (x >> 8) as u8 % 32 }, 2 => if x % 2 == 0 { 0x7f } else { 0x5b }, _ => [0x5b, 0x60, 0x7f, 0x5f, 0x80, 0x00, 0xfe][(x % 7) as usize] }; c.push(b); }
        check(&c, "random");
    }
    for len in 0..300usize { for fill in [0x5bu8, 0x60, 0x7f, 0x00] { let c = vec![fill; len]; check(&c, "uniform"); } }
    println!("cases {cases} mismatches scalar {} sse41 {} avx2 {} avx512vbmi {} dispatch {}", bad[0], bad[1], bad[2], bad[3], bad[4]);
    for f in first { println!("{f}"); }
}
