// undef: type-check one package directory with imports stubbed, print "undefined:" errors for
// unqualified identifiers, which point at files of the same package missing from the download.
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"go/types"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type stub struct{}

func (stub) Import(p string) (*types.Package, error) { return nil, fmt.Errorf("stub") }

func main() {
	dir := os.Args[1]
	fset := token.NewFileSet()
	var files []*ast.File
	ents, _ := os.ReadDir(dir)
	for _, e := range ents {
		n := e.Name()
		if !strings.HasSuffix(n, ".go") || strings.HasSuffix(n, "_test.go") {
			continue
		}
		f, err := parser.ParseFile(fset, filepath.Join(dir, n), nil, 0)
		if err == nil {
			files = append(files, f)
		}
	}
	seen := map[string]bool{}
	conf := types.Config{Importer: stub{}, Error: func(err error) {
		s := err.Error()
		if i := strings.Index(s, "undefined: "); i >= 0 {
			id := s[i+len("undefined: "):]
			if !strings.Contains(id, ".") {
				seen[id] = true
			}
		}
	}}
	conf.Check("p", fset, files, nil)
	var ids []string
	for k := range seen {
		ids = append(ids, k)
	}
	sort.Strings(ids)
	fmt.Println(len(files), "files;", len(ids), "undefined unqualified identifiers")
	for _, k := range ids {
		fmt.Println(" ", k)
	}
}
