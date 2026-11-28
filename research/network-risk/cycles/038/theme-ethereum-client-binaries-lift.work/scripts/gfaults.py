"""Cycle 38 planted faults in the inlined code of geth v1.17.10 (*EVM).execUntraced, applied to the in-memory
disassembly text before the model parses it (the binary is not modified). A patch that does not match exactly stops.
  carry  a0323f: the second limb of the inline ADD adds without the carry (adc -> add)
  limb   a03720: the inline comparison loads limb 2 of the first operand instead of limb 3
  borrow a0373d: the inline comparison drops the borrow of limb 2 (sbb -> sub)"""
import faults as F

SPEC = {
    'carry': ([(0xa0323f, 'adc    r15,r11', 'add    r15,r11')], ['ADD']),
    'limb': ([(0xa03720, '[r8+r12*1+0x18]', '[r8+r12*1+0x10]')], ['LT', 'GT', 'SLT', 'SGT']),
    'borrow': ([(0xa0373d, 'sbb    rdi,rcx', 'sub    rdi,rcx')], ['LT', 'GT', 'SLT', 'SGT']),
}


def get(name):
    if name == 'none':
        return {}
    patch, ops = SPEC[name]
    return {'ops': ops, 'text_patch': F.text_patcher(patch), 'stop_after': 20,
            'where': [{'addr': hex(a), 'old': o, 'new': n} for a, o, n in patch]}
