# JekyllSetup Workflow

Configure Jekyll for your GitHub Pages site.

## Checklist

- [ ] Choose a theme
- [ ] Create _config.yml
- [ ] Setup directory structure
- [ ] Configure front matter
- [ ] Test locally (optional)
- [ ] Deploy and verify

---

## Step 1: Choose a Theme

### Supported Themes (Zero Configuration)

| Theme | Style |
|-------|-------|
| `jekyll-theme-architect` | Blueprint/technical |
| `jekyll-theme-cayman` | Clean, modern |
| `jekyll-theme-dinky` | Playful |
| `jekyll-theme-hacker` | Terminal/hacker |
| `jekyll-theme-leap-day` | Yellow notebook |
| `jekyll-theme-merlot` | Warm, inviting |
| `jekyll-theme-midnight` | Dark, sophisticated |
| `jekyll-theme-minima` | Minimal blog |
| `jekyll-theme-minimal` | Simple, clean |
| `jekyll-theme-modernist` | Modern, sleek |
| `jekyll-theme-slate` | Gray, professional |
| `jekyll-theme-tactile` | Textured |
| `jekyll-theme-time-machine` | Retro futuristic |

### Remote Themes (Any GitHub Jekyll Theme)

Use `remote_theme` to use themes not in the supported list.

---

## Step 2: Create _config.yml

### Minimal Configuration

```yaml
theme: jekyll-theme-minimal
title: My Site
description: A description of my site
```

### Full Configuration

```yaml
# Theme
theme: jekyll-theme-minimal
# Or use remote theme:
# remote_theme: pages-themes/minimal@v0.2.0

# Site Settings
title: My Site
description: A description of my site
url: https://username.github.io
baseurl: "" # or "/repository-name" for project sites

# Author
author:
  name: Your Name
  email: your@email.com

# Build Settings
markdown: kramdown
highlighter: rouge

# Plugins (optional)
plugins:
  - jekyll-feed
  - jekyll-seo-tag
  - jekyll-sitemap

# Exclude from build
exclude:
  - README.md
  - Gemfile
  - Gemfile.lock
  - node_modules
  - vendor
```

---

## Step 3: Directory Structure

### Basic Structure

```
.
├── _config.yml          # Site configuration
├── index.md             # Homepage
├── about.md             # About page
├── _posts/              # Blog posts
│   └── 2024-01-01-welcome.md
├── assets/
│   ├── css/
│   │   └── style.scss   # Custom styles
│   └── images/
└── _layouts/            # Custom layouts (optional)
    └── default.html
```

### Blog Post Naming Convention

```
_posts/YYYY-MM-DD-title.md
```

Example: `_posts/2024-01-15-my-first-post.md`

---

## Step 4: Configure Front Matter

### Page Front Matter

```yaml
---
layout: default
title: Page Title
description: Page description for SEO
permalink: /custom-url/
---

Page content here...
```

### Blog Post Front Matter

```yaml
---
layout: post
title: "Blog Post Title"
date: 2024-01-15 10:00:00 -0500
categories: [category1, category2]
tags: [tag1, tag2]
author: Your Name
---

Post content here...
```

---

## Step 5: Customize Theme

### Custom CSS

Create `assets/css/style.scss`:

```scss
---
---

@import "{{ site.theme }}";

// Custom styles below
body {
  font-family: 'Your Font', sans-serif;
}

h1, h2, h3 {
  color: #333;
}

// Add more custom styles...
```

### Custom Layout

1. Find theme's `_layouts/default.html` in theme repository
2. Copy contents to your `_layouts/default.html`
3. Modify as needed

Example custom layout:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page.title }} | {{ site.title }}</title>
    <link rel="stylesheet" href="{{ '/assets/css/style.css' | relative_url }}">
</head>
<body>
    <header>
        <h1>{{ site.title }}</h1>
        <nav>
            <a href="{{ '/' | relative_url }}">Home</a>
            <a href="{{ '/about' | relative_url }}">About</a>
        </nav>
    </header>

    <main>
        {{ content }}
    </main>

    <footer>
        <p>&copy; {{ site.time | date: '%Y' }} {{ site.author.name }}</p>
    </footer>
</body>
</html>
```

---

## Step 6: Test Locally (Optional)

### Prerequisites

```bash
# Install Ruby (if not installed)
# macOS: brew install ruby
# Ubuntu: sudo apt install ruby-full

# Install Bundler
gem install bundler
```

### Setup

Create `Gemfile`:

```ruby
source "https://rubygems.org"

gem "github-pages", group: :jekyll_plugins

# Optional plugins
gem "jekyll-feed"
gem "jekyll-seo-tag"
```

### Run Locally

```bash
# Install dependencies
bundle install

# Ruby 3.0+ may need:
bundle add webrick

# Start local server
bundle exec jekyll serve

# Or with live reload
bundle exec jekyll serve --livereload

# Access at http://localhost:4000
```

---

## Step 7: Deploy

```bash
# Commit changes
git add .
git commit -m "Setup Jekyll site"
git push origin main
```

Wait up to 10 minutes for deployment.

---

## Common Issues

### Theme Not Applying

- Verify theme name in `_config.yml` is correct
- Clear browser cache
- Check for YAML syntax errors

### Custom CSS Not Loading

- Ensure front matter dashes `---` at top of SCSS file
- Verify @import statement matches theme name
- Check file is in correct location

### Build Errors

- Check Actions tab for error messages
- Verify YAML front matter syntax
- Ensure all plugins are supported

---

## Useful Liquid Tags

```liquid
<!-- Link to another page -->
[About]({{ '/about' | relative_url }})

<!-- Include image -->
![Alt text]({{ '/assets/images/photo.jpg' | relative_url }})

<!-- Loop through posts -->
{% for post in site.posts %}
  <h2><a href="{{ post.url }}">{{ post.title }}</a></h2>
  <p>{{ post.excerpt }}</p>
{% endfor %}

<!-- Site metadata -->
{{ site.github.repository_name }}
{{ site.github.project_title }}
```

---

## Resources

- [Jekyll Documentation](https://jekyllrb.com/docs/)
- [Liquid Template Language](https://shopify.github.io/liquid/)
- [GitHub Pages Theme Repository](https://github.com/pages-themes)
