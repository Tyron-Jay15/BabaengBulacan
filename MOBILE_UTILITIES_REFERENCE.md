# Mobile-Responsive CSS Utilities Quick Reference

## Display Classes

```html
<!-- Hide/Show on specific breakpoints -->
<div class="d-none d-sm-block">Hidden on mobile, visible on larger</div>
<div class="d-sm-none">Visible on mobile, hidden on larger</div>
<div class="d-md-none">Visible on mobile/tablet, hidden on desktop</div>
<div class="d-lg-none">Visible on phone/tablet, hidden on large desktop</div>

<!-- Force specific display -->
<div class="d-block">Display as block</div>
<div class="d-flex">Display as flex</div>
<div class="d-grid">Display as grid</div>
<div class="d-inline">Display as inline</div>
<div class="d-inline-block">Display as inline-block</div>
```

## Spacing Utilities

```html
<!-- Gap between flex/grid items -->
<div class="d-flex gap-1">Small gap (0.5rem)</div>
<div class="d-flex gap-2">Medium gap (1rem)</div>
<div class="d-flex gap-3">Large gap (1.5rem)</div>

<!-- Margin utilities -->
<div class="mx-auto">Horizontal auto margin (centers)</div>
<div class="mt-auto">Margin top auto</div>
<div class="mb-auto">Margin bottom auto</div>
```

## Text Utilities

```html
<!-- Text alignment -->
<div class="text-center">Center aligned text</div>
<div class="text-start">Left aligned text</div>
<div class="text-end">Right aligned text</div>

<!-- Text size -->
<div class="text-lg">Large text</div>
<div class="text-sm">Small text</div>
```

## Size Utilities

```html
<!-- Width and Height -->
<div class="w-100">Full width (100%)</div>
<div class="h-100">Full height (100%)</div>

<!-- Overflow -->
<div class="overflow-hidden">Hidden overflow</div>
<div class="overflow-auto">Auto scroll on overflow</div>
```

---

## Responsive Button Examples

### Single Button
```html
<button class="btn btn-primary w-100">Full-width button on mobile</button>
```

### Button Group (Side by Side)
```html
<div class="d-flex gap-2">
    <button class="btn btn-primary flex-1">Save</button>
    <button class="btn btn-secondary flex-1">Cancel</button>
</div>
```

### Button Group (Stacked on Mobile)
```html
<div class="d-flex flex-column gap-2 flex-md-row">
    <button class="btn btn-primary">Save</button>
    <button class="btn btn-secondary">Cancel</button>
</div>
```

---

## Responsive Form Examples

### Basic Form
```html
<form>
    <div class="form-group">
        <label for="email">Email</label>
        <input type="email" class="form-control" id="email" required>
        <div class="invalid-feedback">Please enter a valid email.</div>
    </div>
    
    <div class="form-group">
        <label for="message">Message</label>
        <textarea class="form-control" id="message" required></textarea>
    </div>
    
    <button type="submit" class="btn btn-primary w-100">Submit</button>
</form>
```

### Form with Two Columns
```html
<form>
    <div class="row">
        <div class="col-md-6">
            <div class="form-group">
                <label for="firstName">First Name</label>
                <input type="text" class="form-control" id="firstName" required>
            </div>
        </div>
        <div class="col-md-6">
            <div class="form-group">
                <label for="lastName">Last Name</label>
                <input type="text" class="form-control" id="lastName" required>
            </div>
        </div>
    </div>
</form>
```

### Form with Checkboxes
```html
<div class="form-group">
    <div class="form-check">
        <input class="form-check-input" type="checkbox" id="agree" required>
        <label class="form-check-label" for="agree">
            I agree to the terms and conditions
        </label>
    </div>
</div>
```

---

## Responsive Card Examples

### Single Card
```html
<div class="stat-card stat-primary">
    <div class="stat-icon"><i class="fas fa-heart"></i></div>
    <div class="stat-number">150</div>
    <div class="stat-label">Reports Filed</div>
</div>
```

### Card Grid
```html
<div class="row">
    <div class="col-12 col-md-6 col-lg-3">
        <div class="stat-card stat-primary">
            <!-- Card content -->
        </div>
    </div>
    <!-- Repeat for more cards -->
</div>
```

---

## Responsive Alert Examples

### Basic Alert
```html
<div class="alert alert-success alert-dismissible fade show" role="alert">
    <i class="fas fa-check-circle me-2"></i>
    <strong>Success!</strong> Your report has been submitted.
    <button type="button" class="alert-close" data-dismiss="alert">×</button>
</div>
```

### Alert Types
```html
<!-- Success -->
<div class="alert alert-success">✅ Success message</div>

<!-- Error/Danger -->
<div class="alert alert-danger">❌ Error message</div>

<!-- Warning -->
<div class="alert alert-warning">⚠️ Warning message</div>

<!-- Info -->
<div class="alert alert-info">ℹ️ Information message</div>
```

---

## Responsive Modal Examples

