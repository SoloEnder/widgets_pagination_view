
## v1.1.0 (12/06/26)

### Fix:
- Removed the nothing to show and the loading page

## Refactor:
- removed the unused `dynamic_pages_loader` wrapper
- the role of the deleted `dynamic_pages_switching` is now handled by the `smart_unload` method
- `max_loadables_pages_count` and `widgets` are now property

## v1.1.1
### Fix:
- a bug where a type hint was created before the declaration of the class type
- removed type alias on type declaration

### Refactor:
- removed unused imports
