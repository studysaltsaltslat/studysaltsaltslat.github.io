# studysalt's blog

Personal blog built with [Astro](https://astro.build/) and the
[Astro Theme Pure](https://astro-pure.js.org/) theme.

## Commands

| Command         | Action                                            |
| :-------------- | :------------------------------------------------ |
| `npm install`   | Installs dependencies                             |
| `npm run dev`   | Starts local dev server at `localhost:4321`       |
| `npm run build` | Checks the theme config and builds the site       |
| `npm run check` | Runs `astro check` for type errors                |
| `npm run preview` | Preview the production build locally            |

## Customization

- Site information (title, author, menu, social links): `src/site.config.ts`
- Blog posts: `src/content/blog/`
- Homepage & about page: `src/pages/index.astro`, `src/pages/about/index.astro`
- Deployment: GitHub Pages via `.github/workflows/astro.yml`

See the [theme documentation](https://astro-pure.js.org/docs/) for details.
