# Kling Video Generation — Prompt Pack
## CleanTrust Touch™ YZ3500 Cinematic Campaign

All prompts designed for Kling v1.5 Pro mode. Use Image-to-Video where reference frames are available from Gemini-generated stills.

---

## Shot 01 — Hero Device Reveal
**Type:** Text-to-Video
**Duration:** 5s
**Aspect Ratio:** 9:16 (vertical/Reels), 16:9 (landscape/LinkedIn)
**Camera:** Slow orbit, 15° above eye level

**Prompt:**
```
Cinematic product reveal of a handheld scientific luminometer device on a pure black background. The device is a sleek rectangular instrument with a glowing 5.5 inch touchscreen display showing teal-cyan data readouts. Slow orbital camera movement around the device. Volumetric teal-cyan light emanating from the screen illuminates the matte black device body. Particles of light drift upward like bioluminescent plankton. Ultra-sharp product photography quality. Dark, moody, scientific laboratory lighting. 8K render quality. No text overlay.
```

**Negative Prompt:**
```
cartoon, illustration, low quality, blurry, text, watermark, logo, bright background, colorful, cluttered, hands, people
```

---

## Shot 02 — Swab Collection (Surface Testing)
**Type:** Text-to-Video
**Duration:** 5s
**Aspect Ratio:** 16:9
**Camera:** Close-up macro, slight dolly forward

**Prompt:**
```
Extreme close-up of a professional ATP testing swab being drawn across a polished stainless steel surface in a commercial kitchen environment. Clinical lighting. The swab tip contacts the surface at a 30 degree angle. Shallow depth of field with the swab tip in razor-sharp focus. Background is softly blurred industrial stainless steel. Cool blue-white lighting. Professional hygiene inspection setting. Cinematic grade color grading with slight teal shadows. Slow deliberate motion. 8K quality.
```

**Negative Prompt:**
```
cartoon, illustration, amateur, shaky camera, bright saturated colors, text, watermark, dirty environment
```

---

## Shot 03 — Swab Insertion into Device
**Type:** Image-to-Video (use Gemini-generated device close-up as reference)
**Duration:** 5s
**Aspect Ratio:** 9:16
**Camera:** Close-up, static with slight rack focus

**Prompt:**
```
Close-up cinematic shot of a testing swab being carefully inserted into the sample chamber of a handheld luminometer device. The insertion slot glows with faint teal-cyan bioluminescent light from within the device chamber. The swab slides smoothly downward into the reaction chamber. The device screen in the background shows "READY" in cyan text. Dark laboratory environment. Volumetric light spilling from the chamber opening. Professional scientific instrument aesthetic. Extreme precision and care in the hand movement. 8K cinematic quality.
```

**Negative Prompt:**
```
cartoon, illustration, toy, plastic, cheap, bright colors, cluttered background, text overlay
```

---

## Shot 04 — Internal Bioluminescence Reaction (The Hero Shot)
**Type:** Text-to-Video
**Duration:** 10s
**Aspect Ratio:** 1:1 (square for social), 16:9 (landscape)
**Camera:** Macro internal view, slow push-in

**Prompt:**
```
Microscopic cinematic view inside a bioluminescence reaction chamber. A transparent cylindrical tube filled with clear reagent liquid. As ATP molecules contact the luciferin enzyme, hundreds of tiny points of teal-cyan light begin to appear and cascade through the liquid like a galaxy forming. The bioluminescent glow intensifies progressively, filling the chamber with ethereal blue-green light. Tiny luminous particles swirl in fluid dynamics patterns. A precision photodiode sensor at the base of the chamber captures the light, its surface reflecting the bioluminescent glow. Scientific visualization aesthetic. Pure black background surrounding the chamber. Volumetric light rays emanating through the liquid. 8K macro cinematography quality. Mesmerizing and beautiful.
```

**Negative Prompt:**
```
cartoon, illustration, CGI looking, plastic, unrealistic, bright background, text, UI elements, cluttered
```

---

## Shot 05 — RLU Reading Data Cascade
**Type:** Image-to-Video (use HTML screenshot of RLU display as reference)
**Duration:** 5s
**Aspect Ratio:** 9:16
**Camera:** Static frontal, screen focus

