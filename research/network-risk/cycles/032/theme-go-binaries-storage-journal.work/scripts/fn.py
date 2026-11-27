"""Print one function's body from a model's disassembly text (helper for choosing planted-fault sites)."""
import re
def body(text, name):
    m = re.search(r'^[0-9a-f]+ <[^>]*%s>:\n(.*?)(?=^[0-9a-f]+ <|\Z)' % re.escape(name), text, re.M | re.S)
    return m.group(1) if m else ''
