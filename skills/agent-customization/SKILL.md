# Skill: Use and Create Custom Tags (frontend components)

## Purpose
Provide a short, repeatable workflow for using existing custom UI tags (components) in the frontend and creating minimal, no-styles replacements when a tag is missing.

## When to use
- Editing or adding frontend pages/components in this repository.
- You need to insert a UI element but are unsure whether a custom tag exists.

## Applicability
Workspace-scoped. Intended for contributors working in `src/frontend/src/components/tags`.

## Workflow (step-by-step)
1. Locate the tags folder
   - Path: `src/frontend/src/components/tags`
   - List available tags (filenames without extension).
2. Prefer existing tags
   - If the tag you need exists, import and use it. These components include inline styling and helpers.
3. If a required tag is missing, add a barebones TSX file
   - Create `src/frontend/src/components/tags/<TagName>.tsx` that only exports the component and does not add CSS or extra logic.
   - The component should map to a semantic HTML element and forward props/children.
   - Keep it intentionally minimal (no styles). Example:

```tsx
import React from 'react'
import type { HTMLAttributes } from 'react'

export default function TagName(props: HTMLAttributes<HTMLElement>) {
  const { children, ...rest } = props
  return <div {...rest}>{children}</div>
}
```

   - Replace `<div>` with the most appropriate HTML tag (`button`, `span`, `section`, etc.).
4. Use the new tag in your page/component
   - Import from `components/tags/<TagName>` and use as usual.
5. After finishing the feature, follow-up task (manual): find existing CSS for the visual variant used elsewhere, copy the CSS into the TSX component (or a module), then comment out the copied CSS and add a TODO to re-enable/clean it later.

## Decision points
- If a tag is shared across pages, prefer implementing a minimal component in `tags/` rather than inline JSX at the usage site.
- If the component requires behavior (state, events), stub the props and keep behavior minimal — prefer enhancing later.

## Quality checks
- New tag files contain only exported TSX component and types — no styles, no side effects.
- Component forwards standard HTML attributes and `children`.
- Created file path: `src/frontend/src/components/tags/<TagName>.tsx`.
- Add a follow-up TODO to locate and port styling (commented) after feature is merged.

## Example prompt to the agent
- "Create a barebones tag `MyFancyTag` in `src/frontend/src/components/tags` that renders a `section` and forwards props/children."

## Next customizations to consider
- Add a generator script to scaffold a minimal tag file with proper typing.
- Add lint rule enforcing tag files in `tags/` to be style-free (prevent accidental CSS additions).

---

_Last updated: automated skill generator_
