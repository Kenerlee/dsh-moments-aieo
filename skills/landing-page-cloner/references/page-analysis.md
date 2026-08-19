# Page Analysis Reference

Detailed guide for analyzing landing pages to achieve 100% fidelity cloning.

## Color Extraction Techniques

### From CSS
Look for these patterns in stylesheets:
```css
/* Common color declarations */
--primary-color: #XXXXXX;
--brand-color: #XXXXXX;
background-color: rgb(X, X, X);
color: hsl(X, X%, X%);
```

### From Computed Styles
Use browser DevTools:
1. Right-click element → Inspect
2. Check "Computed" tab
3. Find `color`, `background-color`, `border-color`
4. Note exact values

### Color Conversion
```python
# RGB to HEX
def rgb_to_hex(r, g, b):
    return f'#{r:02x}{g:02x}{b:02x}'

# HSL to RGB
import colorsys
def hsl_to_rgb(h, s, l):
    r, g, b = colorsys.hls_to_rgb(h/360, l/100, s/100)
    return int(r*255), int(g*255), int(b*255)
```

## Typography Analysis

### Font Detection Steps
1. Inspect text element in DevTools
2. Check `font-family` in Computed styles
3. Look for `@font-face` declarations in CSS
4. Check Network tab for font file requests (.woff2, .woff, .ttf)
5. Identify Google Fonts link in `<head>`

### Common Font Sources
- Google Fonts: `fonts.googleapis.com`
- Adobe Fonts: `use.typekit.net`
- Custom fonts: Usually in `/fonts/` or `/assets/fonts/`

### Font Metrics to Capture
```
Font Family: [name]
Font Weight: [100-900]
Font Size: [px/rem/em]
Line Height: [unitless or px]
Letter Spacing: [px/em]
Text Transform: [uppercase/lowercase/capitalize/none]
```

## Layout Analysis

### Grid Detection
```css
/* Look for these patterns */
display: grid;
grid-template-columns: repeat(12, 1fr);
display: flex;
max-width: 1200px; /* Container width */
```

### Breakpoint Detection
Common patterns in media queries:
```css
/* Mobile */
@media (max-width: 480px) {}
@media (max-width: 576px) {}

/* Tablet */
@media (max-width: 768px) {}
@media (max-width: 992px) {}

/* Desktop */
@media (max-width: 1200px) {}
@media (max-width: 1440px) {}
```

### Section Measurement
For each section, note:
- `height` or `min-height`
- `padding-top` and `padding-bottom`
- `margin-top` and `margin-bottom`
- Background treatment

## Animation Analysis

### CSS Animations
```css
/* Look for */
animation: name duration timing-function delay iteration-count;
transition: property duration timing-function;
transform: translateX() rotate() scale();
```

### JavaScript Animations
Check for libraries:
- GSAP (greensock)
- AOS (Animate On Scroll)
- Framer Motion
- Lottie
- Three.js

### Scroll Effects
- Parallax scrolling
- Fade-in on scroll
- Sticky headers
- Progress indicators

## Interactive Elements

### Forms
```
Input Styles:
- Border radius
- Border color (normal/focus/error)
- Background color
- Placeholder style
- Label positioning

Button Styles:
- Background color
- Hover state
- Active state
- Border radius
- Shadow
- Transition effect
```

### Navigation
```
Nav Type: [sticky/fixed/static]
Mobile Menu: [hamburger/sidebar/dropdown]
Hover Effects: [underline/background/color change]
Active State: [indicator style]
Transition: [duration and easing]
```

## Image Analysis

### Image Types
- Hero backgrounds (large, often parallax)
- Product images (precise dimensions)
- Icons (SVG preferred)
- Decorative elements (shapes, patterns)

### Image Optimization Notes
```
Format: [jpg/png/webp/svg]
Dimensions: [width x height]
Loading: [lazy/eager]
Srcset: [responsive sizes]
```

## CSS Framework Detection

### Bootstrap
```html
<link href="bootstrap.min.css">
<!-- Class patterns: col-md-6, btn-primary, container -->
```

### Tailwind
```html
<!-- Class patterns: flex, items-center, bg-blue-500 -->
```

### Custom CSS
Look for:
- BEM naming (.block__element--modifier)
- Custom properties (--custom-variable)
- Unique class naming patterns
