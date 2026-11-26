// Streaming zstd decompression with node's built-in zlib. Reads input path, writes output path.
// Used only to read package members as data; nothing from the package is executed.
const fs = require('fs');
const zlib = require('zlib');
const [, , inp, out] = process.argv;
fs.createReadStream(inp)
  .pipe(zlib.createZstdDecompress())
  .pipe(fs.createWriteStream(out))
  .on('finish', () => console.log('ok', out, fs.statSync(out).size));
