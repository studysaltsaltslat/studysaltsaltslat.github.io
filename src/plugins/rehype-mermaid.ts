import type { Element, Root } from 'hast'

/** Turn Mermaid fenced code blocks into elements Mermaid can render in-browser. */
export default function rehypeMermaid() {
  return (tree: Root) => {
    const visit = (node: Root | Element) => {
      if (!Array.isArray(node.children)) return
      for (let index = 0; index < node.children.length; index += 1) {
        const child = node.children[index]
        if (child.type === 'element' && child.tagName === 'pre') {
          const code = child.children[0]
          if (code?.type === 'element' && code.tagName === 'code') {
            const classes = code.properties?.className
            if (Array.isArray(classes) && classes.includes('language-mermaid')) {
              const text = code.children
                .filter((item) => item.type === 'text')
                .map((item) => item.value)
                .join('')
              node.children[index] = {
                type: 'element',
                tagName: 'div',
                properties: { className: ['mermaid'] },
                children: [{ type: 'text', value: text }]
              }
              continue
            }
          }
        }
        if (child.type === 'element') visit(child)
      }
    }
    visit(tree)
  }
}
