// Fails fast with a clear message when Node is too old for Vite 8 (needs >= 20.19).
const [major, minor] = process.versions.node.split('.').map(Number)
if (major < 20 || (major === 20 && minor < 19)) {
  console.error(
    `\nNode ${process.versions.node} is too old for this project (needs Node 20.19+ or 22.12+).\n` +
    `Your terminal is using: ${process.execPath}\n` +
    'If Node 24 is installed in ~/.local/node, open a new terminal or run: source ~/.bashrc\n'
  )
  process.exit(1)
}
