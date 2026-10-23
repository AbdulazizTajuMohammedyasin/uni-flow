/** The first thing the Tab key reaches: jumps past the menus to the page itself (WCAG 2.4.1).
 * Hidden until focused. The page's <main> needs id="main" and tabIndex={-1}. */
export function SkipLink() {
  return (
    <a
      href="#main"
      className="sr-only rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground outline-none focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 focus-visible:ring-3 focus-visible:ring-ring/50"
    >
      Skip to content
    </a>
  )
}