**Prompt:**
```
Cinematic close-up of a luminometer device touchscreen display in a dark environment. The screen shows a large teal-cyan number rapidly counting upward from 0 to 142, with the text "RLU" below it. Concentric ring graphics pulse outward from the number on the display. A green checkmark appears as the reading stabilizes. The screen glow illuminates the edges of the matte black device body. Data visualization bars animate along the bottom of the screen. Scientific instrument display aesthetic. Dark background. The screen is the sole light source. Professional grade. 8K quality.
```

**Negative Prompt:**
```
cartoon, pixelated screen, CRT monitor, old technology, bright room, text overlay outside screen, watermark
```

---

## Shot 06 — Closing Brand Shot (CCW + CleanTrust)
**Type:** Text-to-Video
**Duration:** 5s
**Aspect Ratio:** 9:16 and 16:9
**Camera:** Slow pull-back reveal

**Prompt:**
```
The luminometer device sits on a dark reflective surface. The device screen displays a completed test reading glowing in teal-cyan. Camera slowly pulls back to reveal the full device in a cinematic hero composition. Volumetric light beams emanate upward from the device like a beacon. Floating bioluminescent particles drift in the surrounding darkness. The device is centered in the frame with generous negative space for text overlay. Ultra-premium product photography aesthetic. Dark gradient background from deep navy to pure black. 8K cinematic final shot.
```

**Negative Prompt:**
```
cartoon, illustration, cluttered, busy background, multiple objects, text, logos, bright lighting, consumer electronics
```

---

## Post-Production Overlay Notes

After Kling generates the raw video clips, add text overlays in post:

**Shot 01 overlay:** "CleanTrust Touch™ YZ3500" (top), CCW logo mark (top-left)
**Shot 02 overlay:** "01 — SWAB" (bottom-left, monospace)
**Shot 03 overlay:** "02 — INSERT" (bottom-left, monospace)
**Shot 04 overlay:** "BIOLUMINESCENCE DETECTION" (bottom center, small caps)
**Shot 05 overlay:** "142 RLU — SURFACE CLEAN" (only if not visible on device screen)
**Shot 06 overlay:** CCW logo (center), "ccwonline.com.au" (below), "Buy Now — $5,291.49" (bottom)

---

## Gemini Image Generation Prompts (Reference Frames for Kling)

Use these with Gemini Imagen 3 to create the reference stills that Kling's Image-to-Video mode uses as starting frames:

### Reference Frame A — Device Hero
```
Professional product photography of a handheld ATP luminometer device, rectangular matte black body with a 5.5 inch glowing teal-cyan touchscreen display showing data readouts. Sitting on a pure black reflective surface. Single dramatic side light. Studio product photography. 8K.
```

### Reference Frame B — Chamber Close-up
```
Extreme macro photograph of the interior of a clear cylindrical test tube chamber filled with liquid showing bioluminescent blue-green glowing particles suspended in fluid. Scientific laboratory aesthetic. Pure black background. 8K macro photography.
```

### Reference Frame C — Device Screen RLU Display
```
Close-up photograph of a modern touchscreen device display showing the number 142 in large teal-cyan glowing text with "RLU" below it. Concentric circle graphics surrounding the number. Dark interface design. Pure black background around the device. 8K.
```

---

## Orchestration Sequence

```
1. Gemini Imagen 3 → Generate Reference Frames A, B, C
2. Kling v1.5 Pro → Shot 01 (text-to-video, 5s)
3. Kling v1.5 Pro → Shot 02 (text-to-video, 5s)
4. Kling v1.5 Pro → Shot 03 (image-to-video from Frame A, 5s)
5. Kling v1.5 Pro → Shot 04 (text-to-video, 10s) ← HERO SHOT
6. Kling v1.5 Pro → Shot 05 (image-to-video from Frame C, 5s)
7. Kling v1.5 Pro → Shot 06 (text-to-video, 5s)
8. Post-production → Stitch clips, add CCW branding overlays, audio
```

**Estimated Kling API cost:** ~35 seconds of Pro video = approximately $3.50–$7.00 USD depending on resolution and retry rate.
