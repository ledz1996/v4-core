# Price and liquidity from the public DexScreener API for one token address.
import sys, json, requests
def info(addr):
    try:
        j = requests.get('https://api.dexscreener.com/latest/dex/tokens/' + addr, timeout=30).json()
    except Exception as e: return None
    ps = j.get('pairs') or []
    if not ps: return None
    ps = [p for p in ps if p.get('baseToken', {}).get('address', '').lower() == addr.lower()] or ps
    best = max(ps, key=lambda p: (p.get('liquidity') or {}).get('usd') or 0)
    return dict(sym=best['baseToken']['symbol'], name=best['baseToken']['name'], chain=best['chainId'], price=float(best.get('priceUsd') or 0), liq=(best.get('liquidity') or {}).get('usd'), dex=best.get('dexId'), labels=best.get('labels'), npairs=len(ps),
                v4=[(p['chainId'], p['dexId'], (p.get('liquidity') or {}).get('usd')) for p in ps if 'v4' in (p.get('labels') or [])][:5])
if __name__ == '__main__':
    for a in sys.argv[1:]: print(a, info(a))
