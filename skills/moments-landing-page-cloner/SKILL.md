---
name: moments-landing-page-cloner
description: 100% clone and recreate landing pages or websites. Use when user wants to replicate, clone, copy, or recreate an existing landing page, website homepage, or web page design. Triggers on requests like "复刻落地页", "clone this website", "recreate this landing page", "copy this page design", or any URL-based page replication task. Handles full workflow from URL analysis to final deliverable with custom branding.
---

# Landing Page Cloner

Clone any landing page or website with 100% fidelity while replacing branding with user's own assets.

## Workflow Overview

```
1. URL Collection     → Get target page URL from user
2. Page Analysis      → Fetch and analyze structure, layout, colors, fonts
3. Asset Collection   → Request user's logo, contact info, product details
4. Favicon Creation   → Generate or source a matching favicon.ico
5. Hero Customization → Customize hero section with user's content
6. Full Build         → Create complete HTML/CSS/JS clone
7. Delivery           → Package and deliver final files
```

## Step 1: URL Collection

Ask user for the target landing page URL:

```
请提供您想要复刻的落地页或网站URL：
```

## Step 2: Page Analysis

Use `web_fetch` to retrieve the page, then analyze:

### Structure Analysis Checklist
- [ ] Overall layout (grid system, sections count)
- [ ] Navigation structure (fixed/sticky, items, style)
- [ ] Hero section (layout type, CTA placement, media)
- [ ] Content sections (features, testimonials, pricing, etc.)
- [ ] Footer structure (columns, links, social icons)

### Visual Analysis Checklist
- [ ] Color palette (primary, secondary, accent, backgrounds)
- [ ] Typography (heading fonts, body fonts, sizes, weights)
- [ ] Spacing patterns (margins, padding, gaps)
- [ ] Visual effects (shadows, gradients, animations)
- [ ] Media elements (images, videos, icons style)

### Technical Analysis
- [ ] Responsive breakpoints
- [ ] Animation/transition effects
- [ ] Interactive elements (forms, modals, sliders)
- [ ] External resources (CDNs, fonts, icons)

Document findings in this format:
```markdown
## Page Analysis Report

### Layout Structure
- Grid: [12-col / flexbox / custom]
- Sections: [list each section type]
- Navigation: [fixed/static, items]

### Color Palette
- Primary: #XXXXXX
- Secondary: #XXXXXX
- Accent: #XXXXXX
- Background: #XXXXXX
- Text: #XXXXXX

### Typography
- Headings: [font-family, weights]
- Body: [font-family, weight]
- Special: [any decorative fonts]

### Hero Section Details
- Type: [full-screen / split / centered]
- Background: [image/video/gradient/solid]
- CTA Style: [button style, placement]
- Media: [image/video/animation position]
```

## Step 3: Asset Collection

Request these assets from user:

### Required Assets
```
为了完美复刻落地页，请提供以下信息：

📁 **必需资产**
1. 公司/品牌 LOGO（PNG/SVG格式，透明背景最佳）

📋 **公司信息**
2. 公司/品牌名称
3. Slogan/标语（如有）

📞 **联系信息**
4. 电话号码
5. 邮箱地址
6. 公司地址
7. 社交媒体链接（微信公众号、微博等）

🎯 **Hero区域内容**（非常重要！）
8. 主标题文案
9. 副标题/描述文案
10. CTA按钮文案（如：立即咨询、免费试用）
11. Hero区域背景图片（如需替换）

📦 **产品/服务信息**
12. 产品或服务名称
13. 主要卖点（3-5个）
14. 产品图片（如有）

🎨 **品牌偏好**（可选）
15. 品牌主色调（如已确定）
16. 是否保留原页面配色
```

## Step 4: Favicon Creation

Generate or source an appropriate favicon:

### Option A: Extract from Logo
If user provides a logo:
```python
# Use PIL to resize logo to favicon dimensions
from PIL import Image
img = Image.open('logo.png')
img = img.resize((32, 32), Image.LANCZOS)
img.save('favicon.ico', format='ICO')
```

### Option B: Generate Simple Favicon
Create a distinctive favicon using the brand's primary color and first letter:
```python
from PIL import Image, ImageDraw, ImageFont

def create_favicon(letter, bg_color, text_color='white'):
    sizes = [(16,16), (32,32), (48,48)]
    images = []
    for size in sizes:
        img = Image.new('RGBA', size, bg_color)
        draw = ImageDraw.Draw(img)
        # Center the letter
        font_size = int(size[0] * 0.7)
        draw.text((size[0]//2, size[1]//2), letter.upper(), 
                  fill=text_color, anchor='mm')
        images.append(img)
    images[0].save('favicon.ico', format='ICO', sizes=sizes)
```

### Option C: Use Online Favicon Generator
Recommend user use favicon.io or realfavicongenerator.net with their logo.

## Step 5: Hero Section Customization

Hero区域是落地页最关键的部分，必须100%精准复刻结构并替换内容。

### Hero Types & Recreation

