// Runs the cover backend (server/index.js) and the Vite dev server together.
// Usage: npm run dev:full   (Ctrl+C stops both)
import { spawn } from 'node:child_process'

const children = []

function start(name, command, args) {
  const child = spawn(command, args, { stdio: 'inherit', shell: true })
  children.push(child)
  child.on('exit', (code) => {
    console.log(`[run-both] ${name} exited with code ${code}`)
    for (const other of children) {
      if (other !== child && !other.killed) other.kill()
    }
    process.exit(code ?? 0)
  })
  return child
}

start('cover-server', 'node', ['server/index.js'])
start('vite', 'npm', ['run', 'dev'])

for (const sig of ['SIGINT', 'SIGTERM']) {
  process.on(sig, () => {
    for (const child of children) {
      if (!child.killed) child.kill()
    }
  })
}
