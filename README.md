# The Road Is Life

This is an archival archaeology project to restore a friend's twenty-year-old
travelogue and turn it into a readable static site. The journal follows Ryan
Henderson's attempt to travel around the world without flying, from 2005 to 2007.

The original site was recovered from [the Internet Archive's April 2010 capture](https://web.archive.org/web/20100406044023/http://theroadislife.com/).
The archived pages identify the publishing platform as Movable Type. This project
preserves the recovered HTML and turns available posts and supporting pages into
Markdown, with their publication metadata, links, and photos retained where possible.

The static edition is built with Hugo. It reads the extracted Markdown and images
directly, while the raw archive remains available for research and future recovery.
The recovery is incomplete: 173 of 186 indexed posts have been extracted so far.
See [`TODO.md`](TODO.md) and the reports in `extraction/` for known gaps.

The published site is available at <https://clutchski.github.io/theroadislife/>.

## Repository layout

- [`extraction/`](extraction/README.md) contains the recovery tools, raw Wayback
  captures, extracted Markdown, photos, and coverage reports.
- [`blog/`](blog/README.md) contains the Hugo templates, styles, and site
  configuration. The source content remains in `extraction/`.
- [`TODO.md`](TODO.md) tracks recovery gaps and site work.

## Preview and build

Install the pinned Hugo version with mise, then start a local preview:

```sh
mise install
mise run blog:serve
```

Build the publishable site with `mise run blog:build`. GitHub Actions builds and
deploys the site to GitHub Pages when changes reach `main`.
