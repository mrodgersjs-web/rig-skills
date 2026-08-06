# Key Principles — Agentic Coding (Ofri Wolfus, agenticoding.ai)

Source: https://agenticoding.ai/docs (open source, Tier 2)
License: Free and open source

## The Operator Mindset
- AI agents aren't teammates — they're power tools
- You're not managing a junior dev — you're operating precision instruments
- The agent executes; the operator owns acceptance
- Agents are amplifiers — good or bad, they compound what exists
- You are the circuit breaker — every accepted line becomes pattern context

## The Four-Phase Workflow
Research → Plan → Execute → Validate
- **Research (Grounding)**: Inject reality into context before generation
- **Plan**: Two modes — Exploration (unclear solution) vs Exact (known solution)
- **Execute**: Supervised (learning) vs Autonomous (YOLO — real productivity)
- **Validate**: Iterate (fixable gaps) vs Regenerate (fundamental mismatch)

## Context Engineering
- The context window is the agent's entire world
- Everything is just text flowing through a single text buffer
- The LLM is completely stateless — no hidden memory
- Control what's in the window = control behavior
- Fresh context = unbiased analysis (key for code review)

## Grounding by Codebase Scale
| Scale | Tools |
|-------|-------|
| <10K LOC | Agentic search (Grep, Read, Glob) |
| 10-100K LOC | Semantic search or Explore agent |
| 100K+ LOC | Structured code research (ChunkHound) |

## Tests as Guardrails
- Tests define operational boundaries agents cannot cross
- Write code in Context A, tests in fresh Context B, debug in fresh Context C
- Sociable unit tests > heavily mocked tests
- Sub-30-second smoke test suite for fast iteration
- Green tests ≠ working software — run the actual product

## Fresh-Context Review
- Agent reviewing its own work in same conversation will defend its decisions
- Fresh context provides objective analysis
- Chain-of-Draft (CoD): think step by step, 5 words max per step, final answer after separator
- Stop when findings become trivial nitpicks or agent hallucinates problems

## Evidence-Based Debugging
- "What do you think is wrong?" → "Prove the bug exists, then prove your fix works"
- Closed-loop: BUILD → REPRODUCE → PLACE → INVESTIGATE → VERIFY
- Agents parse whatever logs you give them — don't wait for perfect logging
- Reproduction scripts are trivial for AI to generate

## Spec-Driven Development
- Code is the single source of truth — period
- Specs are temporary scaffolding for the creation process
- DELETE specs after implementation
- Regenerate specs on-demand from code when needed
- HOW knowledge → lives in code. WHY knowledge → decision records.

## Prompting 101
- Prompting is pattern completion, not conversation
- Skip "please" and "thank you" — dilutes signal
- Personas affect vocabulary, not capability
- Avoid negation — LLMs struggle with "NOT"
- LLMs can't do math — have them write code that does

## Project Onboarding
- AGENTS.md = vendor-neutral standard (Copilot, Cursor, Windsurf)
- CLAUDE.md = hierarchical system (Claude Code only)
- Context files give agents "project memory"
- Auto-generate with: ChunkHound code research + ArguSeek web research
- Keep ≤200 lines, focus on AI-specific operations

## Anti-Patterns
- Babysitting one agent in one window
- Starting every session from zero context
- Treating agents as teammates
- Living specs that drift from code
- Heavy mocking (verifies implementation details, not behavior)
- Jumping straight to code without research
- Same-context review (confirmation bias)
