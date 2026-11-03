# Hugo site

This Hugo site builds from the Markdown and photos in the sibling `extraction/`
directory. The Hugo config mounts `extraction/content/` and `extraction/photos/`
directly, so the extracted copy remains the single source of truth. Raw captures
stay in `extraction/raw/` and are never part of the published output.

From the repository root, install the pinned Hugo version and preview the site:

```sh
mise install
mise run blog:serve
```

Build the publishable site with `mise run blog:build`. The output is written to
`blog/public/`. GitHub Actions runs the same pinned Hugo version and deploys to
GitHub Pages when changes reach `main`.
