## Project architecture focus

- Design around cohesive components, not around file count reduction.
- Start by identifying ownership boundaries and reasons to change before proposing moves.
- For this repo, preserve clear separation between `pipeline`, `monitor`, `terminal_ui`, `runtime`, `workflow`, `integrations`, `configuration`, `sessions`, and `shared`.
- Keep terminal presentation concerns in `terminal_ui` / `monitor`, execution substrate in `runtime`, workflow policy in `workflow`, and external system concerns in `integrations`.

## Interface rules

- Define the component interface first, then place implementation behind it.
- Prefer a small number of explicit component-level interfaces over many cross-module helper imports.
- Avoid dependency bags and broad facades that know too much about internal details.
- Avoid functions with more than 5 parameters unless the parameters form a cohesive value object with clear ownership.
- Shared data crossing a boundary should have a named type or stable schema.

## Planning expectations

- In every design/refactor plan, name each target component, its responsibility, its public interface, and its allowed dependencies.
- Call out where responsibilities are currently mixed and how the new cut removes that mixing.
- Favor high cohesion and loose coupling over backward compatibility or minimal file churn.
- Do not propose moves that merely relocate code without improving ownership, interfaces, or dependency direction.
- When introducing a new module or package, justify why it exists and why its responsibility is not already owned elsewhere.
