# The Road Is Life

In 2005, my friend Ryan set off to circumnavigate the globe without taking a
plane. He kept us up to date on theroadislife.com, a travel blog before that
was really a thing. I thought it was the coolest thing in the world and was
intensely jealous while I was back at school.

Then came kids, jobs, life. The site was overrun by comment spam, fell into
disrepair, and fell off the internet.

This is a bit of internet archaeology: recover the original blog, turn it into
Markdown, and keep it online as a static site that feels like it did 20 years
ago.

All 186 posts listed in the archive index are available as Markdown. Thirteen
were recovered from monthly or category archives because their individual pages
were missing or incomplete. Flickr photos remain linked externally, and comments
haven't been collected separately. The original [Internet Archive capture](https://web.archive.org/web/20100406044023/http://theroadislife.com/)
identifies the publishing platform as Movable Type.

The site is live at <https://clutchski.github.io/theroadislife/>. Raw captures,
recovery tools, Markdown, and photos are in `extraction/`; the Hugo site is in
`blog/`. See [`TODO.md`](TODO.md) for remaining work.

## Run it locally

Install the pinned Hugo version and start a preview:

```sh
mise install
mise run blog:serve
```

Build with `mise run blog:build`. GitHub Actions publishes changes to GitHub
Pages when they reach `main`.
