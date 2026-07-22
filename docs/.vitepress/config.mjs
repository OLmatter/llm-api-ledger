import { defineConfig } from 'vitepress'

// GitHub Pages 部署在 https://ollmatter.github.io/llm-api-ledger/
// 本地开发用 '/'，生产用 '/llm-api-ledger/'
const base = process.env.NODE_ENV === 'production' ? '/llm-api-ledger/' : '/'

export default defineConfig({
  title: 'LLM API Ledger',
  description: 'LLM API 领域的可信数据账本 — 集齐主流厂商的真实用量与性能',
  lang: 'zh-CN',
  lastUpdated: true,
  cleanUrls: true,
  base,

  head: [
    ['meta', { name: 'theme-color', content: '#0071e3' }],
  ],

  themeConfig: {
    siteTitle: 'LLM API Ledger',
    logo: '/logo.svg',

    nav: [
      { text: '榜单', link: '/' },
      { text: '厂商', link: '/vendors' },
      { text: '工具', link: '/probe' },
      { text: '关于', link: '/about' },
    ],

    sidebar: {
      '/': [
        {
          text: '榜单',
          items: [{ text: '全部套餐', link: '/' }],
        },
        {
          text: '工具',
          items: [
            { text: '本地探针', link: '/probe' },
            { text: '导出 PR 包', link: '/probe-export' },
          ],
        },
        {
          text: '项目',
          items: [
            { text: '关于', link: '/about' },
            { text: '贡献指南', link: '/contributing' },
            { text: '数据口径', link: '/methodology' },
          ],
        },
      ],
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/OLmatter/llm-api-ledger' },
    ],

    footer: {
      message: 'GPL-3.0 · 数据 CC BY 4.0 · 文档 CC BY-SA 4.0',
      copyright: '© 2026 OLmatter / llm-api-ledger contributors',
    },

    search: { provider: 'local' },

    outline: { level: [2, 3] },
  },
})
