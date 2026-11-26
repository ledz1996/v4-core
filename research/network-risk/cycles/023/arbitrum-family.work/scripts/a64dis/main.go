// Disassemble raw arm64 function bytes (from the pcln dump) in GNU syntax.
package main

import (
	"a64dis/arm64asm"
	"bufio"
	"fmt"
	"os"
	"regexp"
	"strconv"
	"strings"
)

func main() {
	idx, _ := os.Open(os.Args[1])
	dir := os.Args[2]
	sc := bufio.NewScanner(idx)
	re := regexp.MustCompile(`[^A-Za-z0-9_.]`)
	for sc.Scan() {
		p := strings.Fields(sc.Text())
		entry, _ := strconv.ParseUint(p[1], 16, 64)
		b, _ := os.ReadFile(dir + "/" + re.ReplaceAllString(p[0], "_") + ".bin")
		fmt.Printf("### %s %s\n", p[0], p[4])
		for i := 0; i+4 <= len(b); i += 4 {
			inst, err := arm64asm.Decode(b[i : i+4])
			s := "?"
			if err == nil { s = arm64asm.GNUSyntax(inst) }
			fmt.Printf("  %x:\t%02x %02x %02x %02x \t%s\n", entry+uint64(i), b[i], b[i+1], b[i+2], b[i+3], s)
		}
	}
}
