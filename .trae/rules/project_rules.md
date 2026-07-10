# Project Rules

## Version Management

When making any code changes to the project, you MUST update the version number and user manual:

1.  **Version Number**: The version is defined in THREE places. All must be kept in sync:
    -   `backend/app/config.py` — `app_version` field in `Settings` class
    -   `frontend/src/components/Layout.tsx` — the `<span>vX.Y.Z</span>` text in the header (e.g., `v1.0.1`)
    -   `InvoiceMaster_部署手册与使用说明.docx` — version on the cover page and throughout

2.  **Version Bumping Rules**:
    -   **Major (`X.0.0`)**: Breaking changes, significant new features, or major UI redesign
    -   **Minor (`X.Y.0`)**: New features, non-breaking enhancements
    -   **Patch (`X.Y.Z`)**: Bug fixes, small improvements, or documentation updates

3.  **User Manual**: After any feature addition or significant change, regenerate:
    -   `InvoiceMaster_部署手册与使用说明.docx` in the project root
    -   Use the `docx` skill to generate it via `generate_manual.js`
    -   Ensure the version number matches across cover page and content

## Commit Message Format

Use conventional commits: `type(scope): description`

-   `feat`: new feature
-   `fix`: bug fix
-   `docs`: documentation only
-   `refactor`: code change that neither fixes a bug nor adds a feature
-   `style`: formatting, whitespace
-   `chore`: build process or auxiliary tool changes

## Code Style

-   Python: Follow existing patterns in `backend/app/`. No comments unless specifically requested.
-   TypeScript/React: Follow existing patterns in `frontend/src/`. Use `cn()` from `@/lib/utils` for class merging.
-   Use the `npm run build` command to verify frontend builds before completing.
