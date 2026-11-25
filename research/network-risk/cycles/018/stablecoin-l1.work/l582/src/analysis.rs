//! Legacy bytecode padding and jump destination analysis.

use crate::op;

#[cfg(target_arch = "aarch64")]
mod aarch64;
#[cfg(any(target_arch = "x86", target_arch = "x86_64"))]
pub mod x86;

/// Analyzes the original, unpadded legacy bytecode to produce its jump table.
///
/// A `JUMPDEST` byte is a valid jump destination unless it is part of the data of a
/// `PUSH1..=PUSH32` instruction. This applies to every fork: the immediates of
/// `DUPN`/`SWAPN`/`EXCHANGE` are scanned as if they were opcodes.

/// Marks the jump destinations of `code` from the instruction at `pc` on.
///
/// `pc` must be zero or the first instruction after the analyzed prefix.
#[inline]
pub fn analyze_scalar(code: &[u8], table: &mut [u8], pc: usize) {
    let range = code.as_ptr_range();
    let start = range.start;
    // A PUSH from the prefix can run past the end, so `wrapping_add` keeps this defined.
    let mut iterator = start.wrapping_add(pc);
    let end = range.end;

    while iterator < end {
        let last_byte = unsafe { *iterator };
        if last_byte == op::JUMPDEST {
            // SAFETY: Jumps are max length of the code.
            let offset = unsafe { iterator.offset_from_unsigned(start) };
            // SAFETY: `table` has a bit for each byte of `code`.
            unsafe { *table.get_unchecked_mut(offset / 8) |= 1 << (offset % 8) };
            iterator = unsafe { iterator.add(1) };
        } else {
            let push_offset = last_byte.wrapping_sub(op::PUSH1);
            if push_offset < 32 {
                // A trailing PUSH can advance past the bytecode allocation.
                // `wrapping_add` keeps that offset computation defined.
                iterator = iterator.wrapping_add(push_offset as usize + 2);
            } else {
                // SAFETY: Iterator access range is checked in the while loop.
                iterator = unsafe { iterator.add(1) };
            }
        }
    }
}

/// Marks the jump destinations of full SIMD blocks and returns the offset of the next instruction.
#[inline]
pub fn analyze_simd(code: &[u8], table: &mut [u8]) -> usize {
    if code.len() < 16 {
        return 0;
    }
    core::cfg_select! {
        any(target_arch = "x86", target_arch = "x86_64") => x86::analyze(code, table),
        target_arch = "aarch64" => aarch64::analyze(code, table),
        _ => {
            let _ = table;
            0
        }
    }
}

/// A SIMD kernel that analyzes blocks of [`Self::LEN`] bytes.
#[cfg(any(target_arch = "x86", target_arch = "x86_64", target_arch = "aarch64"))]
trait Kernel {
    /// Jump destination bits of a block, one per byte.
    type Bits: Into<u128>;

    /// Offset of the first instruction in a block.
    type Entry: Entry;

    /// Block length in bytes.
    const LEN: usize = 8 * size_of::<Self::Bits>();

    /// Returns the JUMPDEST bits of the block at `ptr` that start an instruction, and moves
    /// `entry` to the next block.
    unsafe fn block(ptr: *const u8, entry: &mut Self::Entry) -> Self::Bits;
}

/// Analyzes full blocks with `K` from the block at `pc`, entered at `entry`, and returns the next
/// block and its entry.
///
/// # Safety
///
/// The CPU must support the kernel's target features, and `table` must have a bit for each byte
/// of `code`.
#[cfg(any(target_arch = "x86", target_arch = "x86_64", target_arch = "aarch64"))]
#[inline(always)]
unsafe fn analyze_blocks<K: Kernel>(
    code: &[u8],
    table: &mut [u8],
    (mut pc, entry): (usize, usize),
) -> (usize, usize) {
    let mut entry = unsafe { K::Entry::new(entry) };
    while pc + K::LEN <= code.len() {
        // SAFETY: the block and its bits are in bounds.
        unsafe {
            let bits = K::block(code.as_ptr().add(pc), &mut entry).into().to_le_bytes();
            let dst = table.as_mut_ptr().add(pc / 8);
            core::ptr::copy_nonoverlapping(bits.as_ptr(), dst, K::LEN / 8);
        }
        pc += K::LEN;
    }
    (pc, unsafe { entry.offset() })
}

/// A kernel's representation of the offset of the first instruction in a block.
#[cfg(any(target_arch = "x86", target_arch = "x86_64", target_arch = "aarch64"))]
trait Entry: Copy {
    /// Converts an offset, at most 32, to an entry.
    unsafe fn new(offset: usize) -> Self;

    /// Converts the entry to an offset.
    unsafe fn offset(self) -> usize;
}

/// Every opcode below this, including `0x80..` as signed bytes, is one byte long.
#[cfg(any(target_arch = "x86", target_arch = "x86_64", target_arch = "aarch64"))]
const PUSHX: i8 = op::PUSH1 as i8 - 1;

/// Subtracted from `max(opcode, PUSH1 - 1)` to get the length of an instruction.
#[cfg(any(target_arch = "x86", target_arch = "x86_64", target_arch = "aarch64"))]
const END_OFFSET: u8 = op::PUSH1 - 2;

/// Returns lanes counting up from `start`, restarting every `period` lanes.
#[cfg(any(target_arch = "x86", target_arch = "x86_64", target_arch = "aarch64"))]
const fn lanes<const N: usize>(period: usize, start: u8) -> [u8; N] {
    let mut lanes = [0; N];
    let mut i = 0;
    while i < N {
        lanes[i] = start.wrapping_add((i % period) as u8);
        i += 1;
    }
    lanes
}

/// Returns the JUMPDEST bits of a block without PUSH opcodes, clearing those the previous block's
/// PUSH covers, and moves `entry` to the next block.
#[cfg(any(target_arch = "x86", target_arch = "x86_64", target_arch = "aarch64"))]
#[inline(always)]
unsafe fn uncarried<E: Entry>(jumpdests: u64, entry: &mut E) -> u64 {
    let carried = unsafe { entry.offset() };
    *entry = unsafe { E::new(0) };
    // At most 32, so the shifts never overflow.
    jumpdests >> carried << carried
}

/// Maximum PUSH immediate length plus a terminating STOP.
const PADDING: usize = 33;

