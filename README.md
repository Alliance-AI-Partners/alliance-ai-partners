# alliance-ai-partners

The brand foundation and the website of Alliance AI Partners. Start with `CLAUDE.md` for what lives where.

## The website

A Next.js 16 app with TypeScript and Tailwind CSS v4, built from the Figma website file and the design system in `design-system/`. It needs Node.js 20.9 or later.

```bash
npm install
npm run dev
```

Then open http://localhost:3000. Before pushing, run `npm run lint`, `npm run typecheck` and `npm run build`.

## Deploying on Vercel

The site is ready for Vercel as it is: Vercel recognises Next.js, reads the Node.js version from `package.json` (24.x) and needs no settings for a first deployment. Every page is prerendered, so it is served from Vercel's CDN.

1. Sign in at [vercel.com](https://vercel.com), choose the team (or your personal account) that should own the site, then **Add New… → Project**.
2. Import the GitHub repository `Alliance-AI-Partners/alliance-ai-partners`. If it isn't listed, choose **Configure GitHub App** and give Vercel access to it.
3. Leave the settings as Vercel detects them: Framework **Next.js**, Root Directory `./`, the default build and install commands.
4. Click **Deploy**. When the build finishes (about two minutes), open the `.vercel.app` address Vercel shows.

From then on, every push to `main` deploys to production, and every other branch or pull request gets its own preview address.

**Search engines stay out until launch.** The site still shows `[PRICE]` placeholders and the example email address, so every deployment tells search engines not to index it (`robots.txt`, a `noindex` tag and header). At launch, once the placeholders are real:

1. In the Vercel project, open **Settings → Environment Variables**.
2. Add `ALLOW_INDEXING` with the value `true`, for the **Production** environment only.
3. Redeploy production (**Deployments → … → Redeploy**). Preview deployments stay closed to search engines.

**Custom domain.** Add it under **Settings → Domains**, then add `SITE_URL` (for example `https://www.example.com`) for Production and redeploy, so canonical links and the sitemap use it. Both variables are described in `.env.example`.

**Deploying from your computer** (optional): `npx vercel` uploads only what the website needs (the allowlist in `.vercelignore`, about 50 MB), not the print masters and notes in the rest of the repository.

