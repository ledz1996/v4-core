// Standalone copy of the Load/Store logic of keccakResultCache from bor v2.12.0-beta core/vm/shared_cache.go
// (metrics removed, sha256 standing in for keccak; the cache logic does not depend on the hash function).
// Many goroutines look up and store inputs of 58 and 160 bytes drawn from a small pool, in buffers they
// overwrite right after every call, as EVM memory would be. Every hit must equal the hash of the bytes looked up.
package main

import (
	"crypto/sha256"
	"fmt"
	"math/rand/v2"
	"sync"
	"sync/atomic"
	"unsafe"
)

type Hash [32]byte

type cache struct {
	m                   sync.Map
	maxEntries, maxBytes int64
	entries, bytes      atomic.Int64
	full                atomic.Bool
}

func (s *cache) Load(data []byte) (Hash, bool) {
	v, ok := s.m.Load(unsafe.String(unsafe.SliceData(data), len(data)))
	if !ok {
		return Hash{}, false
	}
	return v.(Hash), true
}
func reserve(c *atomic.Int64, n, max int64) bool {
	for {
		cur := c.Load()
		if cur+n > max {
			return false
		}
		if c.CompareAndSwap(cur, cur+n) {
			return true
		}
	}
}
func (s *cache) Store(data []byte, h Hash) {
	if s.full.Load() {
		return
	}
	n := int64(len(data))
	if !reserve(&s.entries, 1, s.maxEntries) {
		s.mark()
		return
	}
	if !reserve(&s.bytes, n, s.maxBytes) {
		s.entries.Add(-1)
		s.mark()
		return
	}
	if _, loaded := s.m.LoadOrStore(string(data), h); loaded {
		s.entries.Add(-1)
		s.bytes.Add(-n)
	}
}
func (s *cache) mark() {
	if s.entries.Load() >= s.maxEntries || s.bytes.Load() >= s.maxBytes {
		s.full.CompareAndSwap(false, true)
	}
}

func main() {
	var bad, hits, miss atomic.Int64
	for round := 0; round < 8; round++ {
		c := &cache{maxEntries: 1 << 16, maxBytes: 32 << 20}
		if round%4 == 3 {
			c.maxEntries = 300 // exercise the full path
		}
		var wg sync.WaitGroup
		for g := 0; g < 16; g++ {
			wg.Add(1)
			go func(g int) {
				defer wg.Done()
				r := rand.New(rand.NewPCG(uint64(round), uint64(g)))
				mem := make([]byte, 4096)
				for i := 0; i < 100000; i++ {
					n := 58
					if r.IntN(2) == 0 {
						n = 160
					}
					if r.IntN(50) == 0 {
						n = 1 + r.IntN(300)
					}
					off := r.IntN(1024)
					data := mem[off : off+n]
					// inputs from a small pool that differ in one byte, and prefixes of each other
					id := r.IntN(2000)
					for j := range data {
						data[j] = byte(id >> (uint(j%2) * 8))
					}
					data[r.IntN(n)] ^= byte(id % 3)
					want := Hash(sha256.Sum256(data))
					if h, ok := c.Load(data); ok {
						hits.Add(1)
						if h != want {
							bad.Add(1)
						}
					} else {
						miss.Add(1)
						c.Store(data, want)
					}
					// overwrite the memory the key came from
					for j := range data {
						data[j] = byte(r.Uint32())
					}
				}
			}(g)
		}
		wg.Wait()
		// every stored key must still map to the hash of its own bytes
		c.m.Range(func(k, v any) bool {
			if Hash(sha256.Sum256([]byte(k.(string)))) != v.(Hash) {
				bad.Add(1)
			}
			return true
		})
	}
	fmt.Println("hits", hits.Load(), "misses", miss.Load(), "wrong", bad.Load())
}
