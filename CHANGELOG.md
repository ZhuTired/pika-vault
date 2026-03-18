# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Drag-and-Drop Sorting**: Added an "Edit Mode" to the Credentials and Bookmarks pages allowing users to manually drag and drop cards to reorder them.
- **Hash-based URL Routing**: The application now updates the URL hash (e.g., `#/credentials/database` or `#/bookmarks/work`) when navigating between tabs and categories. This allows users to refresh the page without losing their current view context.
- **Auto-fetch Favicons**: When opening a bookmark that does not have a custom favicon, the system will now attempt to automatically fetch and save the website's favicon in the background.

### Changed
- Database schema updated to include `sort_order` for credentials.
