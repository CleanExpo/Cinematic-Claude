/**
 * CleanTrust YZ3500 — Multimodel Cinematic Pipeline Orchestrator
 *
 * This script orchestrates the full visual generation pipeline:
 *   Claude  → Prompt engineering, sequencing, QA reasoning
 *   Gemini  → Reference frame image generation (Imagen 3)
 *   Kling   → Cinematic video generation (v1.5 Pro)
 *
 * Prerequisites:
 *   1. Copy env-local-template.env → .env.local and fill in API keys
 *   2. npm install dotenv node-fetch jsonwebtoken
 *   3. node orchestrate-pipeline.js
 *
 * API Documentation:
 *   Gemini: https://ai.google.dev/gemini-api/docs/image-generation
 *   Kling:  https://docs.qingque.cn/d/home/eZQBMJiR3dGVzaFZhb0hnTmRR
 */

import 'dotenv/config';
import fs from 'fs/promises';
import path from 'path';
import crypto from 'crypto';

// ─── CONFIG ───
const CONFIG = {
  runId: `${process.env.RUN_ID_PREFIX || 'ccw'}-${Date.now()}`,
  outputDir: process.env.OUTPUT_DIR || './output',
  tracing: process.env.ENABLE_TRACE_LOGGING === 'true',
};

// ─── TRACE LOGGER ───
const traces = [];
function trace(step, provider, data) {
  const entry = {
    timestamp: new Date().toISOString(),
    runId: CONFIG.runId,
    step,
    provider,
    ...data,
  };
  traces.push(entry);
  if (CONFIG.tracing) {
    console.log(`[TRACE] ${step} | ${provider} |`, JSON.stringify(data, null, 0));
  }
}

// ─── GEMINI: Image Generation via Imagen 3 ───
async function generateGeminiImage(prompt, outputFilename) {
  trace('gemini-image-start', 'gemini', { prompt: prompt.slice(0, 80) + '...' });

  const apiKey = process.env.GOOGLE_GEMINI_API_KEY;
  if (!apiKey) throw new Error('GOOGLE_GEMINI_API_KEY not set in .env.local');

  const model = process.env.GEMINI_IMAGE_MODEL || 'imagen-3.0-generate-002';
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:predict?key=${apiKey}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      instances: [{ prompt }],
      parameters: {
        sampleCount: 1,
        aspectRatio: '1:1',
        safetyFilterLevel: 'block_only_high',
      },
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    trace('gemini-image-error', 'gemini', { status: response.status, error: err });
    throw new Error(`Gemini Imagen API error: ${response.status} — ${err}`);
  }

  const data = await response.json();
  const imageBytes = data.predictions?.[0]?.bytesBase64Encoded;
  if (!imageBytes) throw new Error('No image returned from Gemini');

  const outputPath = path.join(CONFIG.outputDir, 'assets', outputFilename);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, Buffer.from(imageBytes, 'base64'));

  trace('gemini-image-complete', 'gemini', { output: outputPath });
  return outputPath;
}

// ─── KLING: JWT Auth Token Generation ───
function generateKlingJWT() {
  const accessKey = process.env.KLING_ACCESS_KEY;
  const secretKey = process.env.KLING_SECRET_KEY;
  if (!accessKey || !secretKey) throw new Error('KLING_ACCESS_KEY / KLING_SECRET_KEY not set');

  // Kling uses a custom JWT — header.payload.signature
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
  const now = Math.floor(Date.now() / 1000);
  const payload = Buffer.from(JSON.stringify({
    iss: accessKey,
    exp: now + 1800, // 30 min expiry
    nbf: now - 5,
  })).toString('base64url');
  const signature = crypto
    .createHmac('sha256', secretKey)
    .update(`${header}.${payload}`)
    .digest('base64url');

  return `${header}.${payload}.${signature}`;
}

// ─── KLING: Text-to-Video ───
async function generateKlingVideo(prompt, negativePrompt, options = {}) {
  const shotId = options.shotId || `shot-${Date.now()}`;
  trace('kling-video-start', 'kling', { shotId, prompt: prompt.slice(0, 80) + '...' });

  const token = generateKlingJWT();
  const baseUrl = process.env.KLING_API_BASE || 'https://api.klingai.com/v1';

  const body = {
    model_name: process.env.KLING_MODEL || 'kling-v1-5',
    prompt,
    negative_prompt: negativePrompt || '',
    duration: options.duration || process.env.KLING_DEFAULT_DURATION || '5',
    mode: options.mode || process.env.KLING_MODE || 'pro',
    aspect_ratio: options.aspectRatio || '16:9',
    cfg_scale: options.cfgScale || 0.5,
  };

  // Image-to-Video: attach reference image
  if (options.referenceImagePath) {
    const imgBuffer = await fs.readFile(options.referenceImagePath);
    body.image = imgBuffer.toString('base64');
    body.image_tail = options.tailImagePath
      ? (await fs.readFile(options.tailImagePath)).toString('base64')
      : undefined;
  }

  const response = await fetch(`${baseUrl}/videos/text2video`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const err = await response.text();
    trace('kling-video-error', 'kling', { shotId, status: response.status, error: err });
    throw new Error(`Kling API error: ${response.status} — ${err}`);
  }

  const data = await response.json();
  const taskId = data.data?.task_id;
  trace('kling-video-submitted', 'kling', { shotId, taskId });

  // Poll for completion
  return await pollKlingTask(taskId, shotId, token, baseUrl);
}

