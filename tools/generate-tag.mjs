import { promises as fs } from 'fs'
import path from 'path'

async function main() {
  const [,, rawName, rawElement] = process.argv
  if (!rawName) {
    console.error('Usage: node generate-tag.mjs <TagName> [element]')
    process.exit(2)
  }

  const tagName = rawName.replace(/[^A-Za-z0-9_]/g, '')
  const element = rawElement || 'div'

  const tagsDir = path.resolve('./src/frontend/src/components/tags')
  const targetPath = path.join(tagsDir, `${tagName}.tsx`)

  try {
    await fs.mkdir(tagsDir, { recursive: true })
  } catch (err) {
    // ignore
  }

  try {
    await fs.access(targetPath)
    console.error(`File already exists: ${targetPath}`)
    process.exit(1)
  } catch (e) {
    // file doesn't exist, continue
  }

  const content = `import React from 'react'
import type { HTMLAttributes } from 'react'

export interface ${tagName}Props extends HTMLAttributes<HTMLElement> {}

export default function ${tagName}(props: ${tagName}Props) {
  const { children, ...rest } = props
  return <${element} {...rest}>{children}</${element}>
}
`

  await fs.writeFile(targetPath, content, 'utf8')
  console.log(`Created ${targetPath}`)
}

main().catch(err => {
  console.error(err)
  process.exit(1)
})
