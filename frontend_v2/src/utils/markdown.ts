function escapeHtml(value: string) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function sanitizeUrl(url: string) {
  const trimmed = url.trim()

  if (/^https?:\/\//i.test(trimmed)) {
    return trimmed
  }

  return '#'
}

function formatInline(value: string) {
  const codeSegments: string[] = []
  let escaped = escapeHtml(value)

  escaped = escaped.replace(/`([^`]+)`/g, (_match: string, code: string) => {
    const token = `__CODE_TOKEN_${codeSegments.length}__`
    codeSegments.push(`<code>${escapeHtml(code)}</code>`)
    return token
  })

  escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_match: string, label: string, url: string) => {
    const safeUrl = sanitizeUrl(url)
    return `<a href="${safeUrl}" target="_blank" rel="noreferrer">${label}</a>`
  })

  escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  escaped = escaped.replace(/(^|[\s(])\*([^*]+)\*(?=[\s).,!?]|$)/g, '$1<em>$2</em>')
  escaped = escaped.replace(/~~([^~]+)~~/g, '<del>$1</del>')

  return codeSegments.reduce(
    (result, snippet, index) => result.replace(`__CODE_TOKEN_${index}__`, snippet),
    escaped,
  )
}

function closeList(html: string[], listType: 'ul' | 'ol' | null) {
  if (listType) {
    html.push(`</${listType}>`)
  }
}

function closeBlockquote(html: string[], active: boolean) {
  if (active) {
    html.push('</blockquote>')
  }
}

function flushParagraph(html: string[], lines: string[]) {
  if (!lines.length) {
    return
  }

  html.push(`<p>${lines.map((line) => formatInline(line)).join('<br />')}</p>`)
  lines.length = 0
}

export function renderMarkdownToHtml(markdown: string | null | undefined) {
  if (!markdown) {
    return '<p>暂无正文。</p>'
  }

  const lines = markdown.replace(/\r\n/g, '\n').split('\n')
  const html: string[] = []
  const paragraphLines: string[] = []
  const codeLines: string[] = []

  let listType: 'ul' | 'ol' | null = null
  let inBlockquote = false
  let inCodeBlock = false
  let codeLanguage = ''

  for (const line of lines) {
    const trimmed = line.trim()

    if (inCodeBlock) {
      if (trimmed.startsWith('```')) {
        html.push(
          `<pre><code class="language-${escapeHtml(codeLanguage)}">${escapeHtml(
            codeLines.join('\n'),
          )}</code></pre>`,
        )
        codeLines.length = 0
        inCodeBlock = false
        codeLanguage = ''
      } else {
        codeLines.push(line)
      }
      continue
    }

    if (trimmed.startsWith('```')) {
      flushParagraph(html, paragraphLines)
      closeList(html, listType)
      closeBlockquote(html, inBlockquote)
      listType = null
      inBlockquote = false
      inCodeBlock = true
      codeLanguage = trimmed.slice(3).trim()
      continue
    }

    if (!trimmed) {
      flushParagraph(html, paragraphLines)
      closeList(html, listType)
      closeBlockquote(html, inBlockquote)
      listType = null
      inBlockquote = false
      continue
    }

    const headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/)
    if (headingMatch) {
      flushParagraph(html, paragraphLines)
      closeList(html, listType)
      closeBlockquote(html, inBlockquote)
      listType = null
      inBlockquote = false
      const level = (headingMatch[1] ?? '#').length
      const headingText = headingMatch[2] ?? ''
      html.push(`<h${level}>${formatInline(headingText)}</h${level}>`)
      continue
    }

    if (/^(-{3,}|\*{3,}|_{3,})$/.test(trimmed)) {
      flushParagraph(html, paragraphLines)
      closeList(html, listType)
      closeBlockquote(html, inBlockquote)
      listType = null
      inBlockquote = false
      html.push('<hr />')
      continue
    }

    const blockquoteMatch = trimmed.match(/^>\s?(.*)$/)
    if (blockquoteMatch) {
      flushParagraph(html, paragraphLines)
      closeList(html, listType)
      listType = null
      if (!inBlockquote) {
        html.push('<blockquote>')
        inBlockquote = true
      }
      const blockquoteText = blockquoteMatch[1] ?? ''
      html.push(`<p>${formatInline(blockquoteText)}</p>`)
      continue
    }

    if (inBlockquote) {
      closeBlockquote(html, true)
      inBlockquote = false
    }

    const unorderedMatch = trimmed.match(/^[-*+]\s+(.*)$/)
    if (unorderedMatch) {
      flushParagraph(html, paragraphLines)
      if (listType !== 'ul') {
        closeList(html, listType)
        html.push('<ul>')
        listType = 'ul'
      }
      const unorderedText = unorderedMatch[1] ?? ''
      html.push(`<li>${formatInline(unorderedText)}</li>`)
      continue
    }

    const orderedMatch = trimmed.match(/^\d+\.\s+(.*)$/)
    if (orderedMatch) {
      flushParagraph(html, paragraphLines)
      if (listType !== 'ol') {
        closeList(html, listType)
        html.push('<ol>')
        listType = 'ol'
      }
      const orderedText = orderedMatch[1] ?? ''
      html.push(`<li>${formatInline(orderedText)}</li>`)
      continue
    }

    closeList(html, listType)
    listType = null
    paragraphLines.push(line)
  }

  flushParagraph(html, paragraphLines)
  closeList(html, listType)
  closeBlockquote(html, inBlockquote)

  if (inCodeBlock) {
    html.push(
      `<pre><code class="language-${escapeHtml(codeLanguage)}">${escapeHtml(
        codeLines.join('\n'),
      )}</code></pre>`,
    )
  }

  return html.join('\n')
}
