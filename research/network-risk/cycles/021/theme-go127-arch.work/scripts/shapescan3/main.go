// shapescan: search Go source trees for the code shapes of Go issues 81863 and 82839.
//
// Usage: shapescan <tree-name> <tree-root> <module-path> <uint256-root> <pkgdir>...
//
// Each pkgdir is relative to tree-root. Packages are parsed (non-test files, all build tags) and
// type-checked with go/types; imports inside the tree and holiman/uint256 are resolved from source,
// the standard library from GOROOT source, anything else becomes an empty package (errors ignored).
//
// Shape A (issue 82839, prove): an ordered comparison (<, <=, >, >=) where one side is a conversion to a
// wider integer type of an expression whose type is int8, int16 or int32 (a value-preserving sign
// extension), and the other side is a constant that does not fit the narrow type. Also reported, as
// lower tiers: the same with a non-constant other side (A2), and every narrow-signed-to-wider conversion
// elsewhere (A3), because inlining and constant propagation can turn those into the A shape.
//
// Shape B (issue 81863, deadstore after branchelim): a pointer variable that receives the address of two
// or more different local variables or parameters of the same function (B1); a function returning one of
// two pointer parameters by a branch (B2, the inlined form) and each call that passes two address-of
// local operands to such a function (B3).
// Cycle 21 (theme-go127-arch) adds shapes D1 to D5 for compiler faults that go1.27.3 still holds:
// D1 Go issue 82825 (amd64): a non-constant shift count that the same function also compares with the shift width.
// D2 Go issue 82777 (arm64): a conditional assignment of a bitwise complement ^y (CSINV after lowering).
// D3 master 607cfcea17a4 (arm64): a signed comparison with 0 of a - x*y (MSUB noov with InvertFlags).
// D4 master a15f882163a2 (arm64): 32-bit byte reversals (REVW), nested=true when one feeds another.
// D5 Go issue 83036 (phiopt): a bool declared outside a loop and set to a constant inside it.
// EXTRA=modpath=dir[,modpath=dir] resolves further modules from source.
package main

