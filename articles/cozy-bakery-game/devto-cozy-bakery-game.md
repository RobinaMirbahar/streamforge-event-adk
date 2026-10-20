---
title: "I Built a Cozy 60 FPS AI Agent Bakery Game to Teach RAG, Guardrails, Context Caching and Multi-Agent Orchestration"
published: false
description: "An interactive 60 FPS AI Agent Architecture Training and Simulation Platform built with Google Gemma 4 and Antigravity where pastry stations map 1-to-1 to production AI patterns."
tags: ai, gamedev, opensource, javascript
cover_image: https://raw.githubusercontent.com/RobinaMirbahar/cozy-ai-agent-cafe-game/main/assets/cozy_ai_cafe_banner.jpg
---

## What I Built

Who said learning **AI System Design** has to be all dark cyberpunk terminal screens and exploding servers?

I built and open-sourced **Prompt Paws: The Cozy AI Agent Cafe & Bakery** (architected with **Google Gemma 4 & Antigravity**) — an interactive **60 FPS AI Agent Architecture Training & Simulation Platform** disguised as a cozy pastel pastry bakery run by **Robot-Cat Chefs**.

**Who would use it?**
- **Engineering Teams, Bootcamps & Developer Relations Programs** training developers on production LLM architecture (where a single uncached system prompt or missing input guardrail can cost thousands of dollars in wasted tokens or security incidents).
- Instead of static slide decks, **Prompt Paws** gives teams an interactive, visual sandbox where every pastry station maps **1-to-1** to a real production AI pattern:

| Cozy Bakery Station | Critter Order Handled | Production AI Engineering Layer |
| --- | --- | --- |
| **Flash Pastry Oven** | Prompt Croissant | **Fast Low-Latency Model (`gemini-2.5-flash` / Gemma 4)** |
| **Context Cache Jar** | Repeat Owl Menu Query | **Prefix & Context Caching (95% Token Savings)** |
| **Guardrail Flour Sieve** | Spicy Injection Jalapeno | **Input Classifier & Prompt-Injection Sanitizer** |
| **Vector Berry Patch** | RAG Berry Tart | **Vector Search & Fact Grounding (Anti-Hallucination)** |
| **Tool-Call Boba Mixer** | Code-Exec Boba Tea | **Deterministic Python Sandbox & Function Calling** |
| **Deep-Think Souffle Oven** | Reasoning Souffle | **Extended Thinking / System-2 Deliberation** |
| **Subagent Sous-Chef Bell** | Parallel Banquet Aura | **Multi-Agent Parallel Delegation (+45% Speed Aura)** |

---

## Live Playable Demo & How to Play in 30 Seconds