**Type A: Full-Screen Hero**
```html
<section class="hero hero--fullscreen">
  <div class="hero__background">
    <!-- 背景图/视频/渐变 -->
  </div>
  <div class="hero__content">
    <h1 class="hero__title">[用户主标题]</h1>
    <p class="hero__subtitle">[用户副标题]</p>
    <div class="hero__cta">
      <a href="#" class="btn btn--primary">[用户CTA文案]</a>
    </div>
  </div>
</section>
```

**Type B: Split Hero (Image + Text)**
```html
<section class="hero hero--split">
  <div class="hero__text">
    <h1>[用户主标题]</h1>
    <p>[用户描述]</p>
    <a href="#" class="btn">[CTA]</a>
  </div>
  <div class="hero__media">
    <img src="[用户产品图]" alt="">
  </div>
</section>
```

**Type C: Centered Hero**
```html
<section class="hero hero--centered">
  <h1>[用户主标题]</h1>
  <p>[用户副标题]</p>
  <div class="hero__buttons">
    <a href="#" class="btn btn--primary">[主CTA]</a>
    <a href="#" class="btn btn--secondary">[次CTA]</a>
  </div>
</section>
```

### Hero Checklist
- [ ] Logo placement matches original
- [ ] Navigation structure identical
- [ ] Headline hierarchy preserved
- [ ] CTA button styling exact match
- [ ] Background treatment replicated
- [ ] Spacing and alignment precise
- [ ] Animation effects preserved

## Step 6: Full Build

### File Structure
```
landing-page-clone/
├── index.html
├── favicon.ico
├── css/
│   └── style.css
├── js/
│   └── main.js
├── images/
│   ├── logo.png
│   ├── hero-bg.jpg
│   └── [other images]
└── fonts/
    └── [custom fonts if needed]
```

### HTML Template Structure
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>[公司名称] - [Slogan]</title>
  <link rel="icon" href="favicon.ico">
  <link rel="stylesheet" href="css/style.css">
  <!-- Google Fonts or local fonts -->
</head>
<body>
  <!-- Navigation -->
  <header class="header">...</header>
  
  <!-- Hero Section - CRITICAL -->
  <section class="hero">...</section>
  
  <!-- Features/Benefits -->
  <section class="features">...</section>
  
  <!-- [Other sections matching original] -->
  
  <!-- Footer -->
  <footer class="footer">
    <div class="footer__contact">
      <p>电话: [用户电话]</p>
      <p>邮箱: [用户邮箱]</p>
      <p>地址: [用户地址]</p>
    </div>
    <div class="footer__social">
      <!-- 社交媒体链接 -->
    </div>
    <div class="footer__copyright">
      © 2024 [公司名称]. All rights reserved.
    </div>
  </footer>
  
  <script src="js/main.js"></script>
</body>
</html>
```

### CSS Best Practices
```css
/* 使用CSS变量便于品牌定制 */
:root {
  /* 从原页面提取的颜色 */
  --color-primary: #EXTRACTED;
  --color-secondary: #EXTRACTED;
  --color-accent: #EXTRACTED;
  --color-bg: #EXTRACTED;
  --color-text: #EXTRACTED;
  
  /* 从原页面提取的字体 */
  --font-heading: 'ExtractedFont', sans-serif;
  --font-body: 'ExtractedFont', sans-serif;
  
  /* 从原页面提取的间距 */
  --spacing-section: XXpx;
  --spacing-element: XXpx;
}

/* 精确复刻每个section */
.hero { /* 100%匹配原页面 */ }
.features { /* 100%匹配原页面 */ }
/* ... */
```

### JavaScript for Interactions
```javascript
// 复刻原页面的所有交互效果
// - 导航滚动效果
// - 动画触发
// - 表单验证
// - 模态框
// - 轮播/滑块
```

## Step 7: Delivery

### Final Checklist
- [ ] All sections match original layout
- [ ] Colors exactly replicated
- [ ] Typography matches (fonts, sizes, weights)
- [ ] Spacing and alignment precise
- [ ] Responsive behavior preserved
- [ ] Animations/transitions working
- [ ] User's logo properly integrated
- [ ] Contact info correctly placed
- [ ] Hero section customized with user content
- [ ] Favicon generated and linked
- [ ] All links functional
- [ ] Images optimized

### Deliverables
1. Complete HTML file(s)
2. CSS stylesheet(s)
3. JavaScript file(s)
4. All images and assets
5. favicon.ico
6. Brief usage instructions

Output files to `/mnt/user-data/outputs/` and present to user.

## Quality Standards

### 100% Fidelity Requirements
- Pixel-perfect section heights and widths
- Exact color values (use browser dev tools to extract)
- Identical font stacks and fallbacks
- Matching hover states and transitions
- Same responsive breakpoints
- Equivalent animation timing and easing

### Common Pitfalls to Avoid
- Don't approximate colors - extract exact hex values
- Don't use similar fonts - identify and use exact fonts
- Don't simplify animations - replicate full effect
- Don't skip small details - borders, shadows, gradients matter
- Don't forget mobile views - test all breakpoints
