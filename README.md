# CleanTrust Touch™ YZ3500 — Cinematic Campaign

Multimodel cinematic marketing campaign for the **CleanTrust Touch™ YZ3500 Luminometer**, distributed by [Carpet Cleaners Warehouse](https://ccwonline.com.au).

## Campaign Assets

| File | Description |
|------|-----------|
| `CleanTrust-YZ3500-Cinematic.html` | Scroll-driven animated cinematic experience — hero reveal, exploded device internals, swab process, live RLU analysis, specs + CTA |
| `CleanTrust-YZ3500-Social-Post.jsx` | React component for 1080×1080 social media post with CCW branding |
| `CleanTrust-YZ3500-Social-Copy-Pack.md` | Platform-specific copy for Instagram, LinkedIn, Facebook, Twitter/X with hashtag sets |
| `CleanTrust-YZ3500-Design-Philosophy.md` | "Bioluminescent Precision" design philosophy guiding all visual assets |

## Multimodel Pipeline

| File | Description |
|------|-----------|
| `orchestrate-pipeline.js` | Node.js orchestration script — Gemini (reference frames) → Kling (cinematic video) |
| `Kling-Video-Prompt-Pack.md` | 6-shot cinematic video prompt pack for Kling v1.5 Pro + Gemini Imagen 3 reference frames |
| `env-local-template.env` | API key template for Claude, Gemini, Kling, and Shopify |

## Setup

```bash
cp env-local-template.env .env.local
# Fill in API keys: Gemini, Kling, (optional) Shopify
npm install dotenv
node orchestrate-pipeline.js
```

## Model Routing

- **Claude** — Orchestration, prompt engineering, structured outputs, campaign strategy
- **Gemini (Imagen 3)** — Reference frame image generation for Kling Image-to-Video
- **Kling v1.5 Pro** — Cinematic video generation (device reveal, bioluminescence, RLU readout)

## Product

**CleanTrust Touch™ YZ3500 Luminometer** — AUD $5,291.49
[View on CCW Online](https://ccwonline.com.au/products/cleantrust-touch-yz3500-luminometer)
