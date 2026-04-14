---
name: vue-develop
description: 当用户提到vue相关内容时，使用这个skill，帮助指定vue过程中使用的配置.
---

# Vue Develop
Use the existing frontend stack instead of imposing a new one. Match the repository's Vue major version, package manager, state solution, routing conventions, CSS strategy, test runner, and file layout before editing code.

Prefer small, local changes that fit the current architecture. Put reusable stateful logic in composables or stores, keep presentational components narrow, and verify behavior with the project's existing lint, typecheck, and test commands when available.

vue开发过程中，css使用less，尽可能使用scoped，vue开发尽可能简单，不要太复杂，js代码尽可能简洁，views中的内容拆分到多个文件/文件夹中分模块去完成，减少大量代码出现在一个文件中的情况

## Workflow

1. Identify the stack.
Look for `package.json`, `vite.config.*`, `nuxt.config.*`, `tsconfig.json`, router setup, store setup, and test config. Confirm whether the app uses Vue 3, Options API or Composition API, JavaScript or TypeScript, Pinia or Vuex, and the active CSS approach.

2. Follow local conventions.
Reuse established patterns for imports, prop typing, emitted events, slot APIs, API clients, and naming. If the repo already has wrapper components, utility composables, or feature folders, extend them instead of creating parallel abstractions.

3. Put logic in the right place.
Use components for rendering and user interaction.
Use composables for reusable reactive logic and side effects.
Use stores for shared application state.
Use router definitions and guards for navigation concerns.
Keep data-fetching boundaries consistent with the existing app structure.

4. Implement with Vue-native patterns.
In Vue 3, prefer `script setup` when the codebase already uses it.
Use computed state instead of duplicating derived data.
Watch sparingly; prefer computed values and explicit event flows when possible.
Keep props one-way; emit events or update stores instead of mutating parent-owned state.
Handle async UI with explicit loading, success, and error states.

5. Verify behavior.
Run the repo's existing frontend checks when they exist, typically linting, typechecking, unit tests, or a targeted build. If a command is missing or the environment blocks execution, state that clearly.

## Implementation Rules

Prefer composition over large monolithic components.
Break repeated template or state logic into child components or composables.

Keep public APIs stable.
If changing component props, emits, slots, store contracts, or route params, update all call sites and tests in the same pass.

Be careful with reactivity boundaries.
When destructuring reactive objects, preserve reactivity with the project's existing pattern.
Avoid unnecessary watchers that mirror one reactive source into another.

Prefer typed interfaces when the repo uses TypeScript.
Type props, emits, store state, and API payloads consistently with local conventions.

Respect styling conventions.
Match the existing approach for scoped styles, CSS modules, utility classes, or design-system tokens. Do not introduce a new styling system for a small feature.

## Common Tasks

### Components
Add or update props, emits, slots, and local UI state without pushing unrelated logic into the component.
For forms, keep validation, submission state, and error rendering explicit.

### Composables
Extract logic that is reused or hard to read inline. Name composables with `use...`, return only the reactive surface the caller needs, and keep network side effects and cleanup explicit.

### Stores
Use the existing store library. Keep actions responsible for async work and state mutation rules consistent with the rest of the codebase. Do not move local component state into a global store without a clear sharing need.

### Routing
Place route records, nested routes, metadata, and guards in the existing router structure. If route params or query handling change, update links, navigation helpers, and dependent tests.

### Async Data
Use the project's established client or fetch wrapper. Normalize loading and error handling at the same layer the repo already uses.

## Output Expectations

When finishing work:

- Summarize the user-visible change.
- Reference the main files touched.
- Report which checks ran and which did not.
- Call out any contract changes, migration risks, or follow-up work.

## Example Triggers

- "Use `$vue-develop` to add a paginated table to this Vue 3 admin page."
- "Use `$vue-develop` to refactor this large component into composables and child components."
- "Use `$vue-develop` to debug why this Pinia store is not updating the UI."
- "Use `$vue-develop` to add a guarded route and wire it into the existing router."