### Basic Modal
```html
<button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#exampleModal">
    Open Modal
</button>

<div class="modal fade" id="exampleModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Modal Title</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                Modal content here...
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary">Save</button>
            </div>
        </div>
    </div>
</div>
```

---

## Responsive Navigation Examples

### Navbar with Brand
```html
<nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container-fluid">
        <a class="navbar-brand" href="#">
            <img src="logo.png" alt="Logo" class="navbar-logo">
            <span class="navbar-brand-text">BabaengBulacan</span>
        </a>
        
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav ms-auto">
                <li class="nav-item">
                    <a class="nav-link" href="#">Home</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="#">About</a>
                </li>
            </ul>
        </div>
    </div>
</nav>
```

---

## Responsive Layout Examples

### Hero Section
```html
<section class="hero-section">
    <div class="container">
        <h1>Welcome to BabaengBulacan</h1>
        <p>Support and empowerment for women</p>
        <button class="btn btn-quick-report">Report an Incident</button>
    </div>
</section>
```

### Two-Column Layout
```html
<div class="row">
    <div class="col-12 col-md-6">
        <h2>Column 1</h2>
        <p>Content for first column</p>
    </div>
    <div class="col-12 col-md-6">
        <h2>Column 2</h2>
        <p>Content for second column</p>
    </div>
</div>
```

### Three-Column Grid
```html
<div class="row">
    <div class="col-12 col-md-6 col-lg-4">
        <div class="card">
            <!-- Card content -->
        </div>
    </div>
    <div class="col-12 col-md-6 col-lg-4">
        <div class="card">
            <!-- Card content -->
        </div>
    </div>
    <div class="col-12 col-md-6 col-lg-4">
        <div class="card">
            <!-- Card content -->
        </div>
    </div>
</div>
```

---

## JavaScript Mobile Detection

### Check Device Type
```javascript
// Mobile detection
if (isMobile()) {
    console.log('User is on mobile');
}

if (isTablet()) {
    console.log('User is on tablet');
}

if (isDesktop()) {
    console.log('User is on desktop');
}

// Detailed device info
const device = MobileUtils.getDeviceInfo();
console.log(device);
// Output: { 
//   type: 'phone', 
//   orientation: 'portrait',
//   touchEnabled: true,
//   width: 390,
//   height: 844
// }
```

### Detect Touch Device
```javascript
if (MobileUtils.isTouchDevice()) {
    // Hide hover effects
    // Use touch-optimized interactions
} else {
    // Show hover effects
    // Use mouse-optimized interactions
}
```

### Detect Orientation
```javascript
if (MobileUtils.isPortrait()) {
    // Layout for portrait mode
}

if (MobileUtils.isLandscape()) {
    // Layout for landscape mode
}
```

---

## Mobile Optimization Best Practices

### ✅ DO:
- Use full-width buttons on mobile
- Stack form fields vertically
- Use large touch targets (44x44px minimum)
- Test on real devices
- Use mobile-first CSS approach
- Optimize images for mobile
- Use viewport meta tags correctly
- Handle keyboard appearing/disappearing
- Use semantic HTML
- Implement lazy loading

### ❌ DON'T:
- Use small clickable elements (<44px)
- Use hover-only controls
- Force landscape on phones
- Use autoplay for videos
- Make modals too wide
- Use too many large images
- Disable zoom on mobile
- Use horizontal scrolling content
- Block scrolling unnecessarily
- Use dated frameworks

---

## Testing Tips

### Browser DevTools Mobile Testing
1. Open Chrome DevTools (F12)
2. Click device toolbar icon (Ctrl+Shift+M)
3. Select device from dropdown
4. Test responsive layout
5. Test touch interactions

### Mobile Testing Frameworks
- BrowserStack - Real device testing
- Sauce Labs - Cross-browser testing
- Google PageSpeed Insights - Performance
- Lighthouse - Accessibility & PWA

### Things to Test
1. Tap/click all buttons
2. Try swipe gestures
3. Test with keyboard visible
4. Test in landscape/portrait
5. Test with slow network (3G)
6. Test form submission
7. Test navigation menu
8. Test modal/popup appearance

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Text too small | Ensure font sizes use rem units, check viewport meta |
| Buttons hard to tap | Increase min-height to 44px, add more spacing |
| Form inputs overlap | Use responsive columns, stack on mobile |
| Menu not closing | Check navbar-toggler onClick handlers |
| Images overflow | Add `max-width: 100%` to images |
| Scrolling issues | Check fixed positioning, use viewport meta |
| Keyboard hiding content | Adjust bottom padding, use soft keyboard detection |
| Touch feels slow | Reduce animation duration, optimize JS |

---

## Resources

- [MDN Responsive Web Design](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)
- [Web.dev Mobile Optimization](https://web.dev/mobile/)
- [CSS Tricks Flexbox](https://css-tricks.com/snippets/css/a-guide-to-flexbox/)
- [Can I Use - Browser Support](https://caniuse.com/)

