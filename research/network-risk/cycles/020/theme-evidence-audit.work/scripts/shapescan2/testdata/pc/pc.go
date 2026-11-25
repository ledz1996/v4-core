package pc

func shl64(x uint64) uint64 { return (x + x) << 63 }
func shl32(x uint32) uint32 { return (x + x) << 31 }
func narrow(x uint32) uint32 { return x >> 3 }
func mk(n int) []int { s := make([]int, n); return s }
