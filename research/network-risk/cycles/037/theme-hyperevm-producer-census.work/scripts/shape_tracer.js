{
  m: {}, n: 0, orig: {}, cur: {},
  T: 1n << 256n, MAX: (1n << 256n) - 1n, H: 1n << 255n, L64: 1n << 64n, L192: 1n << 192n,
  add: function (op, cl, a, pc, x, y, z) {
    var k = op + ':' + cl + ':' + a + ':' + pc;
    var v = this.m[k];
    if (v) { v[0]++; } else { this.m[k] = [1, x.toString(16), y.toString(16), z.toString(16)]; }
  },
  limbs: function (x) { if (x == 0n) return 0; var l = 1; while (x >= this.L64) { x = x >> 64n; l++; } return l; },
  step: function (log, db) {
    var op = log.op.toNumber();
    var want = (op >= 2 && op <= 0x0b) || op == 0x12 || op == 0x13 || (op >= 0x1a && op <= 0x1d) || op == 0x20 ||
      op == 0x55 || op == 0x57 || op == 0x5c || op == 0x5d || op == 0x5e;
    if (!want) return;
    var s = log.stack;
    var a = s.peek(0), b = s.peek(1);
    var c = (op == 8 || op == 9 || op == 0x5e) ? s.peek(2) : 0n;
    var ad = toHex(log.contract.getAddress());
    var pc = log.getPC();
    this.n++;
    var H = this.H, MAX = this.MAX, T = this.T;
    var na = a >= H, nb = b >= H;
    if (op == 2) { if (a * b >= T) this.add(op, 1, ad, pc, a, b, c); return; }
    if (op == 3 || op == 1) return;
    if (op != 0x55) this.add(op, 0, ad, pc, a, b, c);
    if (op == 4) {
      if (b == 0n) this.add(op, 1, ad, pc, a, b, c);
      else if (a >= this.L192) this.add(op, 10 + this.limbs(b), ad, pc, a, b, c);
    } else if (op == 6) {
      if (b == 0n) this.add(op, 1, ad, pc, a, b, c);
    } else if (op == 5) {
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
      if (wide && c != MAX && c >= this.L192) this.add(op, 4, ad, pc, a, b, c);
      if (wide && c != 0n && c < (1n << 128n)) this.add(op, 5, ad, pc, a, b, c);
      if (wide && c != MAX && c != 0n) this.add(op, 10 + this.limbs(c), ad, pc, a, b, c);
    } else if (op == 0x0a) {
      if (b >= 256n) this.add(op, 1, ad, pc, a, b, c);
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
        this.add(op, 100 + Number(a) * 2 + (bit ? 1 : 0), ad, pc, a, b, c);
      } else this.add(op, 3, ad, pc, a, b, c);
    } else if (op == 0x1a) {
      if (a < 32n) this.add(op, 1, ad, pc, a, b, c); else this.add(op, 2, ad, pc, a, b, c);
      if (a == 0n) this.add(op, 3, ad, pc, a, b, c);
      if (a == 31n) this.add(op, 4, ad, pc, a, b, c);
    } else if (op == 0x1b || op == 0x1c) {
      if (a >= 256n) this.add(op, 1, ad, pc, a, b, c);
      else if (a == 0n) this.add(op, 2, ad, pc, a, b, c);
      else this.add(op, 3, ad, pc, a, b, c);
    } else if (op == 0x1d) {
      if (nb && a < 256n) this.add(op, 1, ad, pc, a, b, c);
      if (nb && a >= 256n) this.add(op, 2, ad, pc, a, b, c);
      if (!nb && a >= 256n) this.add(op, 3, ad, pc, a, b, c);
    } else if (op == 0x12 || op == 0x13) {
      if (na != nb) this.add(op, 1, ad, pc, a, b, c);
      if (na && nb) this.add(op, 2, ad, pc, a, b, c);
    } else if (op == 0x20) {
      var L = b;
      var cl = (L == 64n) ? 1 : (L == 58n) ? 2 : (L == 160n) ? 3 : (L == 136n) ? 4 : (L == 135n || L == 137n) ? 5 : (L == 0n) ? 6 : (L == 32n) ? 7 : 9;
      this.add(op, cl, ad, pc, a, b, c);
      if (L > 136n) this.add(op, 8, ad, pc, a, b, c);
    } else if (op == 0x5e) {
      var d = a > b ? a - b : b - a;
      if (c != 0n && d < c) this.add(op, a > b ? 1 : 2, ad, pc, a, b, c);
    } else if (op == 0x57) {
      if (b == 0n) this.add(op, 1, ad, pc, a, b, c);
      else if (b >= this.L64) this.add(op, 2, ad, pc, a, b, c);
      else this.add(op, 3, ad, pc, a, b, c);
    } else if (op == 0x55) {
      var key = ad + ':' + a.toString(16);
      var o = this.orig[key];
      var dbv;
      try { dbv = db.getState(log.contract.getAddress(), toWord(a.toString(16).length % 2 ? '0x0' + a.toString(16) : '0x' + a.toString(16))); dbv = BigInt(toHex(dbv)); } catch (e) { dbv = null; }
      if (o === undefined) { o = dbv; this.orig[key] = dbv; }
      var cur = (this.cur[key] !== undefined) ? this.cur[key] : o;
      this.cur[key] = b;
      this.add(op, 0, ad, pc, a, b, cur === null ? -1n : cur);
      if (o !== null && cur !== null) {
        if (b == o && cur != o) this.add(op, 1, ad, pc, a, b, c);
        if (b == cur) this.add(op, 2, ad, pc, a, b, c);
        if (dbv != cur) this.add(op, 3, ad, pc, a, b, dbv);
      } else this.add(op, 9, ad, pc, a, b, c);
    }
  },
  fault: function (log, db) {},
  result: function (ctx, db) { return { n: this.n, m: this.m }; }
}
