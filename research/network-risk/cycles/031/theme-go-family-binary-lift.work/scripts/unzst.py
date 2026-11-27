"""Decompress a .deb data.tar.zst member with the backports.zstd module already present in the poetry tool venv,
then list and extract the tar with Python's tarfile (data filter). Reads data only."""
import sys, io, tarfile
sys.path.append('/root/.local/share/uv/tools/poetry/lib/python3.13/site-packages')
from backports import zstd
src, dst = sys.argv[1], sys.argv[2]
raw = zstd.decompress(open(src, 'rb').read())
t = tarfile.open(fileobj=io.BytesIO(raw))
t.extractall(dst, filter='data')
for m in t.getmembers():
    if m.isfile() and m.size > 1 << 20: print(m.name, m.size)
