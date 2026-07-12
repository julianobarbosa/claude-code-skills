# Jekyll Configuration Reference

Complete reference for configuring Jekyll on GitHub Pages.

---

## _config.yml

The primary configuration file for Jekyll sites.

### Minimal Configuration

```yaml
theme: jekyll-theme-minimal
title: My Site
description: A brief description of my site
```

### Full Configuration

```yaml
# =============================================================================
# Site Settings
# =============================================================================

title: My Site
description: >-
  A longer description that can span
  multiple lines for SEO purposes.
url: https://username.github.io
baseurl: ""  # Use "/repo-name" for project sites

# =============================================================================
# Theme
# =============================================================================

# Supported themes (no additional setup needed)
theme: jekyll-theme-minimal

# Or use a remote theme from GitHub
# remote_theme: pages-themes/minimal@v0.2.0

# =============================================================================
# Author
# =============================================================================

author:
  name: Your Name
  email: you@example.com
  twitter: yourhandle
  github: yourusername

# =============================================================================
# Build Settings
# =============================================================================

markdown: kramdown
highlighter: rouge
permalink: pretty  # or /:year/:month/:day/:title/

# Timezone for date/time
timezone: America/New_York

# =============================================================================
# Plugins
# =============================================================================

plugins:
  - jekyll-feed
  - jekyll-seo-tag
  - jekyll-sitemap
  - jekyll-paginate
  - jekyll-relative-links

# =============================================================================
# Collections (optional)
# =============================================================================

collections:
  projects:
    output: true
    permalink: /projects/:name/
  docs:
    output: true
    permalink: /docs/:path/

# =============================================================================
# Defaults
# =============================================================================

defaults:
  - scope:
      path: ""
      type: "posts"
    values:
      layout: "post"
      author: "Your Name"
  - scope:
      path: ""
      type: "pages"
    values:
      layout: "default"

# =============================================================================
# Pagination (requires jekyll-paginate)
# =============================================================================

paginate: 10
paginate_path: /blog/page:num/

# =============================================================================
# Exclude/Include
# =============================================================================

exclude:
  - Gemfile
  - Gemfile.lock
  - node_modules
  - vendor
  - README.md
  - CHANGELOG.md
  - LICENSE

include:
  - _pages
  - .htaccess

# =============================================================================
# Kramdown Configuration
# =============================================================================

kramdown:
  input: GFM
  hard_wrap: false
  syntax_highlighter: rouge
  syntax_highlighter_opts:
    block:
      line_numbers: true

# =============================================================================
# Sass Configuration
# =============================================================================

sass:
  style: compressed
  sass_dir: _sass
```

---

## GitHub Pages Auto-Configuration

GitHub Pages automatically sets these values (cannot be overridden):

```yaml
lsi: false
safe: true
source: [repository root]
incremental: false
highlighter: rouge
gist:
  noscript: false
kramdown:
  math_engine: mathjax
  syntax_highlighter: rouge
```

---

## Supported Plugins

### Auto-Enabled by GitHub Pages

| Plugin | Description |
|--------|-------------|
| jekyll-coffeescript | CoffeeScript converter |
| jekyll-default-layout | Set default layouts |
| jekyll-gist | Gist embedding |
| jekyll-github-metadata | Repository metadata |
| jekyll-optional-front-matter | Front matter optional for some files |
| jekyll-paginate | Pagination |
| jekyll-readme-index | Use README as index |
| jekyll-titles-from-headings | Auto-generate titles |
| jekyll-relative-links | Convert relative links |

### Optional Supported Plugins

Enable in `_config.yml`:

```yaml
plugins:
  - jekyll-feed          # RSS/Atom feed
  - jekyll-seo-tag       # SEO meta tags
  - jekyll-sitemap       # XML sitemap
  - jekyll-avatar        # GitHub avatar helper
  - jekyll-mentions      # @mention links
  - jekyll-redirect-from # Redirect pages
  - jemoji               # Emoji support
```

**Note:** Unsupported plugins will cause build failures. Build locally if you need unsupported plugins.

---

## Supported Themes

### Built-in Themes

Use with `theme:` in _config.yml:

| Theme Name | Config Value |
|------------|--------------|
| Architect | `jekyll-theme-architect` |
| Cayman | `jekyll-theme-cayman` |
| Dinky | `jekyll-theme-dinky` |
| Hacker | `jekyll-theme-hacker` |
| Leap Day | `jekyll-theme-leap-day` |
| Merlot | `jekyll-theme-merlot` |
| Midnight | `jekyll-theme-midnight` |
| Minima | `minima` |
| Minimal | `jekyll-theme-minimal` |
| Modernist | `jekyll-theme-modernist` |
| Slate | `jekyll-theme-slate` |
| Tactile | `jekyll-theme-tactile` |
| Time Machine | `jekyll-theme-time-machine` |

### Remote Themes

Use any Jekyll theme from GitHub:

```yaml
remote_theme: owner/repository
# or with version
remote_theme: owner/repository@v1.0.0
```

**Examples:**
```yaml
remote_theme: pages-themes/cayman@v0.2.0
remote_theme: mmistakes/minimal-mistakes
remote_theme: just-the-docs/just-the-docs
```

