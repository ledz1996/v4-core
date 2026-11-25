// Positive controls for shapescan: the reproducers of Go issues 81863 and 82839 and inlined variants.
package ctl

var sink int

func f81863(c bool) int {
	var x, y int
	p := &x
	if c {
		p = &y
	}
	*p = 1
	return x
}

func pick(c bool, a, b *[4]uint64) *[4]uint64 {
	if c {
		return a
	}
	return b
}

func g81863(c bool) uint64 {
	var x, y [4]uint64
	q := pick(c, &x, &y)
	q[0] = 1
	return x[0]
}

func f82839(x uint8) {
	if int32(int16(x)-513) < -536870911 {
		sink = 1
	}
}

func h82839(x int32) bool { return int64(x+5) > 1<<40 }

func k81863(c bool, out *[4]uint64) uint64 {
	var tmp [4]uint64
	p := out
	if c {
		p = &tmp
	}
	p[1] = 7
	return 0
}

func n81863(c bool) int {
	p := new(int)
	if c {
		p = new(int)
	}
	*p = 1
	return 0
}
