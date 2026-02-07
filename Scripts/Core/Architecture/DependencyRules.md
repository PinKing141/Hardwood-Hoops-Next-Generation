# C# Architecture Dependency Rules

These rules define allowable dependencies for the C# port. Keep the arrows pointing inward.

```
Domain → Simulation → App → UI
Infra → App/Simulation (never the other way around)
```

## Allowed References
- **Domain**: no dependencies on other layers.
- **Simulation**: may reference Domain only.
- **App**: may reference Domain + Simulation + Infra abstractions.
- **UI**: may reference App (and data contracts surfaced by App).
- **Infra**: may reference Domain and Simulation for concrete adapters, never UI.

## Notes
- Introduce interfaces in `Infra` or `App` and depend on abstractions.
- Avoid direct references from Domain to any other layer.

