export interface KnowledgeGraphNode {
  id: string
  name: string
  category: 'subject' | 'article' | 'keyword' | 'group' | 'capability'
  value: number
  meta?: string
}

export interface KnowledgeGraphLink {
  source: string
  target: string
  label?: string
}
