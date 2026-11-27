// Lists top-level funcs, methods, package vars and types of the non-test Go files given as arguments.
package main

import (
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"os"
	"strings"
)

func recv(e ast.Expr) string {
	switch t := e.(type) {
	case *ast.StarExpr:
		return "(*" + recv(t.X) + ")"
	case *ast.Ident:
		return t.Name
	case *ast.IndexExpr:
		return recv(t.X)
	case *ast.IndexListExpr:
		return recv(t.X)
	}
	return "?"
}

func main() {
	fs := token.NewFileSet()
	for _, p := range os.Args[1:] {
		if strings.HasSuffix(p, "_test.go") {
			continue
		}
		f, err := parser.ParseFile(fs, p, nil, 0)
		if err != nil {
			fmt.Fprintln(os.Stderr, p, err)
			continue
		}
		base := p[strings.LastIndex(p, "/")+1:]
		for _, d := range f.Decls {
			switch x := d.(type) {
			case *ast.FuncDecl:
				n := x.Name.Name
				if x.Recv != nil && len(x.Recv.List) > 0 {
					n = recv(x.Recv.List[0].Type) + "." + n
				}
				fmt.Printf("func %s %s:%d\n", n, base, fs.Position(x.Pos()).Line)
			case *ast.GenDecl:
				for _, s := range x.Specs {
					switch y := s.(type) {
					case *ast.ValueSpec:
						if x.Tok == token.VAR {
							for _, id := range y.Names {
								fmt.Printf("var %s %s:%d\n", id.Name, base, fs.Position(id.Pos()).Line)
							}
						}
					case *ast.TypeSpec:
						fmt.Printf("type %s %s:%d\n", y.Name.Name, base, fs.Position(y.Pos()).Line)
					}
				}
			}
		}
	}
}
