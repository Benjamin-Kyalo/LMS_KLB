# Public site content configuration

The public homepage keeps its editable text in one file:

`frontend/src/config/publicSite.js`

No `Home.jsx` change is needed to customise the footer or the role previews.

## Footer

Edit `DEFAULT_FOOTER`:

```js
export const DEFAULT_FOOTER = {
  name: "KLB Digital Learning Ecosystem",
  lines: [
    "Kenya Literature Bureau · Nairobi, Kenya",
    "Access help: contact your school administrator",
    "Learning management · School information · Digital publishing",
  ],
  credit: {
    prefix: "Photography via ",
    linkLabel: "Unsplash",
    linkHref: "https://unsplash.com/license",
    suffix: " · Illustration by KLB",
  },
};
```

- `name` renders as the bold footer heading.
- Each entry in `lines` becomes one footer line.
- `credit` renders the photography/illustration acknowledgement. Keep the
  Unsplash licence link unless the photographs are replaced and recredited in
  `docs/ASSET_CREDITS.md`.

## Role access preview

Edit `DEFAULT_ROLE_PREVIEWS`. Keys match the role buttons on the homepage:
`learners`, `guardians`, `teachers` and `content`.

```js
learners: {
  rights: ["..."],
  content: ["..."],
},
```

When a visitor selects a role, the homepage shows those two lists and the
workspace link for that role. The lists describe access already enforced by the
Django backend; do not advertise rights that the API does not grant.

## Optional runtime override

A deployment can override values without a rebuild by setting
`window.__KLB_SITE_CONFIG__` before the React app mounts, for example in
`frontend/index.html`:

```html
<script>
  window.__KLB_SITE_CONFIG__ = {
    footer: {
      name: "Custom KLB site",
      lines: ["Custom contact line"],
      credit: {
        prefix: "Images: ",
        linkLabel: "Licence",
        linkHref: "https://example.test/licence",
        suffix: "",
      },
    },
    rolePreviews: {
      learners: {
        rights: ["Custom right"],
        content: ["Custom content area"],
      },
    },
  };
</script>
```

Omitted fields keep their defaults from `publicSite.js`. The homepage has tests
for both the default footer and a runtime override.
