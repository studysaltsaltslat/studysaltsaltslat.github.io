import type { Root } from 'mdast'
import { visit } from 'unist-util-visit'

/** Promote every Markdown heading by one level (h2 -> h1, h3 -> h2, ...). */
export default function remarkShiftHeadings() {
  return (tree: Root) => {
    visit(tree, 'heading', (node) => {
      node.depth = Math.max(1, node.depth - 1) as 1 | 2 | 3 | 4 | 5 | 6
    })
  }
}