async function pollKlingTask(taskId, shotId, token, baseUrl) {
  const maxAttempts = 60; // 5 minutes at 5s intervals
  for (let i = 0; i < maxAttempts; i++) {
    await new Promise(r => setTimeout(r, 5000));

    const res = await fetch(`${baseUrl}/videos/text2video/${taskId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });

    if (!res.ok) continue;
    const data = await res.json();
    const status = data.data?.task_status;

    if (status === 'succeed') {
      const videoUrl = data.data?.task_result?.videos?.[0]?.url;
      if (videoUrl) {
        // Download video
        const videoRes = await fetch(videoUrl);
        const videoBuffer = Buffer.from(await videoRes.arrayBuffer());
        const outputPath = path.join(CONFIG.outputDir, 'video', `${shotId}.mp4`);
        await fs.mkdir(path.dirname(outputPath), { recursive: true });
        await fs.writeFile(outputPath, videoBuffer);
        trace('kling-video-complete', 'kling', { shotId, taskId, output: outputPath });
        return outputPath;
      }
    } else if (status === 'failed') {
      trace('kling-video-failed', 'kling', { shotId, taskId, data: data.data });
      throw new Error(`Kling task ${taskId} failed: ${JSON.stringify(data.data?.task_status_msg)}`);
    }
    // else still processing...
  }
  throw new Error(`Kling task ${taskId} timed out after ${maxAttempts * 5}s`);
}

// ─── MAIN PIPELINE ───
async function runPipeline() {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`  CleanTrust YZ3500 — Cinematic Pipeline`);
  console.log(`  Run ID: ${CONFIG.runId}`);
  console.log(`${'═'.repeat(60)}\n`);

  await fs.mkdir(path.join(CONFIG.outputDir, 'assets'), { recursive: true });
  await fs.mkdir(path.join(CONFIG.outputDir, 'video'), { recursive: true });
  await fs.mkdir(path.join(CONFIG.outputDir, 'logs'), { recursive: true });

  // ── PHASE 1: Gemini Reference Frames ──
  console.log('▸ Phase 1: Generating reference frames via Gemini Imagen 3...\n');

  const framePrompts = {
    'ref-frame-A-device-hero.png':
      'Professional product photography of a handheld ATP luminometer device, rectangular matte black body with a 5.5 inch glowing teal-cyan touchscreen display showing scientific data readouts. Sitting on a pure black reflective surface. Single dramatic side light creating volumetric light rays. Studio product photography. Ultra-sharp. 8K.',
    'ref-frame-B-chamber-macro.png':
      'Extreme macro photograph of the interior of a clear cylindrical test tube chamber filled with liquid showing bioluminescent blue-green glowing particles suspended in fluid. Scientific laboratory aesthetic. Pure black background. Volumetric caustic light patterns through the liquid. 8K macro photography.',
    'ref-frame-C-rlu-display.png':
      'Close-up photograph of a modern touchscreen device display showing the large number 142 in teal-cyan glowing text with RLU below it. Concentric circle data visualization graphics surrounding the number. Dark scientific interface design. Pure black background around the device edges. 8K quality.',
  };

  const referenceFrames = {};
  for (const [filename, prompt] of Object.entries(framePrompts)) {
    try {
      referenceFrames[filename] = await generateGeminiImage(prompt, filename);
      console.log(`  ✓ ${filename}`);
    } catch (err) {
      console.error(`  ✗ ${filename}: ${err.message}`);
    }
  }

  // ── PHASE 2: Kling Video Generation ──
  console.log('\n▸ Phase 2: Generating cinematic video clips via Kling v1.5 Pro...\n');

  const shots = [
    {
      shotId: 'shot-01-hero-reveal',
      prompt: 'Cinematic product reveal of a handheld scientific luminometer device on a pure black background. The device is a sleek rectangular instrument with a glowing 5.5 inch touchscreen display showing teal-cyan data readouts. Slow orbital camera movement around the device. Volumetric teal-cyan light emanating from the screen illuminates the matte black device body. Particles of light drift upward like bioluminescent plankton. Ultra-sharp product photography quality. Dark moody scientific laboratory lighting. 8K render quality.',
      negativePrompt: 'cartoon, illustration, low quality, blurry, text, watermark, logo, bright background',
      duration: '5',
      aspectRatio: '9:16',
    },
    {
      shotId: 'shot-02-swab-collection',
      prompt: 'Extreme close-up of a professional ATP testing swab being drawn across a polished stainless steel surface in a commercial kitchen. Clinical lighting. The swab tip contacts the surface at 30 degrees. Shallow depth of field with the swab in razor-sharp focus. Background softly blurred industrial stainless steel. Cool blue-white lighting. Cinematic color grading with teal shadows. Slow deliberate motion. 8K.',
      negativePrompt: 'cartoon, illustration, amateur, shaky, bright saturated, text, watermark',
      duration: '5',
      aspectRatio: '16:9',
    },
    {
      shotId: 'shot-03-swab-insertion',
      prompt: 'Close-up cinematic shot of a testing swab being carefully inserted into the sample chamber of a handheld luminometer device. The insertion slot glows with faint teal-cyan bioluminescent light from within. The swab slides smoothly downward. Dark laboratory environment. Volumetric light spilling from the chamber opening. Professional scientific instrument aesthetic. 8K cinematic quality.',
      negativePrompt: 'cartoon, toy, plastic, cheap, bright colors, cluttered, text overlay',
      duration: '5',
      aspectRatio: '9:16',
      referenceImagePath: referenceFrames['ref-frame-A-device-hero.png'],
    },
    {
      shotId: 'shot-04-bioluminescence-hero',
      prompt: 'Microscopic cinematic view inside a bioluminescence reaction chamber. A transparent cylindrical tube filled with clear reagent liquid. As ATP molecules contact luciferin enzyme, hundreds of tiny points of teal-cyan light appear and cascade through the liquid like a galaxy forming. The bioluminescent glow intensifies progressively. Tiny luminous particles swirl in fluid dynamics patterns. A precision photodiode sensor at the base captures the light. Pure black background. Volumetric light rays through liquid. 8K macro cinematography. Mesmerizing and beautiful.',
      negativePrompt: 'cartoon, CGI looking, plastic, unrealistic, bright background, text, UI, cluttered',
      duration: '10',
      aspectRatio: '1:1',
    },
    {
      shotId: 'shot-05-rlu-readout',
      prompt: 'Cinematic close-up of a luminometer touchscreen display in darkness. Screen shows a large teal-cyan number rapidly counting from 0 to 142 with RLU text. Concentric ring graphics pulse outward. Green checkmark appears as reading stabilizes. Screen glow illuminates device edges. Data bars animate along screen bottom. Scientific instrument display. Dark background. Screen is sole light source. 8K.',
      negativePrompt: 'cartoon, pixelated, CRT, old tech, bright room, text overlay outside screen, watermark',
      duration: '5',
      aspectRatio: '9:16',
      referenceImagePath: referenceFrames['ref-frame-C-rlu-display.png'],
    },
    {
      shotId: 'shot-06-closing-brand',
      prompt: 'The luminometer device sits on a dark reflective surface. Screen displays completed test reading glowing teal-cyan. Camera slowly pulls back to reveal full device in cinematic hero composition. Volumetric light beams emanate upward like a beacon. Floating bioluminescent particles drift in surrounding darkness. Device centered with generous negative space for text overlay. Ultra-premium product photography. Dark gradient background from deep navy to pure black. 8K cinematic final shot.',
      negativePrompt: 'cartoon, cluttered, busy background, multiple objects, text, logos, bright lighting',
      duration: '5',
      aspectRatio: '16:9',
    },
  ];

  for (const shot of shots) {
    try {
      const result = await generateKlingVideo(shot.prompt, shot.negativePrompt, {
        shotId: shot.shotId,
        duration: shot.duration,
        aspectRatio: shot.aspectRatio,
        referenceImagePath: shot.referenceImagePath,
      });
      console.log(`  ✓ ${shot.shotId} → ${result}`);
    } catch (err) {
      console.error(`  ✗ ${shot.shotId}: ${err.message}`);
    }
  }

  // ── PHASE 3: Save trace log ──
  const logPath = path.join(CONFIG.outputDir, 'logs', `${CONFIG.runId}-trace.json`);
  await fs.writeFile(logPath, JSON.stringify(traces, null, 2));
  console.log(`\n▸ Pipeline complete. Trace log: ${logPath}`);
  console.log(`  Total steps traced: ${traces.length}`);
  console.log(`${'═'.repeat(60)}\n`);
}

runPipeline().catch(err => {
  console.error('Pipeline failed:', err);
  process.exit(1);
});
