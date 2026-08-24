import Link from "next/link";
import type { ReactNode } from "react";

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link href="/" className="brand">
        WhichPlaceGusto
      </Link>
      <nav>
        <Link href="/spain/malaga">Explore</Link>
        <Link href="/compare/malaga-vs-alicante">Compare</Link>
      </nav>
    </header>
  );
}

export function SiteShell({ children }: { children: ReactNode }) {
  return (
    <div className="shell">
      <SiteHeader />
      <main>{children}</main>
      <footer className="site-footer">
        <p>
          MVP uses provisional seed metrics until official SERPAVI / INE / AEMET
          pipelines replace them. Every number carries a quality flag.
        </p>
      </footer>
    </div>
  );
}
