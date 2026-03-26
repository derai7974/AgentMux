## Project architecture review lens

- Review architecture first. Style and minor cleanup are secondary.
- Check that each changed component has a clear responsibility and a single main reason to change.
- Flag mixed responsibilities immediately, especially when terminal UI, runtime control, workflow policy, session/state handling, and external integrations bleed into one another.
- For this repo, pay close attention to the seams between `pipeline`, `monitor`, `terminal_ui`, `runtime`, `workflow`, `integrations`, `configuration`, `sessions`, and `shared`.

## Interface checks

- Verify that component boundaries are expressed through clear interfaces, narrow APIs, and stable data contracts.
- Call out excessive cross-module knowledge, wide helper imports, dependency bags, or functions with too many unrelated parameters.
- Prefer a few explicit component interfaces over many ad hoc helper calls across packages.
- Check that dependency direction stays coherent and that inner workflow logic does not reach directly into terminal/runtime/integration details without an intentional interface.

## Review output expectations

- Report findings in terms of cohesion, coupling, ownership, and interface quality.
- Distinguish between a real component cut and a superficial file move.
- Block approval when code has been rearranged without clarifying responsibilities or tightening interfaces.
- When possible, suggest the correct owning component and the interface that should exist at that seam.
