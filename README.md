# Microsoft Agent Framework Demo Guide

This repo is a hands-on demo set for Microsoft Agent Framework in DevUI.

It is designed for local learning and walkthroughs, not production deployment.

## What You Get

- Clear examples of orchestration styles (sequential, concurrent, handoff, group chat, magentic)
- A memory + grounding example with optional persistence across conversations
- A practical demo flow you can run in order

## Quick Start

Run these commands from the workspace root:

```bash
pip install -r requirements.txt
az login
devui --no-auth
```

Before launching DevUI, copy settings from `.env.example` into `.env` and fill in your own values.

## DevUI Input Format

When DevUI asks for Structured Data, use:

1. `role`: `user`
2. `contents`: your prompt text

Example:

- `role`: `user`
- `contents`: `We need a one-paragraph launch update for a new budget-friendly e-bike.`

## Recommended Demo Order

Use this sequence for a smooth story:

1. `01_sequential_orchestration.py`
2. `02_concurrent_orchestration.py`
3. `03_handoff_orchestration.py`
4. `04_group_chat_orchestration.py`
5. `05_magentic_orchestration.py`
6. `06_memory_and_grounding.py`

## Example Cheat Sheet

### 1) Sequential Orchestration

**File:** `01_sequential_orchestration.py`

**What it demonstrates**

Two agents run in order:

- `intake_agent` creates a compact summary
- `drafter_agent` turns that summary into polished output

**What to highlight in DevUI**

- Step-by-step execution is predictable
- Output from step one is passed into step two
- Easy to reason about and debug

**Suggested prompt**

`We need a one-paragraph launch update for a new budget-friendly e-bike.`

### 2) Concurrent Orchestration

**File:** `02_concurrent_orchestration.py`

**What it demonstrates**

Multiple specialists analyze the same prompt in parallel.

**What to highlight in DevUI**

- Commercial, legal, and technical perspectives run independently
- Outputs are collected together at the end
- Value is diversity of viewpoints, not only speed

**Suggested prompt**

`Review this budget e-bike launch proposal from commercial, legal, and technical angles: We are excited to launch our new budget-friendly e-bike, designed to make everyday riding more accessible without compromising on comfort, reliability, or style. Built for commuting, errands, and weekend rides, it offers practical range, easy handling, and essential features at a price point that opens the door to more riders. This launch reflects our commitment to affordable mobility and gives customers a smart, approachable way to enjoy the convenience and fun of electric biking.`

### 3) Handoff Orchestration

**File:** `03_handoff_orchestration.py`

**What it demonstrates**

`triage_agent` routes the request to a specialist agent.

**What to highlight in DevUI**

- `triage_agent` speaks first
- Responsibility transfers to `billing_agent` or `technical_agent`
- Context is carried forward with the handoff

**Suggested sequence**

1. `My e-bike order EBIKE-123 arrived with a dead battery and I want to understand the return options.`
2. `Use this triage_agent output: route to billing_agent because the user is asking about returns and order handling. Continue with the same issue: My e-bike order EBIKE-123 arrived with a dead battery and I want to understand the return options.`

### 4) Group Chat Orchestration

**File:** `04_group_chat_orchestration.py`

**What it demonstrates**

Two agents collaborate in a shared conversation.

**What to highlight in DevUI**

- Both agents see prior turns
- Each turn refines the previous result
- Collaboration is more iterative than handoff

**Suggested prompt**

`Draft a short launch tagline for a new budget-friendly e-bike.`

### 5) Magentic Orchestration

**File:** `05_magentic_orchestration.py`

**What it demonstrates**

A manager agent dynamically coordinates specialists.

**What to highlight in DevUI**

- The manager decides what happens next based on progress
- Work can span multiple rounds
- More flexible than fixed workflows, but harder to trace

**Suggested prompt**

`Summarize the main enterprise benefits of Microsoft Agent Framework for a local devcontainer demo.`

### 6) Memory and Grounding

**File:** `06_memory_and_grounding.py`

**What it demonstrates**

Memory + personalization with:

- `ContextProvider`
- `InMemoryHistoryProvider`
- Optional JSON persistence for cross-conversation recall

**What to highlight in DevUI**

- The agent asks for the user name when unknown
- Name is saved in session and optionally persisted
- Later turns personalize responses
- A new thread can still recall saved identity

**Suggested sequence**

1. `Hello, I need help with my e-bike order.`
2. Agent asks for user name.
3. `My name is Alice.`
4. Agent acknowledges and stores the name.
5. `What is the status of my order?`
6. Start a new conversation thread.
7. `What is my name?`

Expected behavior: agent recalls `Alice`.

## Tips for a Better Demo

- Keep prompts short and concrete
- Focus on who speaks, when, and why
- Compare trace/event flow between patterns
- Re-run the same prompt across patterns to show differences quickly
