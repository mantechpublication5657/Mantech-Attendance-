# ManTech HRMS Chatbot — Django Integration Guide

A plug-and-play chatbot widget for your existing Django HRMS.
Shows only after login. Greets the user by name. No database, no new models needed.

---

## Files in this package

```
mantech_chatbot/
├── static/
│   └── mantech_chatbot/
│       ├── css/
│       │   └── chatbot.css          ← All chatbot styles
│       └── js/
│           └── chatbot.js           ← All chatbot logic
└── templates/
    └── mantech_chatbot/
        └── chatbot_widget.html      ← Template snippet to include
```

---

## Step 1 — Copy files into your project

Copy the entire `mantech_chatbot/` folder into your Django project root
(same level as `manage.py`).

```
your_project/
├── manage.py
├── mantech_chatbot/        ← paste here
│   ├── static/
│   └── templates/
├── your_app/
└── hrms_project/
```

---

## Step 2 — Register the app in settings.py

Open `hrms_project/settings.py` and add `'mantech_chatbot'` to INSTALLED_APPS:

```python
INSTALLED_APPS = [
    # ... your existing apps ...
    'mantech_chatbot',
]
```

This lets Django discover the static files and templates automatically.

---

## Step 3 — Add {% load static %} to your base template

Open your base template (usually `templates/base.html` or `templates/layout.html`).

Make sure the very first line has:

```django
{% load static %}
```

---

## Step 4 — Include the chatbot widget

Paste this ONE line just before the closing `</body>` tag in your base template:

```django
{% include "mantech_chatbot/chatbot_widget.html" %}
```

Example of how your base.html bottom should look:

```html
    ...your footer HTML...

    {% include "mantech_chatbot/chatbot_widget.html" %}

  </body>
</html>
```

That's it. The widget automatically:
- Shows ONLY when `request.user.is_authenticated` is True
- Greets the user by their `first_name` (falls back to `username`)
- Hides itself completely from logged-out visitors

---

## Step 5 — Collect static files (production only)

If you are running in production with `DEBUG = False`, run:

```bash
python manage.py collectstatic
```

In development (`DEBUG = True`), Django serves static files automatically.

---

## Step 6 — Ensure your views pass `request` to templates

Your views must use `RequestContext` (which is the default with `render()`):

```python
from django.shortcuts import render

def dashboard(request):
    return render(request, 'dashboard.html', context)
    # render() automatically includes request context — chatbot will work.
```

---

## Customising the chatbot

### Change the accent colour
Edit `chatbot.css` and replace `#1a2e4a` (dark navy) with your brand colour.

### Add a new topic / question
Open `chatbot.js` and add a new entry to the `KB` object:

```javascript
"my_new_topic": {
  text: "Here is the answer to the new topic...",
  qr: ["Related question 1", "Related question 2", "Main menu"]
},
```

Then add a new row to the `INTENTS` array so the bot recognises keywords:

```javascript
{ key: "my_new_topic", patterns: ["keyword1", "keyword2"] },
```

Finally add the label to `labelMap` and to the `KB["menu"].qr` list.

### Change attendance window timings
In `chatbot.js`, search for `8:30 AM – 10:30 AM` and update to your timings.

### Connect to a real backend (optional)
Replace the `botReply()` function in `chatbot.js` with a `fetch()` call to a
Django view that returns JSON `{ text, qr }` for dynamic answers.

---

## Requirements

- Django 3.2+ (any version that supports `{% static %}` and `request.user`)
- No extra pip packages needed
- Works with Bootstrap, Tailwind, or any CSS framework — styles are scoped to `#mt-chat-*`

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Chatbot not showing | Check `request.user.is_authenticated` is True in your view |
| CSS/JS 404 error | Run `collectstatic` or check `INSTALLED_APPS` includes `mantech_chatbot` |
| Name shows as "Employee" | Ensure `request.user.first_name` is set in Django admin or profile |
| Widget overlaps footer | Change `bottom: 28px; right: 28px` in `chatbot.css` |
| Widget hidden behind modals | Increase `z-index: 9999` in `chatbot.css` |
