{
  m: {}, w: {}, n: 0,
  T: 1n << 256n, MAX: (1n << 256n) - 1n, H: 1n << 255n,
  add: function (op, cl, a, pc, x, y, z) {
    var k = op + ':' + cl + ':' + a + ':' + pc;
    var v = this.m[k];
    if (v) { v[0]++; } else { this.m[k] = [1, x.toString(16), y.toString(16), z.toString(16)]; }
  },
  step: function (log, db) {
    var op = log.op.toNumber();
    var s = log.stack;
    if (op == 0x55) {
      this.w[toHex(log.contract.getAddress()) + ':' + s.peek(0).toString(16)] = s.peek(1).toString(16);
      return;
    }
    if (!(op == 4 || op == 5 || op == 6 || op == 7 || op == 8 || op == 9 || op == 0x0b || op == 0x12 || op == 0x13 || op == 0x1a || op == 0x1b || op == 0x1c || op == 0x1d)) return;
    var a = s.peek(0), b = s.peek(1), c = (op == 8 || op == 9) ? s.peek(2) : 0n;
    var ad = toHex(log.contract.getAddress());
    var pc = log.getPC();
    this.n++;
    var H = this.H, MAX = this.MAX, T = this.T;
    this.add(op, 0, ad, pc, a, b, c);
    var na = a >= H, nb = b >= H;
    if (op == 4 || op == 6) { if (b == 0n) this.add(op, 1, ad, pc, a, b, c); }
    else if (op == 5) {
      if (na) this.add(op, 1, ad, pc, a, b, c);
      if (nb) this.add(op, 2, ad, pc, a, b, c);
      if (b == 0n) this.add(op, 3, ad, pc, a, b, c);
      if (a == H && b == MAX) this.add(op, 4, ad, pc, a, b, c);
    } else if (op == 7) {
      if (na) this.add(op, 1, ad, pc, a, b, c);
      if (nb) this.add(op, 2, ad, pc, a, b, c);
      if (b == 0n) this.add(op, 3, ad, pc, a, b, c);
    } else if (op == 8) {
      if (a + b >= T) this.add(op, 1, ad, pc, a, b, c);
      if (c == MAX) this.add(op, 2, ad, pc, a, b, c);
      if (c == 0n) this.add(op, 3, ad, pc, a, b, c);
    } else if (op == 9) {
      var wide = a * b >= T;
      if (wide && c == MAX) this.add(op, 1, ad, pc, a, b, c);
      if (wide && c != MAX && c != 0n) this.add(op, 2, ad, pc, a, b, c);
      if (c == 0n) this.add(op, 3, ad, pc, a, b, c);
      if (wide && c != MAX && c >= (1n << 192n)) this.add(op, 4, ad, pc, a, b, c);
      if (wide && c != 0n && c < (1n << 128n)) this.add(op, 5, ad, pc, a, b, c);
    } else if (op == 0x0b) {
      if (a < 31n) {
        var bi = 8n * a + 7n;
        var bit = ((b >> bi) & 1n) == 1n;
        var hi = b >> (bi + 1n);
        var ones = MAX >> (bi + 1n);
        if (a <= 2n && bit) this.add(op, 1, ad, pc, a, b, c);
        if (a > 2n && bit) this.add(op, 2, ad, pc, a, b, c);
        if (a <= 2n && !bit && hi != 0n) this.add(op, 4, ad, pc, a, b, c);
        if (a <= 2n && bit && hi != ones) this.add(op, 5, ad, pc, a, b, c);
      } else this.add(op, 3, ad, pc, a, b, c);
    } else if (op == 0x1a) {
      if (a < 32n) this.add(op, 1, ad, pc, a, b, c); else this.add(op, 2, ad, pc, a, b, c);
    } else if (op == 0x1b || op == 0x1c) {
      if (a >= 256n) this.add(op, 1, ad, pc, a, b, c);
    } else if (op == 0x1d) {
      if (nb && a < 256n) this.add(op, 1, ad, pc, a, b, c);
      if (nb && a >= 256n) this.add(op, 2, ad, pc, a, b, c);
      if (!nb && a >= 256n) this.add(op, 3, ad, pc, a, b, c);
    } else if (op == 0x12 || op == 0x13) {
      if (na != nb) this.add(op, 1, ad, pc, a, b, c);
      if (na && nb) this.add(op, 2, ad, pc, a, b, c);
    }
  },
  fault: function (log, db) {},
  result: function (ctx, db) { return { n: this.n, m: this.m, w: this.w }; }
}
