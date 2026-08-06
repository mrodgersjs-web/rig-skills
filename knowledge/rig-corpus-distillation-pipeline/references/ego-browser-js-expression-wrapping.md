# Ego-Browser JS Expression Wrapping — the silent killer

A single pitfall that bit us in stage 2 of the agentic-coding-school
distillation run. Cost ~30 minutes of debugging. Captured here so no
future ego-browser scraper hits it.

## The setup

ego-browser exposes a `js()` helper that runs JavaScript in the connected
browser context. The helper is documented in the `ego-browser` skill:

> `js()` is essentially `Runtime.evaluate` and takes a string. ... If the
> source contains a top-level `return`, it will be auto-wrapped in an IIFE.
> When the source is wrapped in another IIFE, the JS evaluates to `null`.
> The symptom is empty results.

But the real failure mode is more subtle than the docs imply.

## The trap

If you write:

```js
(() => {
  const url = location.href
  const videoId = (url.match(/[?&]videoId=([0-9a-f-]+)/) || [])[1] || null
  return { url, videoId }
})()
```

…the result is `null`. Why?

The ego-browser `js()` helper wraps your source in `(function(){...})()`.
Your source contains a top-level `return` (line 4). So the wrapper sees
something like:

```js
(function(){(() => {
  const url = location.href
  const videoId = (url.match(/[?&]videoId=([0-9a-f-]+)/) || [])[1] || null
  return { url, videoId }
})()})
```

The outer function calls the inner IIFE for its result, but the inner
IIFE returns `{ url, videoId }` — that's the IIFE's value, not the
outer function's value. The outer function returns `undefined`. Then
ego-browser evaluates that as the result.

**Symptom:** `r` is `null`, `typeof r === 'object'` (because `null` is
`typeof 'object'`), `Object.keys(r)` is `null` (because `null` has no
own keys).

## The deeper trap

If you write:

```js
(() => {
  const url = location.href
  const videoId = (url.match(/[?&]videoId=([0-9a-f-]+)/) || [])[1] || null
  const cleanBody = stripDMCA(document.body.textContent || '')
  const h = (() => { ... })()
  const chapters = (panel => { ... })([...])
  return { url, videoId, cleanBody, chapters }
})()
```

…ego-browser's `js()` helper STILL auto-wraps this, AND the `const` at
the top triggers TDZ errors relative to the trailing object expression
once the auto-wrap adds the outer function. You get a SyntaxError or
silent failure.

## The fix: single-object-expression form

The correct form is a single object expression with no `return`, no
top-level `const`, no helpers-as-IIFEs. Every value is an inline
expression inside the object literal:

```js
({
  pageTitle: document.title,
  pageUrl: location.href,
  videoId: (location.href.match(/[?&]videoId=([0-9a-f-]+)/) || [])[1] || null,
  description: ([...document.querySelectorAll('p')]
    .map(el => (el.textContent || '').replace(/DMCA/gi, ''))
    .filter(t => t.length > 60)[0] || ''),
  chapterCount: document.querySelectorAll('div[class*="max-h-"][class*="overflow-y-auto"] li').length,
  downloads: [...document.querySelectorAll('a[href]')].filter(...).map(...),
  externalLinks: [...document.querySelectorAll('a[href]')].filter(...).map(...),
  htmlSize: document.documentElement.outerHTML.length,
  scrapedAt: new Date().toISOString()
})
```

This works because:
- No top-level `return` → ego-browser doesn't wrap it in an IIFE
- No top-level `const` → no TDZ issue
- Helpers like `[...document.querySelectorAll(...)]` are inline expressions,
  not top-level IIFEs
- The trailing object expression is the value of the expression statement

## The diagnostic checklist

When `js()` returns `null` or an empty result:

1. **Check for `return`**: search your source for `return`. If found,
   remove it; the trailing object expression is the return value.
2. **Check for top-level `const` or `let`**: search for `^const|^let|^var`.
   If found, inline those into the object expression.
3. **Check for nested IIFEs**: `(() => { ... })()` as a top-level
   statement. If found, inline the inner expression into the outer
   object.
4. **Test incrementally**: run the smallest possible object expression
   first (`({ url: location.href })`). If that returns `null`, the
   problem is elsewhere; if it returns the object, grow the expression
   one field at a time.

## The fallback: explicit `return` works

If you need `const` declarations (for readability), the docs say
top-level `return` triggers the auto-wrap. **Test it.** In the
agentic-coding-school run, the explicit-return IIFE form worked in
some cases:

```js
(() => {
  const url = location.href
  const videoId = (url.match(/[?&]videoId=([0-9a-f-]+)/) || [])[1] || null
  return { url, videoId }
})()
```

…returned `null` in the smoke test but later worked. The variance is
likely due to the JS context state + run mode. Don't rely on it.

## The safer fix: use `js()` to evaluate a single expression

If you can't avoid `const` declarations, do the work in Node (the
heredoc body) and pass only the result back via `js()`:

```js
// In the heredoc body:
const pageData = await page.evaluate(() => {
  const url = location.href
  const videoId = (url.match(/[?&]videoId=([0-9a-f-]+)/) || [])[1] || null
  // ... lots of work ...
  return { url, videoId, ... }
})
cliLog('RESULT: ' + JSON.stringify(pageData))
```

`page.evaluate()` is the standard Puppeteer/Playwright API and doesn't
have the ego-browser auto-wrap quirk. Use it for any non-trivial
browser-side work.

## When this bites

The failure mode is silent: `js()` returns `null`, your Python wrapper
gets `null`, you log it as "no result" and the scrape fails. Without
the specific symptom (`r` is `null` AND `Object.keys(r)` is `null`),
it's hard to distinguish from "the page is empty" or "the selector
matched nothing".

The fix is to always inspect the raw `r` value when a scrape fails
silently, and check for the null-vs-empty pattern. If `r` is `null`,
the JS source is the suspect — not the page.

## Source

This pitfall emerged from the 2026-07-29 agentic-coding-school
distillation run (`acs-20260729T183655Z`), stage 2 (per-source body
extraction). The first probe script with the explicit-return IIFE form
returned `null` on every invocation. The fix was to inline everything
into a single object expression with no `return`, no `const`, no IIFEs.
The same fix applied to all subsequent scrapes in the run.