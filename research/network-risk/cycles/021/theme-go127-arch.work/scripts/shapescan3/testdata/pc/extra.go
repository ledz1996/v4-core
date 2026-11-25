package pc

import (
	"encoding/binary"
	"math/bits"
)

func noov(a, x, y int64) bool { return a-x*y < 0 }

func revw(b []byte, x uint32) uint32 { return bits.ReverseBytes32(binary.BigEndian.Uint32(b)) + x }
