# Current Limitations

## Frontend Formation v1 expressiveness

The supplied `screen-manifest.schema.json` permits only these tags:

```text
button, div, section, aside, header, footer, p, span, output
```

It cannot declare:

- text inputs or textareas;
- selects;
- links and route navigation;
- SVG or canvas topology;
- dynamic agent-grid children;
- field-level validation attributes;
- arbitrary ARIA attributes.

The generated projects therefore represent contract-valid semantic surfaces using deterministic fixture controls. They do not replace the eventual full browser implementation required by the canonical Intent Maps.

## Runtime integration

`mock-driver.js` is a deterministic verification driver. It does not call the FastAPI backend, consume the teleology SSE endpoint, connect to WebSockets, start host processes, download an archive, or open a browser/native app.

A production driver must replace the fixture with authenticated HTTP, SSE, and WebSocket bindings while retaining the same action IDs, gate semantics, feedback paths, and error distinctions.

## Contract-only backend capabilities

The canonical maps mark substantial Continuation and Deliverable Launch capabilities as contract-only or incomplete. The fixture can demonstrate their intended gates, but it labels those results `contract_fixture` and does not claim those backend endpoints are shipped.

## Browser-test environment

Chromium navigation to local HTTP and `file:` URLs is blocked by administrator policy in this execution environment. The browser check therefore runs the generated HTML, CSS, and JavaScript inside real headless Chromium through `page.set_content`, with a deterministic `localStorage` polyfill. DOM events, native button keyboard activation, async feedback, gates, projection behavior, and console errors are tested. Real route loading and backend network transport are not.
