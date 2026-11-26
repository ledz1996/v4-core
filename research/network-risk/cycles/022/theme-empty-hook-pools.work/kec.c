/* keccak256 of fixed-length records: reads records of N bytes (argv[1]) from stdin, writes 32-byte digests to stdout. */
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <stdlib.h>
static const uint64_t RC[24]={0x0000000000000001ULL,0x0000000000008082ULL,0x800000000000808aULL,0x8000000080008000ULL,0x000000000000808bULL,0x0000000080000001ULL,0x8000000080008081ULL,0x8000000000008009ULL,0x000000000000008aULL,0x0000000000000088ULL,0x0000000080008009ULL,0x000000008000000aULL,0x000000008000808bULL,0x800000000000008bULL,0x8000000000008089ULL,0x8000000000008003ULL,0x8000000000008002ULL,0x8000000000000080ULL,0x000000000000800aULL,0x800000008000000aULL,0x8000000080008081ULL,0x8000000000008080ULL,0x0000000080000001ULL,0x8000000080008008ULL};
static const int R[25]={0,1,62,28,27,36,44,6,55,20,3,10,43,25,39,41,45,15,21,8,18,2,61,56,14};
#define ROL(x,n) ((n)?(((x)<<(n))|((x)>>(64-(n)))):(x))
static void f(uint64_t A[25]){for(int r=0;r<24;r++){uint64_t C[5],D[5],B[25];for(int x=0;x<5;x++)C[x]=A[x]^A[x+5]^A[x+10]^A[x+15]^A[x+20];
for(int x=0;x<5;x++)D[x]=C[(x+4)%5]^ROL(C[(x+1)%5],1);for(int i=0;i<25;i++)A[i]^=D[i%5];
for(int x=0;x<5;x++)for(int y=0;y<5;y++){B[y+5*((2*x+3*y)%5)]=ROL(A[x+5*y],R[x+5*y]);}
for(int x=0;x<5;x++)for(int y=0;y<5;y++)A[x+5*y]=B[x+5*y]^((~B[(x+1)%5+5*y])&B[(x+2)%5+5*y]);A[0]^=RC[r];}}
static void k256(const uint8_t*in,size_t n,uint8_t out[32]){uint64_t A[25];memset(A,0,sizeof A);uint8_t blk[136];
while(n>=136){for(int i=0;i<17;i++){uint64_t w=0;for(int j=0;j<8;j++)w|=(uint64_t)in[8*i+j]<<(8*j);A[i]^=w;}f(A);in+=136;n-=136;}
memset(blk,0,136);memcpy(blk,in,n);blk[n]^=0x01;blk[135]^=0x80;for(int i=0;i<17;i++){uint64_t w=0;for(int j=0;j<8;j++)w|=(uint64_t)blk[8*i+j]<<(8*j);A[i]^=w;}f(A);
for(int i=0;i<4;i++)for(int j=0;j<8;j++)out[8*i+j]=(A[i]>>(8*j))&0xff;}
int main(int c,char**v){size_t N=atoi(v[1]);uint8_t*b=malloc(N);uint8_t o[32];while(fread(b,1,N,stdin)==N){k256(b,N,o);fwrite(o,1,32,stdout);}return 0;}
