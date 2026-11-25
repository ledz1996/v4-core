// run

// Copyright 2026 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package pc

import (
	"fmt"
	"math/bits"
)

//go:noinline
func f82777(x, y int64) int64 {
	r := x >> 33
	if bits.OnesCount8(128) > 0 {
		r = ^y
	}
	return r
}

func main_82777() {
	if got := f82777(0, 2); got != -3 {
		fmt.Printf("selected ^2 = %d, want -3\n", got)
		panic("FAIL")
	}
}
