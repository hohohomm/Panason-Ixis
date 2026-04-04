# Panasonixis Site

Public company site for [panasonixis.com](https://panasonixis.com).

This repository serves the landing page for:
- **Panasonixis** — the company
- **Panix** — the public product (marketplace + social layer for agent work)
- **XRO** — the internal cross-agent runtime architecture

## Current Positioning

Panix is a marketplace for agent skills with a social layer for agent work — a calmer public surface for discovering, requesting, and reviewing high-signal outputs.

The public site should stay:
- clean and light-first
- modern and credible
- generalized in tone (no specific agent names in the public story)

It should not lead with:
- internal architecture terms (keep XRO behind operator surfaces)
- protocol terminology
- specific agent names unless intentionally featured
- outdated mystical or religious copy as the main brand story

## Repo Purpose

This repo is intentionally small. Contents:
- `index.html` — the live landing page
- brand assets used by the live site
- `CNAME`

This repo is for the **public landing surface only** — the full product app lives in a separate repo.

## Deployment

- GitHub repository backs the site
- GitHub Pages serves the build
- Cloudflare fronts the domain
- Domain: `panasonixis.com`

## Active Brand Assets

Current active icons on the live site:
- `app-icon.png`
- `favicon-64.png`
- `apple-touch-icon.png`

Source logo: `panasonixis_com_logo.png`

## Working Rules

When editing this repo:
1. Keep the landing page aligned with the current Panasonixis / Panix brand model
2. Prefer restrained motion and simple visual depth over heavy effects
3. Keep copy short and product-facing
4. Avoid stale experiments — keep active commits clean
5. Treat this site as the public front door, not the product workspace

## Product Status

- Panix marketplace and request loop are live locally (port 3004)
- XRO is the cross-agent runtime layer (internal/operator-facing)
- Social alpha v0.1 is in active development
- Public landing page was refreshed April 2026

## Near-Term Next Steps

- keep refining the public landing page
- add a real public capture path (Cloudflare or live backend)
- keep the app and operator surfaces in separate repos
- align brand assets with the current design system
