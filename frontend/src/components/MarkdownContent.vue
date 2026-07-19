<template>
  <div class="markdown-content" v-html="html" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const props = defineProps<{ content?: string }>()

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: true
})

const defaultRender = markdown.renderer.rules.link_open || function(tokens, idx, options, _env, self) {
  return self.renderToken(tokens, idx, options)
}

markdown.renderer.rules.link_open = function(tokens, idx, options, _env, self) {
  const hrefIndex = tokens[idx].attrIndex('href')
  if (hrefIndex >= 0 && tokens[idx].attrs) {
    const href = tokens[idx].attrs[hrefIndex][1]
    if (href && (href.startsWith('http://') || href.startsWith('https://'))) {
      tokens[idx].attrPush(['target', '_blank'])
      tokens[idx].attrPush(['rel', 'noopener noreferrer'])
      tokens[idx].attrPush(['class', 'external-link'])
    }
  }
  return defaultRender(tokens, idx, options, _env, self)
}

const html = computed(() => DOMPurify.sanitize(markdown.render(props.content || '')))
</script>

<style scoped>
.markdown-content { color: #334155; font-size: 14px; line-height: 1.8; word-break: break-word; }
.markdown-content :deep(h1), .markdown-content :deep(h2), .markdown-content :deep(h3) {
  color: #0f172a; line-height: 1.4; margin: 18px 0 10px;
}
.markdown-content :deep(h1) { font-size: 22px; }
.markdown-content :deep(h2) { font-size: 19px; }
.markdown-content :deep(h3) { font-size: 16px; }
.markdown-content :deep(p) { margin: 8px 0; }
.markdown-content :deep(ul), .markdown-content :deep(ol) { margin: 8px 0; padding-left: 24px; }
.markdown-content :deep(li) { margin: 4px 0; }
.markdown-content :deep(blockquote) {
  margin: 12px 0; padding: 8px 14px; border-left: 4px solid #14b8a6;
  background: #f0fdfa; color: #475569;
}
.markdown-content :deep(code) { padding: 2px 5px; border-radius: 4px; background: #f1f5f9; color: #be123c; }
.markdown-content :deep(pre) { overflow-x: auto; padding: 12px; border-radius: 8px; background: #0f172a; }
.markdown-content :deep(pre code) { padding: 0; background: transparent; color: #e2e8f0; }
.markdown-content :deep(a) { color: #0d9488; text-decoration: none; }
.markdown-content :deep(a):hover { text-decoration: underline; }
.markdown-content :deep(a.external-link) { color: #3b82f6; font-weight: 500; }
.markdown-content :deep(a.external-link)::after { content: ' ↗'; font-size: 12px; }
.markdown-content :deep(strong) { color: #0f766e; }
</style>
