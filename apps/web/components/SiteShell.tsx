import Link from "next/link";
import type { ReactNode } from "react";

export function SiteHeader() {
  return (
    <header className="site-header is-solid">
      <Link href="/" className="brand">
        WhichPlaceGusto
      </Link>
      <nav>
        <Link href="/find">Find</Link>
        <Link href="/spain/malaga">Explore</Link>
        <Link href="/compare/malaga-vs-alicante">Compare</Link>
      </nav>
    </header>
  );
}

export function SiteShell({
  children,
  fullBleed = false,
}: {
  children: ReactNode;
  fullBleed?: boolean;
}) {
  return (
    <div className="site">
      <SiteHeader />
      <main className="site-main">
        {fullBleed ? children : <div className="content">{children}</div>}
      </main>
      <footer className="site-footer">
        <p>
          Official SERPAVI rents where loaded. Some property figures remain
          provisional until INE pipelines replace them. Every number carries a
          quality flag and source.
        </p>
      </footer>
    </div>
  );
}
