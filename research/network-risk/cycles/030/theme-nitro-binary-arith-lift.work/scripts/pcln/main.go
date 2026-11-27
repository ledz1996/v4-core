// List functions from .gopclntab and dump the machine code bytes of chosen ones.
package main

import (
	"debug/elf"
	"debug/gosym"
	"fmt"
	"os"
	"regexp"
)

func main() {
	f, err := elf.Open(os.Args[1])
	if err != nil { panic(err) }
	pcln := f.Section(".gopclntab")
	pd, _ := pcln.Data()
	text := f.Section(".text")
	base := text.Addr
	if v := os.Getenv("TEXTBASE"); v != "" { fmt.Sscanf(v, "%x", &base) }
	lt := gosym.NewLineTable(pd, base)
	tab, err := gosym.NewTable(nil, lt)
	if err != nil { panic(err) }
	re := regexp.MustCompile(os.Args[2])
	td, _ := text.Data()
	for _, fn := range tab.Funcs {
		if re.MatchString(fn.Name) {
			file, line, _ := tab.PCToLine(fn.Entry)
			fmt.Printf("%s %x %x %d %s:%d\n", fn.Name, fn.Entry, fn.End, fn.End-fn.Entry, file, line)
			if len(os.Args) > 3 {
				b := td[fn.Entry-text.Addr : fn.End-text.Addr]
				os.WriteFile(os.Args[3]+"/"+regexp.MustCompile(`[^A-Za-z0-9_.]`).ReplaceAllString(fn.Name, "_")+".bin", b, 0644)
			}
		}
	}
}
