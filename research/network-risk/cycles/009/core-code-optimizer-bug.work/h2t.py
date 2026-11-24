import re,html,sys
t=open(sys.argv[1]).read()
m=re.search(r'<article.*?</article>',t,re.S)
s=m.group(0) if m else t
s=re.sub(r'<script.*?</script>|<style.*?</style>','',s,flags=re.S)
s=re.sub(r'<[^>]+>','',s); s=html.unescape(s); s=re.sub(r'\n\s*\n+','\n',s)
open(sys.argv[2],'w').write(s); print(sys.argv[2],len(s))
