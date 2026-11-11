# GitHub Profile SVG Card Generator

This repository generates a stack of animated SVG cards that can be embedded in a GitHub profile README.

- **hero.svg** – Name, tagline and optional portrait.
- **tiles.svg** – Three linked icons (GitHub, LinkedIn, website).
- **contributions.svg** – Monthly contribution bar chart with streak info.
- **repo_*.svg** – One card per featured repository (defined in `featured_repos.json`).
- **heatmap.svg** – Re‑coloured contribution heat‑map.

The workflow `update-profile-art.yml` runs daily, fetches fresh contribution data, renders the cards, and commits them back to the repo.
