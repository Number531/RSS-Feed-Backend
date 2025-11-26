# Email Design Customization Guide

**Complete guide for customizing verification email design to match your website aesthetic.**

---

## Quick Start

The verification email template is located at:
```
app/templates/email_verification.html
```

Simply edit this HTML file to customize colors, fonts, layout, and branding!

---

## What You Can Customize

### ✅ Easy to Change
- Brand colors (primary, secondary, text)
- Logo / header image
- Button style and text
- Welcome message and copy
- Social media links
- Company address and footer

### ⚙️ Advanced (requires HTML knowledge)
- Layout structure
- Dark mode / themes
- Background patterns
- Custom fonts
- Additional sections

---

## Step-by-Step Customization

### 1. Brand Colors

Edit lines 10-18 in `app/templates/email_verification.html`:

```css
--primary-color: #007bff;      /* Change to your brand color */
--background: #f8f9fa;         /* Card background */
--text-primary: #1a1a1a;       /* Main text */
```

**Example:** PSQRD purple branding
```css
--primary-color: #7c3aed;      /* Purple */
--background: #f5f3ff;         /* Light purple background */
```

### 2. Add Your Logo

Replace lines 36-38:

**Before (text):**
```html
<h1>{{ app_name }}</h1>
```

**After (image):**
```html
<img src="https://psqrd.ai/logo.png" alt="PSQRD" width="150">
```

### 3. Customize Button

Edit the button style (lines 68-78):

```css
background-color: #7c3aed;     /* Your brand color */
border-radius: 25px;           /* Pill shape */
```

### 4. Update Message

Change the welcome text (lines 50-62):

```html
<h2>Hey {{ username }}! 👋</h2>
<p>Welcome to PSQRD - verify your email to get started!</p>
```

### 5. Add Social Links

Uncomment and edit lines 112-122:

```html
<a href="https://twitter.com/psqrd_ai">Twitter</a>
<a href="https://linkedin.com/company/psqrd">LinkedIn</a>
```

---

## Testing Your Design

### Send Test Email

```bash
python scripts/testing/test_graph_email.py
```

This sends a test email to `ehgj1996@gmail.com` with your custom design.

### Preview in Browser

```bash
open app/templates/email_verification.html
```

Replace `{{ variables }}` with sample text:
- `{{ app_name }}` → "PSQRD"
- `{{ username }}` → "TestUser"
- `{{ verification_url }}` → "https://psqrd.ai/verify?token=test"

---

## Design Tips

### ✅ Best Practices

- **Keep it simple** - Email clients have limited CSS support
- **Use inline styles** - External CSS is stripped
- **Test on mobile** - 60%+ of emails are read on phones
- **Provide fallbacks** - Use web-safe fonts and colors
- **Include alt text** - For accessibility

### ❌ Avoid

- JavaScript (blocked by email clients)
- Complex animations
- Large images (> 100KB)
- External CSS files
- Flexbox/Grid layouts (use tables)

---

## Common Customizations

### Dark Mode

```css
--primary-color: #8b5cf6;
--background: #1f2937;         /* Dark */
--text-primary: #f9fafb;       /* Light text */
```

### Minimalist Design

```css
--primary-color: #000000;
--background: #ffffff;
--border-color: #e5e5e5;
border-radius: 0;              /* Sharp edges */
```

### Gradient Button

```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
```

---

## Need Help?

1. **Template location**: `app/templates/email_verification.html`
2. **Template renderer**: `app/utils/email_templates.py`
3. **Email service**: `app/services/graph_email_service.py`
4. **Test script**: `scripts/testing/test_graph_email.py`

Make edits to the HTML template, then test with the script above!

---

**Quick Reference:**
- Colors: Lines 10-18
- Logo: Lines 35-42
- Button: Lines 68-80
- Message: Lines 50-62
- Footer: Lines 107-140

