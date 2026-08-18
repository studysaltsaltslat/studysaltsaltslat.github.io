import type { Root, Element, Text, Parent } from 'hast'

const markPattern = /==([^=\n]+)==/g

function isParent(node: Root | Parent | Element): node is Parent {
  return Array.isArray(node.children)
}

function visit(parent: Root | Parent | Element, inCode = false) {
  if (!isParent(parent)) return

  const next: (typeof parent.children)[number][] = []
  for (const child of parent.children) {
    const element = child as Element
    const code =
      inCode ||
      (element.type === 'element' &&
        (element.tagName === 'code' || element.tagName === 'pre'))

    if (child.type === 'text' && !code) {
      let last = 0
      let match: RegExpExecArray | null
      markPattern.lastIndex = 0
      while ((match = markPattern.exec((child as Text).value))) {
        if (match.index > last) next.push({ type: 'text', value: (child as Text).value.slice(last, match.index) })
        next.push({
          type: 'element',
          tagName: 'mark',
          properties: {},
          children: [{ type: 'text', value: match[1] }]
        })
        last = match.index + match[0].length
      }
      if (last > 0) {
        if (last < (child as Text).value.length) next.push({ type: 'text', value: (child as Text).value.slice(last) })
      } else next.push(child)
    } else {
      if (child.type === 'element') visit(child, code)
      next.push(child)
    }
  }
  parent.children = next
}

export default function rehypeMark() {
  return (tree: Root) => visit(tree)
}