---

## Front Matter

YAML configuration at the top of content files.

### Page Front Matter

```yaml
---
layout: default
title: Page Title
description: Page description for SEO
permalink: /custom-url/
nav_order: 1
parent: Parent Page
---
```

### Post Front Matter

```yaml
---
layout: post
title: "Post Title"
date: 2024-01-15 10:00:00 -0500
categories: [category1, category2]
tags: [tag1, tag2]
author: Your Name
excerpt: "Custom excerpt for listings"
image: /assets/images/featured.jpg
published: true
---
```

### Draft Posts

Store in `_drafts/` folder without date:

```
_drafts/my-upcoming-post.md
```

Preview drafts locally:
```bash
bundle exec jekyll serve --drafts
```

---

## Directory Structure

```
.
├── _config.yml          # Site configuration
├── _data/               # Data files (YAML, JSON, CSV)
│   └── navigation.yml
├── _drafts/             # Unpublished posts
│   └── upcoming-post.md
├── _includes/           # Reusable partials
│   ├── header.html
│   └── footer.html
├── _layouts/            # Page templates
│   ├── default.html
│   └── post.html
├── _posts/              # Blog posts
│   └── 2024-01-15-hello-world.md
├── _sass/               # Sass partials
│   └── _custom.scss
├── assets/
│   ├── css/
│   │   └── style.scss
│   ├── images/
│   └── js/
├── _pages/              # Additional pages (if using collections)
├── index.md             # Homepage
└── 404.html             # Custom 404 page
```

---

## Data Files

Store structured data in `_data/` folder.

### YAML Example (_data/navigation.yml)

```yaml
- title: Home
  url: /
- title: About
  url: /about/
- title: Blog
  url: /blog/
- title: Contact
  url: /contact/
```

**Usage in templates:**

```liquid
<nav>
{% for item in site.data.navigation %}
  <a href="{{ item.url }}">{{ item.title }}</a>
{% endfor %}
</nav>
```

### JSON Example (_data/team.json)

```json
[
  {
    "name": "Alice",
    "role": "Developer",
    "avatar": "/assets/images/alice.jpg"
  },
  {
    "name": "Bob",
    "role": "Designer",
    "avatar": "/assets/images/bob.jpg"
  }
]
```

---

## Useful Variables

### Site Variables

| Variable | Description |
|----------|-------------|
| `site.title` | Site title |
| `site.description` | Site description |
| `site.url` | Site URL |
| `site.baseurl` | Base URL path |
| `site.pages` | All pages |
| `site.posts` | All posts |
| `site.data` | Data files |
| `site.time` | Current time |
| `site.github` | GitHub metadata |

### Page Variables

| Variable | Description |
|----------|-------------|
| `page.title` | Page title |
| `page.url` | Page URL |
| `page.date` | Page date |
| `page.content` | Page content |
| `page.excerpt` | Page excerpt |
| `page.categories` | Post categories |
| `page.tags` | Post tags |

### GitHub Metadata (site.github)

| Variable | Description |
|----------|-------------|
| `site.github.repository_name` | Repository name |
| `site.github.repository_url` | Repository URL |
| `site.github.project_title` | Project title |
| `site.github.owner_name` | Owner name |
| `site.github.owner_url` | Owner profile URL |

---

## Common Liquid Patterns

### Conditional Content

```liquid
{% if page.title %}
  <h1>{{ page.title }}</h1>
{% endif %}
```

### Loop Through Posts

```liquid
{% for post in site.posts limit:5 %}
  <article>
    <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
    <time>{{ post.date | date: "%B %d, %Y" }}</time>
    {{ post.excerpt }}
  </article>
{% endfor %}
```

### Filter Posts by Category

```liquid
{% assign tech_posts = site.posts | where: "categories", "tech" %}
{% for post in tech_posts %}
  ...
{% endfor %}
```

### Include Partial with Parameters

```liquid
{% include header.html title="Custom Title" %}
```

In `_includes/header.html`:
```liquid
<header>
  <h1>{{ include.title }}</h1>
</header>
```

---

## URL Helpers

```liquid
<!-- Relative URL (respects baseurl) -->
<a href="{{ '/about/' | relative_url }}">About</a>

<!-- Absolute URL -->
<a href="{{ '/about/' | absolute_url }}">About</a>

<!-- Link to post -->
{% post_url 2024-01-15-hello-world %}

<!-- Link to asset -->
{{ '/assets/images/logo.png' | relative_url }}
```

---

## Local Development

### Gemfile

```ruby
source "https://rubygems.org"

gem "github-pages", group: :jekyll_plugins

group :jekyll_plugins do
  gem "jekyll-feed"
  gem "jekyll-seo-tag"
end

# Ruby 3.0+ compatibility
gem "webrick"
```

### Commands

```bash
# Install dependencies
bundle install

# Update dependencies
bundle update

# Serve with live reload
bundle exec jekyll serve --livereload

# Build only
bundle exec jekyll build

# Serve drafts
bundle exec jekyll serve --drafts

# Verbose output
bundle exec jekyll build --verbose
```
