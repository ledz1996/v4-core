// Software model of the AArch64 NEON intrinsics used by evm2 analysis/aarch64.rs, written from the
// Arm intrinsic definitions (lane-wise, wrapping arithmetic, TBX keeps the destination lane when the
// index is >= 16, BSL selects bits of the first operand where the mask is set).
#![allow(non_camel_case_types)]
#[derive(Clone, Copy, PartialEq, Eq, Debug)] #[repr(transparent)] pub struct uint8x16_t(pub [u8; 16]);
#[derive(Clone, Copy)] #[repr(transparent)] pub struct int8x16_t(pub [i8; 16]);
#[derive(Clone, Copy)] #[repr(transparent)] pub struct uint64x2_t(pub [u64; 2]);
fn map2(a: uint8x16_t, b: uint8x16_t, f: impl Fn(u8, u8) -> u8) -> uint8x16_t { let mut r = [0u8; 16]; for i in 0..16 { r[i] = f(a.0[i], b.0[i]); } uint8x16_t(r) }
pub fn vdupq_n_u8(x: u8) -> uint8x16_t { uint8x16_t([x; 16]) }
pub fn vdupq_n_s8(x: i8) -> int8x16_t { int8x16_t([x; 16]) }
pub fn vgetq_lane_u8<const N: i32>(a: uint8x16_t) -> u8 { a.0[N as usize] }
pub fn vgetq_lane_u64<const N: i32>(a: uint64x2_t) -> u64 { a.0[N as usize] }
pub fn vqtbx1q_u8(a: uint8x16_t, t: uint8x16_t, idx: uint8x16_t) -> uint8x16_t { let mut r = a.0; for i in 0..16 { let j = idx.0[i] as usize; if j < 16 { r[i] = t.0[j]; } } uint8x16_t(r) }
pub fn vreinterpretq_s8_u8(a: uint8x16_t) -> int8x16_t { int8x16_t(a.0.map(|x| x as i8)) }
pub fn vreinterpretq_u8_s8(a: int8x16_t) -> uint8x16_t { uint8x16_t(a.0.map(|x| x as u8)) }
pub fn vreinterpretq_u64_u8(a: uint8x16_t) -> uint64x2_t { let mut lo = [0u8; 8]; let mut hi = [0u8; 8]; lo.copy_from_slice(&a.0[..8]); hi.copy_from_slice(&a.0[8..]); uint64x2_t([u64::from_le_bytes(lo), u64::from_le_bytes(hi)]) }
pub fn vmaxq_s8(a: int8x16_t, b: int8x16_t) -> int8x16_t { let mut r = [0i8; 16]; for i in 0..16 { r[i] = a.0[i].max(b.0[i]); } int8x16_t(r) }
pub fn vaddq_u8(a: uint8x16_t, b: uint8x16_t) -> uint8x16_t { map2(a, b, |x, y| x.wrapping_add(y)) }
pub fn vsubq_u8(a: uint8x16_t, b: uint8x16_t) -> uint8x16_t { map2(a, b, |x, y| x.wrapping_sub(y)) }
pub fn vandq_u8(a: uint8x16_t, b: uint8x16_t) -> uint8x16_t { map2(a, b, |x, y| x & y) }
pub fn vorrq_u8(a: uint8x16_t, b: uint8x16_t) -> uint8x16_t { map2(a, b, |x, y| x | y) }
pub fn vceqq_u8(a: uint8x16_t, b: uint8x16_t) -> uint8x16_t { map2(a, b, |x, y| if x == y { 0xff } else { 0 }) }
pub fn vcleq_u8(a: uint8x16_t, b: uint8x16_t) -> uint8x16_t { map2(a, b, |x, y| if x <= y { 0xff } else { 0 }) }
pub fn vbslq_u8(m: uint8x16_t, a: uint8x16_t, b: uint8x16_t) -> uint8x16_t { let mut r = [0u8; 16]; for i in 0..16 { r[i] = (m.0[i] & a.0[i]) | (!m.0[i] & b.0[i]); } uint8x16_t(r) }
pub fn vpaddq_u8(a: uint8x16_t, b: uint8x16_t) -> uint8x16_t { let mut r = [0u8; 16]; for i in 0..8 { r[i] = a.0[2 * i].wrapping_add(a.0[2 * i + 1]); r[8 + i] = b.0[2 * i].wrapping_add(b.0[2 * i + 1]); } uint8x16_t(r) }
pub fn vmaxvq_u8(a: uint8x16_t) -> u8 { *a.0.iter().max().unwrap() }
pub fn vmaxvq_s8(a: int8x16_t) -> i8 { *a.0.iter().max().unwrap() }
pub unsafe fn vld1q_u8(p: *const u8) -> uint8x16_t { let mut r = [0u8; 16]; unsafe { core::ptr::copy_nonoverlapping(p, r.as_mut_ptr(), 16) }; uint8x16_t(r) }