- **Play Live in Your Browser (60 FPS HTML5 Canvas):** [https://robinamirbahar.github.io/cozy-ai-agent-cafe-game/](https://robinamirbahar.github.io/cozy-ai-agent-cafe-game/)
- **100% Client-Side Simulation ($0.00 API Cost & Zero Keys Required):** The entire game runs locally inside your browser using a deterministic HTML5 Canvas simulation engine — **no API keys, no sign-ups, and zero paid LLM tokens** are ever used when you or your team play.

![How to Play Prompt Paws in 3 Easy Steps](https://files.catbox.moe/i9wg40.jpg)

### What Is the Core Gameplay Loop?
Think of **Prompt Paws** as a **cozy Tower-Defense & Kitchen-Management game for AI Agent Architecture**:
- **Customer Pastry Orders = Incoming User Prompts** moving along the bakery conveyor belt toward the **Pickup Window**.
- **Robot-Cat Kitchen Stations = Real-World AI Engineering Components** (Fast LLMs, Context Caches, Input Guardrails, RAG Vector DBs, Deterministic Tool Callers, System-2 Reasoning Models, and Multi-Agent Sous-Chefs) that intercept and process prompts before they reach the customer.
- **Win / Lose Condition:** Every order baked by the right AI Chef Station earns **Star Coins**. If an unbaked order, an ungrounded **Hallucination Puff**, or a sneaky **Prompt Injection** slips all the way to the Pickup Window, you lose a **Cafe Reputation Heart**.

### How to Play in 3 Easy Steps:
1. **STEP 1 — Pick an AI Chef Station (Left Menu):** Click a station card on the left sidebar (start with **Flash Pastry Oven** for `60` coins). Check the **Order Forecast chips** under the level story to see which prompt types are coming.
2. **STEP 2 — Click Any `[+ Slot]` Tile on the Map:** Click one of the 8 pastel counter pads (`Slot 1`–`Slot 8`) beside the conveyor belt to place your Robot-Cat Chef. (Tip: Click a placed chef anytime to **Upgrade** its baking speed or **Refund** it.)
3. **STEP 3 — Click `Open Cafe` (or `Auto-Chef Blueprint`):**
   - Click **`Open Cafe`** (or press `Spacebar`) to start the shift and watch your Robot-Cat Chefs bake.
   - **Want to watch an instant demo first?** Click the purple **`Auto-Chef Blueprint`** button in the top bar on any of the **7 Story Shifts** and the game will automatically build the optimal Guardrail, Cache, RAG, and Subagent pipeline and run it for you.

---

## Open-Source Code

- **GitHub Repository:** [https://github.com/RobinaMirbahar/cozy-ai-agent-cafe-game](https://github.com/RobinaMirbahar/cozy-ai-agent-cafe-game)

---

## How I Built It

I built **Prompt Paws** using an open-source, zero-dependency HTML5 Canvas 60 FPS simulation engine (`game.js`), a 7-shift progressive AI engineering curriculum (`levels.js`), and a procedural WebAudio synthesizer (`audio.js`), orchestrated via **Antigravity** and open agentic workflows.

### 1. Order Routing & Guardrail Sanitization (`game.js`)
Each station inspects passing orders on the winding bakery conveyor ribbon and only picks up tasks that match its architectural role. Notice how **Spicy Prompt-Injection Jalapenos** cannot be safely baked by normal ovens until a **Guardrail Flour Sieve** sanitizes them into safe croissants:

```javascript
function canStationProcessOrder(stationType, ord) {
  // 1. Only the Guardrail Flour Sieve can catch and sanitize Spicy Prompt Injections!
  if (stationType === 'guardrail_sieve') {
    return ord.kind === 'jalapeno';
  }
  // Unfiltered prompt injections bypass normal ovens and damage Cafe Reputation Hearts!
  if (ord.kind === 'jalapeno') {
    return false;
  }

  // 2. Context Cache Jar serves repeated menu queries at 3x speed + bonus Star Coins
  if (stationType === 'cookie_cache') {
    return ord.kind === 'cached' || ord.kind === 'croissant';
  }

  // 3. Vector Berry Patch grounds Berry Tarts so they don't become Hallucination Puffs
  if (stationType === 'vector_garden') {
    return ord.kind === 'tart';
  }

  // 4. Tool-Call Boba Mixer runs deterministic calculations & API recipes
  if (stationType === 'tool_blender') {
    return ord.kind === 'boba';
  }

  // 5. Deep-Think Souffle Oven handles multi-step System-2 reasoning
  if (stationType === 'reasoning_oven') {
    return ord.kind === 'souffle' || ord.kind === 'croissant';
  }

  // 6. Flash Pastry Oven handles high-throughput everyday Prompt Croissants
  if (stationType === 'flash_oven') {
    return ord.kind === 'croissant' || ord.kind === 'cached';
  }

  // 7. Subagent Sous-Chef Bell orchestrates parallel helpers
  if (stationType === 'subagent_bell') {
    return ord.kind !== 'jalapeno';
  }
  return false;
}
```

### 2. Real-Time AI Architecture Linter ("Chef Whiskers")
Before you open the cafe doors, **Chef Whiskers (Staff AI Pastry Architect)** performs live static analysis on your placed stations and warns you about architectural vulnerabilities:

```javascript
function evaluateKitchenArchitecture() {
  const lvl = window.CAFE_LEVELS[currentLevelIdx];
  const weights = lvl.orderWeights;
  const typesPlaced = Object.values(placedStations).map((s) => s.type);
  const alerts = [];

  if (weights.jalapeno && !typesPlaced.includes('guardrail_sieve')) {
    alerts.push({
      kind: 'warn',
      text: 'Prompt Injection Risk! Place a Guardrail Flour Sieve near Slot 1 or 2 to neutralize spicy raccoon orders!'
    });
  }
  if (weights.tart && !typesPlaced.includes('vector_garden')) {
    alerts.push({
      kind: 'warn',
      text: 'Hallucination Warning! Berry Tarts need a Vector Berry Patch (RAG) so chefs do not guess facts!'
    });
  }
  if (weights.boba && !typesPlaced.includes('tool_blender')) {
    alerts.push({
      kind: 'warn',
      text: 'Math/API Alert! Add a Tool-Call Boba Mixer to run deterministic calculations accurately.'
    });
  }
  return alerts;
}
```

---

## Why Open-Source Visual Sandboxes Matter

Open-source AI models, open agent harnesses, and inspectable system design sandboxes ensure that **every developer — not just giant enterprises — can master safe, cost-efficient AI engineering**. By making the entire simulation engine, curriculum (`levels.js`), and architecture blueprints open-source with zero proprietary build steps and **$0.00 API token cost**, any educator or developer community can fork **Prompt Paws**, add new open-weight model stations (like local Gemma 4 or Ollama nodes), and teach agentic reliability visually.