import (
	"encoding/json"
	"fmt"
	"go/ast"
	"go/constant"
	"go/importer"
	"go/parser"
	"go/token"
	"go/types"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

type Cand struct {
	Tree, Pkg, Shape, File string
	Line                   int
	Func, Code, Note       string
}

var (
	fset     = token.NewFileSet()
	treeRoot string
	modPath  string
	u256Root string
	cache    = map[string]*types.Package{}
	stdImp   types.Importer
	pkgFiles = map[string][]*ast.File{}
	pkgInfo  = map[string]*types.Info{}
)

func parseDir(dir string) []*ast.File {
	ents, err := os.ReadDir(dir)
	if err != nil {
		return nil
	}
	var fs []*ast.File
	for _, e := range ents {
		n := e.Name()
		if !strings.HasSuffix(n, ".go") || strings.HasSuffix(n, "_test.go") {
			continue
		}
		f, err := parser.ParseFile(fset, filepath.Join(dir, n), nil, parser.ParseComments)
		if err == nil {
			fs = append(fs, f)
		}
	}
	// keep one package name (the majority), drop e.g. package main helpers
	cnt := map[string]int{}
	for _, f := range fs {
		cnt[f.Name.Name]++
	}
	best := ""
	for k, v := range cnt {
		if best == "" || v > cnt[best] {
			best = k
		}
	}
	var out []*ast.File
	for _, f := range fs {
		if f.Name.Name == best {
			out = append(out, f)
		}
	}
	return out
}

type imp struct{}

func (imp) Import(path string) (*types.Package, error) {
	if p, ok := cache[path]; ok {
		return p, nil
	}
	dir := ""
	switch {
	case path == "github.com/holiman/uint256":
		dir = u256Root
	case strings.HasPrefix(path, modPath+"/"):
		dir = filepath.Join(treeRoot, strings.TrimPrefix(path, modPath+"/"))
	case extraDir(path) != "":
		dir = extraDir(path)
	case !strings.Contains(strings.Split(path, "/")[0], "."):
		p, err := stdImp.Import(path)
		if err == nil {
			cache[path] = p
			return p, nil
		}
	}
	if dir != "" {
		if fs := parseDir(dir); len(fs) > 0 {
			p, _ := check(path, fs)
			return p, nil
		}
	}
	name := filepath.Base(path)
	p := types.NewPackage(path, name)
	p.MarkComplete()
	cache[path] = p
	return p, nil
}

func extraDir(path string) string {
	for _, kv := range strings.Split(os.Getenv("EXTRA"), ",") {
		i := strings.Index(kv, "=")
		if i < 0 {
			continue
		}
		m, d := kv[:i], kv[i+1:]
		if path == m {
			return d
		}
		if strings.HasPrefix(path, m+"/") {
			return filepath.Join(d, strings.TrimPrefix(path, m+"/"))
		}
	}
	return ""
}

// norm strips parentheses and integer conversions so that n, uint(n) and uint64(n) compare equal.
func norm(info *types.Info, e ast.Expr) string {
	e = strip(e)
	for {
		c, ok := e.(*ast.CallExpr)
		if !ok || len(c.Args) != 1 {
			break
		}
		tv, ok := info.Types[c.Fun]
		if !ok || !tv.IsType() || intBits(tv.Type) == 0 {
			break
		}
		e = strip(c.Args[0])
	}
	return src(e)
}

func isMul(e ast.Expr) bool {
	b, ok := strip(e).(*ast.BinaryExpr)
	return ok && b.Op == token.MUL
}

func signedInt(t types.Type) bool {
	if t == nil {
		return false
	}
	b, ok := t.Underlying().(*types.Basic)
	return ok && b.Info()&types.IsInteger != 0 && b.Info()&types.IsUnsigned == 0
}

func isBool(t types.Type) bool {
	if t == nil {
		return false
	}
	b, ok := t.Underlying().(*types.Basic)
	return ok && b.Info()&types.IsBoolean != 0
}

func calleeName(info *types.Info, c *ast.CallExpr) string {
	switch fn := strip(c.Fun).(type) {
	case *ast.SelectorExpr:
		if o := info.Uses[fn.Sel]; o != nil {
			if o.Pkg() != nil {
				return o.Pkg().Path() + "." + src(fn)
			}
		}
		return src(fn)
	case *ast.Ident:
		return fn.Name
	}
	return ""
}

func check(path string, fs []*ast.File) (*types.Package, *types.Info) {
	info := &types.Info{Types: map[ast.Expr]types.TypeAndValue{}, Defs: map[*ast.Ident]types.Object{}, Uses: map[*ast.Ident]types.Object{}}
	conf := types.Config{Importer: imp{}, Error: func(error) {}, FakeImportC: true}
	p, _ := conf.Check(path, fset, fs, info)
	cache[path] = p
	pkgFiles[path] = fs
	pkgInfo[path] = info
	return p, info
}

func narrowSigned(t types.Type) (int, bool) {
	if t == nil {
		return 0, false
	}
	b, ok := t.Underlying().(*types.Basic)
	if !ok {
		return 0, false
	}
	switch b.Kind() {
	case types.Int8:
		return 8, true
	case types.Int16:
		return 16, true
	case types.Int32:
		return 32, true
	}
	return 0, false
}

func intBits(t types.Type) int {
	if t == nil {
		return 0
	}
	b, ok := t.Underlying().(*types.Basic)
	if !ok || b.Info()&types.IsInteger == 0 {
		return 0
	}
	switch b.Kind() {
	case types.Int8, types.Uint8:
		return 8
	case types.Int16, types.Uint16:
		return 16
	case types.Int32, types.Uint32:
		return 32
	default:
		return 64
	}
}

func strip(e ast.Expr) ast.Expr {
	for {
		p, ok := e.(*ast.ParenExpr)
		if !ok {
			return e
		}
		e = p.X
	}
}

// widen returns the narrow argument if e is a conversion of a narrow signed expression to a wider integer type.
func widen(info *types.Info, e ast.Expr) (ast.Expr, int, bool) {
	c, ok := strip(e).(*ast.CallExpr)
	if !ok || len(c.Args) != 1 {
		return nil, 0, false
	}
	tv, ok := info.Types[c.Fun]
	if !ok || !tv.IsType() {
		return nil, 0, false
	}
	nb, ok := narrowSigned(info.TypeOf(c.Args[0]))
	if !ok {
		return nil, 0, false
	}
	if intBits(tv.Type) <= nb {
		return nil, 0, false
	}
	return c.Args[0], nb, true
}

func src(e ast.Node) string {
	var sb strings.Builder
	start, end := fset.Position(e.Pos()), fset.Position(e.End())
	b, err := os.ReadFile(start.Filename)
	if err != nil || end.Offset > len(b) {
		return ""
	}
	sb.Write(b[start.Offset:end.Offset])
	s := strings.Join(strings.Fields(sb.String()), " ")
	if len(s) > 160 {
		s = s[:160] + "..."
	}
	return s
}

func fits(v constant.Value, bits int) bool {
	v = constant.ToInt(v)
	if v.Kind() != constant.Int {
		return true
	}
	lo := constant.MakeInt64(-(int64(1) << (bits - 1)))
	hi := constant.MakeInt64(int64(1)<<(bits-1) - 1)
	return constant.Compare(v, token.GEQ, lo) && constant.Compare(v, token.LEQ, hi)
}

func isConstDelta(info *types.Info, e ast.Expr) bool {
	b, ok := strip(e).(*ast.BinaryExpr)
	if !ok || (b.Op != token.ADD && b.Op != token.SUB) {
		return false
	}
	return info.Types[b.X].Value != nil || info.Types[b.Y].Value != nil
}

func main() {
	tree := os.Args[1]
	treeRoot, modPath, u256Root = os.Args[2], os.Args[3], os.Args[4]
	stdImp = importer.ForCompiler(fset, "source", nil)
	var cands []Cand
	for _, rel := range os.Args[5:] {
		dir := filepath.Join(treeRoot, rel)
		fs := parseDir(dir)
		if len(fs) == 0 {
			continue
		}
		path := modPath + "/" + rel
		if rel == "." {
			path = modPath
		}
		var info *types.Info
		if _, ok := pkgInfo[path]; ok {
			info = pkgInfo[path]
			fs = pkgFiles[path]
		} else {
			_, info = check(path, fs)
		}
		n := 0
		add := func(shape string, node ast.Node, fn, note string) {
			pos := fset.Position(node.Pos())
			r, _ := filepath.Rel(treeRoot, pos.Filename)
			cands = append(cands, Cand{tree, rel, shape, r, pos.Line, fn, src(node), note})
			n++
		}
		// B2: functions that return one of two pointer params chosen by a branch
		selectors := map[types.Object]bool{}
		for _, f := range fs {
			for _, d := range f.Decls {
				fd, ok := d.(*ast.FuncDecl)
				if !ok || fd.Body == nil || fd.Type.Results == nil {
					continue
				}
				params := map[types.Object]bool{}
				for _, fl := range fd.Type.Params.List {
					for _, nm := range fl.Names {
						if o := info.Defs[nm]; o != nil {
							if _, isPtr := o.Type().Underlying().(*types.Pointer); isPtr {
								params[o] = true
							}
						}
					}
				}
				ret := map[types.Object]bool{}
				ast.Inspect(fd.Body, func(x ast.Node) bool {
					if r, ok := x.(*ast.ReturnStmt); ok {
						for _, e := range r.Results {
							if id, ok := strip(e).(*ast.Ident); ok {
								if o := info.Uses[id]; o != nil && params[o] {
									ret[o] = true
								}
							}
						}
					}
					return true
				})
				if len(ret) >= 2 {
					add("B2", fd.Name, fd.Name.Name, "returns one of several pointer parameters")
					if o := info.Defs[fd.Name]; o != nil {
						selectors[o] = true
					}
				}
			}
		}
		for _, f := range fs {
			for _, d := range f.Decls {
				fd, ok := d.(*ast.FuncDecl)
				if !ok || fd.Body == nil {
					continue
				}
				fname := fd.Name.Name
				if fd.Recv != nil && len(fd.Recv.List) > 0 {
					fname = src(fd.Recv.List[0].Type) + "." + fname
				}
				// locals and params of this function
				local := map[types.Object]bool{}
				ast.Inspect(fd, func(x ast.Node) bool {
					if id, ok := x.(*ast.Ident); ok {
						if o, ok := info.Defs[id].(*types.Var); ok && !o.IsField() {
							local[o] = true
						}
					}
					return true
				})
				anon := map[ast.Node]types.Object{}
				rootLocal := func(e ast.Expr) types.Object {
					// new(T) and &T{...} become stack autos when they do not escape
					if c, ok := strip(e).(*ast.CallExpr); ok && len(c.Args) == 1 {
						if id, ok := strip(c.Fun).(*ast.Ident); ok && id.Name == "new" {
							if _, isB := info.Uses[id].(*types.Builtin); isB {
								if anon[c] == nil {
									anon[c] = types.NewVar(c.Pos(), nil, "new@"+fmt.Sprint(fset.Position(c.Pos()).Line), nil)
								}
								return anon[c]
							}
						}
					}
					u, ok := strip(e).(*ast.UnaryExpr)
					if !ok || u.Op != token.AND {
						return nil
					}
					if cl, ok := strip(u.X).(*ast.CompositeLit); ok {
						if anon[cl] == nil {
							anon[cl] = types.NewVar(cl.Pos(), nil, "lit@"+fmt.Sprint(fset.Position(cl.Pos()).Line), nil)
						}
						return anon[cl]
					}
					x := strip(u.X)
					for {
						switch y := x.(type) {
						case *ast.SelectorExpr:
							if info.Types[y.X].Type != nil {
								if _, isPtr := info.TypeOf(y.X).Underlying().(*types.Pointer); isPtr {
									return nil // through a pointer: heap or caller memory
								}
							}
							x = strip(y.X)
							continue
						case *ast.IndexExpr:
							if t := info.TypeOf(y.X); t != nil {
								if _, isArr := t.Underlying().(*types.Array); !isArr {
									return nil // slice or map element: not a stack auto
								}
							}
							x = strip(y.X)
							continue
						case *ast.Ident:
							if o := info.Uses[y]; o != nil && local[o] {
								return o
							}
							return nil
						}
						return nil
					}
				}
				// ---- D shapes (cycle 21) ----
				type shiftSite struct {
					node  ast.Node
					width int
				}
				shifts := map[string][]shiftSite{}
				type cmpSite struct {
					node   ast.Node
					c      int64
					op     token.Token
					branch bool
				}
				cmps := map[string][]cmpSite{}
				branchConds := map[ast.Expr]bool{}
				ast.Inspect(fd.Body, func(x ast.Node) bool {
					switch s := x.(type) {
					case *ast.IfStmt:
						branchConds[strip(s.Cond)] = true
					case *ast.ForStmt:
						if s.Cond != nil {
							branchConds[strip(s.Cond)] = true
						}
					case *ast.CaseClause:
						for _, e := range s.List {
							branchConds[strip(e)] = true
						}
					}
					return true
				})
				addShift := func(n ast.Node, xexpr, y ast.Expr) {
					if info.Types[y].Value != nil {
						return
					}
					// a count masked with a constant below the width is bounded
					if b, ok := strip(y).(*ast.BinaryExpr); ok && b.Op == token.AND {
						if info.Types[b.Y].Value != nil || info.Types[b.X].Value != nil {
							return
						}
					}
					w := intBits(info.TypeOf(xexpr))
					if w == 0 {
						w = intBits(info.TypeOf(n.(ast.Expr)))
					}
					if w == 0 {
						return
					}
					k := norm(info, y)
					shifts[k] = append(shifts[k], shiftSite{n, w})
				}
				ast.Inspect(fd.Body, func(x ast.Node) bool {
					switch s := x.(type) {
					case *ast.BinaryExpr:
						if s.Op == token.SHL || s.Op == token.SHR {
							addShift(s, s.X, s.Y)
						}
						switch s.Op {
						case token.EQL, token.NEQ, token.LEQ, token.GTR, token.LSS, token.GEQ:
							for _, pr := range [][2]ast.Expr{{s.X, s.Y}, {s.Y, s.X}} {
								if tv := info.Types[pr[1]]; tv.Value != nil {
									if v, ok := constant.Int64Val(constant.ToInt(tv.Value)); ok && (v == 8 || v == 16 || v == 32 || v == 64) {
										k := norm(info, pr[0])
										cmps[k] = append(cmps[k], cmpSite{s, v, s.Op, branchConds[s]})
									}
								}
							}
							// D3: signed a - x*y compared with 0
							if s.Op != token.EQL && s.Op != token.NEQ {
								for _, pr := range [][2]ast.Expr{{s.X, s.Y}, {s.Y, s.X}} {
									if tv := info.Types[pr[1]]; tv.Value != nil && constant.Sign(constant.ToInt(tv.Value)) == 0 {
										if b, ok := strip(pr[0]).(*ast.BinaryExpr); ok && signedInt(info.TypeOf(b)) {
											if (b.Op == token.SUB && isMul(b.Y)) || (b.Op == token.ADD && (isMul(b.X) || isMul(b.Y))) {
												add("D3", s, fname, "signed a - x*y (or a + x*y) compared with 0")
											}
										}
									}
								}
							}
						}
						if s.Op == token.SUB && isMul(s.Y) && signedInt(info.TypeOf(s)) {
							add("D3m", s, fname, "signed a - x*y (MSUB candidate)")
						}
					case *ast.AssignStmt:
						if (s.Tok == token.SHL_ASSIGN || s.Tok == token.SHR_ASSIGN) && len(s.Lhs) == 1 {
							addShift(s, s.Lhs[0], s.Rhs[0])
						}
					case *ast.CallExpr:
						cn := calleeName(info, s)
						if strings.HasSuffix(cn, "ReverseBytes32") || strings.Contains(cn, "BigEndian.Uint32") || strings.Contains(cn, "BigEndian.PutUint32") || strings.Contains(cn, "BigEndian.AppendUint32") {
							nested := false
							for _, a := range s.Args {
								ast.Inspect(a, func(y ast.Node) bool {
									if c2, ok := y.(*ast.CallExpr); ok {
										cn2 := calleeName(info, c2)
										if strings.HasSuffix(cn2, "ReverseBytes32") || strings.Contains(cn2, "BigEndian.Uint32") {
											nested = true
										}
									}
									return true
								})
							}
							add("D4", s, fname, fmt.Sprintf("32-bit byte reversal %s nested=%v", cn, nested))
						}
					}
					return true
				})
				for k, ss := range shifts {
					for _, c := range cmps[k] {
						match := false
						for _, sh := range ss {
							if int64(sh.width) == c.c {
								match = true
							}
						}
						if !match {
							continue
						}
						tier := "D1"
						if c.op == token.LSS || c.op == token.GEQ {
							tier = "D1x"
						}
						add(tier, c.node, fname, fmt.Sprintf("count %q shifted unbounded at line %d and compared %s %d, branch=%v", k, fset.Position(ss[0].node.Pos()).Line, c.op, c.c, c.branch))
					}
				}
				// D2: ^y assigned inside an if body to a variable that is also assigned elsewhere
				assigned := map[types.Object]int{}
				ast.Inspect(fd.Body, func(x ast.Node) bool {
					if a, ok := x.(*ast.AssignStmt); ok {
						for _, l := range a.Lhs {
							if id, ok := strip(l).(*ast.Ident); ok {
								o := info.Defs[id]
								if o == nil {
									o = info.Uses[id]
								}
								if o != nil {
									assigned[o]++
								}
							}
						}
					}
					if vs, ok := x.(*ast.ValueSpec); ok {
						for _, id := range vs.Names {
							if o := info.Defs[id]; o != nil {
								assigned[o]++
							}
						}
					}
					return true
				})
				var inIf func(n ast.Node, depth int)
				inIf = func(n ast.Node, depth int) {
					ast.Inspect(n, func(x ast.Node) bool {
						if ifs, ok := x.(*ast.IfStmt); ok && x != n {
							inIf(ifs.Body, depth+1)
							if ifs.Else != nil {
								inIf(ifs.Else, depth+1)
							}
							return false
						}
						if a, ok := x.(*ast.AssignStmt); ok && depth > 0 && len(a.Lhs) == len(a.Rhs) {
							for i := range a.Rhs {
								if u, ok := strip(a.Rhs[i]).(*ast.UnaryExpr); ok && u.Op == token.XOR {
									if id, ok := strip(a.Lhs[i]).(*ast.Ident); ok {
										o := info.Uses[id]
										if o == nil {
											o = info.Defs[id]
										}
										if o != nil && assigned[o] >= 2 {
											add("D2", a, fname, "conditional assignment of a bitwise complement")
										}
									}
								}
							}
						}
						return true
					})
				}
				inIf(fd.Body, 0)
				// D5: bool declared outside a loop and set to a constant inside it
				declPos := map[types.Object]token.Pos{}
				for o := range local {
					declPos[o] = o.Pos()
				}
				ast.Inspect(fd.Body, func(x ast.Node) bool {
					var body *ast.BlockStmt
					switch l := x.(type) {
					case *ast.ForStmt:
						body = l.Body
					case *ast.RangeStmt:
						body = l.Body
					default:
						return true
					}
					ast.Inspect(body, func(y ast.Node) bool {
						if a, ok := y.(*ast.AssignStmt); ok && a.Tok == token.ASSIGN && len(a.Lhs) == len(a.Rhs) {
							for i := range a.Lhs {
								if id, ok := strip(a.Lhs[i]).(*ast.Ident); ok {
									if o := info.Uses[id]; o != nil && local[o] && isBool(o.Type()) && o.Pos() < x.Pos() {
										if tv := info.Types[a.Rhs[i]]; tv.Value != nil {
											add("D5", a, fname, fmt.Sprintf("bool %s declared before the loop at line %d, set to %s inside", id.Name, fset.Position(x.Pos()).Line, tv.Value))
										}
									}
								}
							}
						}
						return true
					})
					return true
				})
				// B1: pointer var assigned &local of two or more different locals
				targets := map[types.Object]map[types.Object]ast.Node{}
				note := func(lhs ast.Expr, rhs ast.Expr) {
					id, ok := strip(lhs).(*ast.Ident)
					if !ok {
						return
					}
					o := info.Defs[id]
					if o == nil {
						o = info.Uses[id]
					}
					if o == nil {
						return
					}
					if _, isPtr := o.Type().Underlying().(*types.Pointer); !isPtr {
						return
					}
					if targets[o] == nil {
						targets[o] = map[types.Object]ast.Node{}
					}
					if r := rootLocal(rhs); r != nil {
						targets[o][r] = rhs
					} else {
						// any other source (parameter, call result, heap pointer): one synthetic key per site
						targets[o][types.NewVar(rhs.Pos(), nil, "other:"+src(rhs), nil)] = rhs
					}
				}
				// pointer parameters and receivers enter with a caller-supplied value
				var plists []*ast.Field
				if fd.Recv != nil {
					plists = append(plists, fd.Recv.List...)
				}
				plists = append(plists, fd.Type.Params.List...)
				for _, fl := range plists {
					for _, nm := range fl.Names {
						if o := info.Defs[nm]; o != nil {
							if _, isPtr := o.Type().Underlying().(*types.Pointer); isPtr {
								targets[o] = map[types.Object]ast.Node{types.NewVar(nm.Pos(), nil, "other:param "+nm.Name, nil): nm}
							}
						}
					}
				}
				ast.Inspect(fd.Body, func(x ast.Node) bool {
					switch s := x.(type) {
					case *ast.AssignStmt:
						if len(s.Lhs) == len(s.Rhs) {
							for i := range s.Lhs {
								note(s.Lhs[i], s.Rhs[i])
							}
						}
					case *ast.ValueSpec:
						if len(s.Names) == len(s.Values) {
							for i := range s.Names {
								note(s.Names[i], s.Values[i])
							}
						}
					case *ast.BinaryExpr:
						// Cycle 20 shapes from the Go release branch logs (theme-evidence-audit).
						// C1, Go issue 81868 (fixed go1.26.11, go1.27.4): a shift of an 8, 16 or 32 bit integer by a
						// constant amount; generic.rules gave the canonical Const64 amount the narrow type of the shifted value.
						// C2, Go issue 79182 (fixed go1.25.11, go1.26.4): (x + x) << 63 or << 31 rewritten to x << 0 on amd64;
						// every shift by 63 or 31 is reported, with dbl=true when the left side is x + x, x * 2 or x << 1.
						if s.Op == token.SHL || s.Op == token.SHR {
							if tv := info.Types[s.Y]; tv.Value != nil {
								nb := 0
				if tx := info.TypeOf(s.X); tx != nil {
					nb = intBits(tx)
				}
								if nb == 8 || nb == 16 || nb == 32 {
									add("C1", s, fname, fmt.Sprintf("%d bit value shifted by constant %s", nb, tv.Value))
								}
								if v, ok := constant.Int64Val(tv.Value); ok && s.Op == token.SHL && (v == 63 || v == 31) {
									dbl := false
									if be, ok := strip(s.X).(*ast.BinaryExpr); ok {
										if be.Op == token.ADD && src(be.X) == src(be.Y) {
											dbl = true
										}
										if be.Op == token.MUL || be.Op == token.SHL {
											if c := info.Types[be.Y]; c.Value != nil {
												if w, ok := constant.Int64Val(c.Value); ok && ((be.Op == token.MUL && w == 2) || (be.Op == token.SHL && w == 1)) {
													dbl = true
												}
											}
										}
									}
									add("C2", s, fname, fmt.Sprintf("shift left by %d of a %d bit value, dbl=%v", v, nb, dbl))
								}
							}
						}
						if s.Op == token.LSS || s.Op == token.LEQ || s.Op == token.GTR || s.Op == token.GEQ {
							for _, pair := range [][2]ast.Expr{{s.X, s.Y}, {s.Y, s.X}} {
								if arg, nb, ok := widen(info, pair[0]); ok {
									tv := info.Types[pair[1]]
									delta := isConstDelta(info, arg)
									if tv.Value != nil {
										if !fits(tv.Value, nb) {
											add("A1", s, fname, fmt.Sprintf("int%d widened, constant %s outside int%d, constDelta=%v", nb, tv.Value, nb, delta))
										} else {
											add("A1fit", s, fname, fmt.Sprintf("int%d widened, constant %s fits int%d (fix keeps the derivation), constDelta=%v", nb, tv.Value, nb, delta))
										}
									} else {
										add("A2", s, fname, fmt.Sprintf("int%d widened, compared with non-constant, constDelta=%v", nb, delta))
									}
								}
							}
						}
					case *ast.CallExpr:
						if id, ok := strip(s.Fun).(*ast.Ident); ok && id.Name == "make" && len(s.Args) >= 2 {
							if t0 := info.TypeOf(s.Args[0]); t0 != nil {
								if _, isSl := t0.Underlying().(*types.Slice); isSl {
								if tv := info.Types[s.Args[1]]; tv.Value == nil {
									add("C3", s, fname, "make of a slice with a non-constant length")
								}
								}
							}
						}
						// A3u: conversion to a signed integer type of an operand whose type go/types could not resolve
						if len(s.Args) == 1 {
							if tv, ok := info.Types[s.Fun]; ok && tv.IsType() && intBits(tv.Type) > 8 {
								if b, ok := tv.Type.Underlying().(*types.Basic); ok && b.Info()&types.IsUnsigned == 0 {
									at := info.TypeOf(s.Args[0])
									if at == nil || at == types.Typ[types.Invalid] {
										add("A3u", s, fname, "signed conversion of an operand of unresolved type")
									}
								}
							}
						}
						if arg, nb, ok := widen(info, s); ok {
							add("A3", s, fname, fmt.Sprintf("int%d -> %s conversion, constDelta=%v", nb, src(s.Fun), isConstDelta(info, arg)))
						}
						// B3
						var fobj types.Object
						switch fn := strip(s.Fun).(type) {
						case *ast.Ident:
							fobj = info.Uses[fn]
						case *ast.SelectorExpr:
							fobj = info.Uses[fn.Sel]
						}
						if fobj != nil && selectors[fobj] {
							roots := map[types.Object]bool{}
							for _, a := range s.Args {
								if r := rootLocal(a); r != nil {
									roots[r] = true
								}
							}
							if len(roots) >= 2 {
								add("B3", s, fname, "selector called with two address-of locals")
							}
						}
					}
					return true
				})
				for p, m := range targets {
					autos := 0
					for r := range m {
						if !strings.HasPrefix(r.Name(), "other:") {
							autos++
						}
					}
					if autos >= 1 && len(m) >= 2 && autos < 2 {
						var names []string
						var first ast.Node
						for r, nd := range m {
							names = append(names, r.Name())
							if first == nil || nd.Pos() < first.Pos() {
								first = nd
							}
						}
						sort.Strings(names)
						add("B4", first, fname, fmt.Sprintf("pointer %s takes one stack-auto address and another pointer: %s", p.Name(), strings.Join(names, " ; ")))
					}
					if autos >= 2 {
						var names []string
						var first ast.Node
						for r, nd := range m {
							names = append(names, r.Name())
							if first == nil || nd.Pos() < first.Pos() {
								first = nd
							}
						}
						sort.Strings(names)
						add("B1", first, fname, fmt.Sprintf("pointer %s takes the address of %s", p.Name(), strings.Join(names, ", ")))
					}
				}
			}
		}
		fmt.Fprintf(os.Stderr, "%s %s files=%d cands=%d\n", tree, rel, len(fs), n)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", " ")
	enc.Encode(cands)
}
