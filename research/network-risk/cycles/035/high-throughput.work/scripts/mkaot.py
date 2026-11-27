# Builds a harness around the arithmetic handlers of megaeth-labs/evmone-compiler master,
# copied verbatim by line range from dl/eco/lib/compiler/aot_instructions.hpp (148-306) and aot_intx.hpp (addmod..count_significant_bytes).
import sys
W='/home/user/v4-core/research/network-risk/cycles/035/high-throughput.work'
ins=open(W+'/dl/eco/lib/compiler/aot_instructions.hpp').read().split('\n')
ix=open(W+'/dl/eco/lib/compiler/aot_intx.hpp').read()
stacktop='\n'.join(ins[18:40])
handlers='\n'.join(ins[147:307])
a=ix.index('inline uint256 addmod'); b=ix.index('} // namespace evmone::intx')
intxpart=ix[a:b]
src=f'''
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <tuple>
#include <string>
#include <bit>
#include <sys/types.h>
#pragma GCC diagnostic ignored "-Wbit-int-extension"
namespace evmone {{
using uint128 = unsigned _BitInt(128);
using uint256 = unsigned _BitInt(256);
using uint257 = unsigned _BitInt(257);
using uint512 = unsigned _BitInt(512);
using int256 = signed _BitInt(256);
using native_jumpdest = void*;
enum evmc_status_code {{ EVMC_SUCCESS=0, EVMC_OUT_OF_GAS=3 }};
enum {{ EVMC_SPURIOUS_DRAGON=3 }};
struct ExecutionState {{ int rev=12; }};
namespace intx {{
{intxpart}
}}
{stacktop}
namespace instr::core {{
#define PARAMS StackTop& stack [[maybe_unused]], int64_t& gas_left [[maybe_unused]], evmc_status_code& status [[maybe_unused]], native_jumpdest& jump_addr [[maybe_unused]], ExecutionState& state [[maybe_unused]]
#define RETURN_STATUS(StatusCode) {{ status = StatusCode; return; }}
{handlers}
}}
}}
using namespace evmone;
static uint256 rd(const char* h){{ uint256 x=0; for(const char*p=h;*p;++p){{int c=*p; int d=c<='9'?c-'0':(c|32)-'a'+10; x=(x<<(unsigned)4)|(uint256)(unsigned)d;}} return x; }}
static void wr(uint256 x){{ char b[65]; for(int i=63;i>=0;--i){{ b[i]="0123456789abcdef"[(unsigned)(x&(uint256)15)]; x>>= (unsigned)4; }} b[64]=0; printf("%s\\n",b); }}
int main(){{
  char op[16], A[80], B[80], C[80];
  while(scanf("%15s %79s %79s %79s",op,A,B,C)==4){{
    uint256 st[8]={{}}; // st[top] is the first EVM operand
    uint256 a=rd(A), b=rd(B), c=rd(C);
    st[4]=c; st[5]=b; st[6]=a; StackTop s(&st[6]);
    int64_t g=1<<30; evmc_status_code status=EVMC_SUCCESS; native_jumpdest j=nullptr; ExecutionState es;
    int resIdx=5; // binary ops: result at second slot
    std::string o(op);
    using namespace instr::core;
    if(o=="DIV") div(s,g,status,j,es); else if(o=="SDIV") sdiv(s,g,status,j,es);
    else if(o=="MOD") mod(s,g,status,j,es); else if(o=="SMOD") smod(s,g,status,j,es);
    else if(o=="ADDMOD") {{ addmod(s,g,status,j,es); resIdx=4; }} else if(o=="MULMOD") {{ mulmod(s,g,status,j,es); resIdx=4; }}
    else if(o=="EXP") exp(s,g,status,j,es); else if(o=="SIGNEXTEND") signextend(s,g,status,j,es);
    else if(o=="LT") lt(s,g,status,j,es); else if(o=="GT") gt(s,g,status,j,es);
    else if(o=="SLT") slt(s,g,status,j,es); else if(o=="SGT") sgt(s,g,status,j,es);
    else if(o=="BYTE") byte(s,g,status,j,es); else if(o=="SHL") shl(s,g,status,j,es);
    else if(o=="SHR") shr(s,g,status,j,es); else if(o=="SAR") sar(s,g,status,j,es);
    else {{ printf("?\\n"); continue; }}
    wr(st[resIdx]);
  }}
}}
'''
open(W+'/aot/harness.cpp','w').write(src)
