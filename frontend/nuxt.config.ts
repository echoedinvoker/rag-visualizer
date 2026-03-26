// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },

  modules: ['@nuxtjs/i18n'],

  i18n: {
    locales: [
      { code: 'zh-TW', name: '繁中', file: 'zh-TW.json' },
      { code: 'en', name: 'English', file: 'en.json' },
    ],
    defaultLocale: 'en',
    lazy: true,
    langDir: '../i18n/locales',
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: 'i18n_lang',
      fallbackLocale: 'en',
    },
  },

  app: {
    head: {
      title: 'RAG Pipeline Studio',
      link: [
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&family=Noto+Sans+TC:wght@400;500;700&display=swap',
        },
      ],
    },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'https://rag-visualizer-api.fly.dev',
    },
  },

  ssr: false,

  css: ['~/assets/css/main.css'],
})
