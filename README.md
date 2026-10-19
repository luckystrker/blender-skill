# Blender Agent Skill — a production pipeline for AI-built 3D models

A battle-tested workflow and toolkit for AI agents (Claude Code, Codex, Cursor, Pi, …) that build 3D models in Blender through the [MCP](https://modelcontextprotocol.io/) bridge.

Built in real sessions: every rule below exists because something broke without it. The skill text is written in Russian (it is the working language of the family assistant it was built for); the tooling and README are English-friendly.

## What's inside

```
skills/blender/SKILL.md                      the agent skill: phases, geometry rules, pitfalls
skills/blender/references/code-patterns.md   copy-paste snippets (lathe, beams, verify, studio)
skills/blender/scripts/blib.py               shared Python library for execute_blender_code
skills/blender/scripts/qa_check.py           CLI audit: objects, sizes, transforms, materials
skills/blender/scripts/studio.py             studio lighting / camera / floor setup
examples/cup.py                              full walkthrough: a decorated ceramic mug
examples/vase.py                             minimal lathe example (a vase in 30 lines)
evals/test-prompts.md                        test prompts + expected behaviour (eval set)
```

## The pipeline in one breath

1. **Understand** — describe the shape with simple primitives; ask when unsure.
2. **Connection map** before any code: what touches what, on which axis, ≥5 mm overlap.
3. **Assets first** — search Poly Haven (`search_assets`); build by hand only what's unique.
4. **Geometry rules** (`tools/blib.py` enforces them):
   - cubes are created with `size=2`, so `scale` *is* the half-extent;
   - directional parts are `make_beam(start, end)` — never rotated cylinders;
   - `transform_apply` immediately after every scale, inside loops;
   - spanning dimensions are derived from `verify_bounds()`, never guessed.
5. **Advanced tools**: `lathe()` (surfaces of revolution via SCREW+SOLIDIFY — mugs, vases),
   `curve_tube()` (Bezier curves with a ribbon profile — handles), `shrinkwrap_to()`
   (wrap flat text/decals onto curved surfaces).
6. **Verify from every angle** — `look` from 4 sides; render every side where important
   details live. A 3/4 beauty shot is not a verification.
7. **Critic pass** — compare with the reference, list 3–5 differences, fix them.
   For important models, hand the renders + reference to a *separate* agent (builder ≠ critic).
8. **QA** — `audit_all()`, bounds assertions, preview render.
9. **Export** — `.glb` with `use_selection=True`, thumbnail, manifest.

**Rule of thumb:** never report to a human until you have looked at the renders of all sides
yourself. Blind spots are real: in one session the buttons of a toaster had silently flown
0.15 m away from the body, and a 3/4 render never showed it.

## Quick start

```bash
# 1. Blender + MCP addon (https://github.com/seehiong/mcp-for-blender or any MCP-for-Blender)
uvx mcp-for-blender setup

# 2. In your MCP client config
{ "mcpServers": { "blender": { "command": "uvx", "args": ["mcp-for-blender"] } } }
```

Then, inside `execute_blender_code`:

```python
exec(open("skills/blender/scripts/blib.py").read())          # load the library (materials, lathe, curve_tube, …)
```

and open `skills/blender/SKILL.md` as the agent skill (drop it into your agent's `skills/blender/`).

## Examples

* `examples/vase.py` — the smallest possible "professional" result: a smooth hollow vase
  from a 20-point profile in ~30 lines.
* `examples/cup.py` — a full ceramic mug: lathe body, Bezier-ribbon handle, two bands of
  64 printed stripes, text laid onto the cone with Shrinkwrap, studio light, GLB export.

## Credits & prior art

This pipeline stands on the shoulders of:

- [ProfRino/Blender-MCP-Assembly-Skill](https://github.com/ProfRino/Blender-MCP-Assembly-Skill) — connection maps, `size=2`, beams, verify/audit.
- [jithinolickal/blender](https://github.com/jithinolickal/blender) — design loop, milestones, multi-angle verification.
- [seehiong/blender-mcp-community](https://github.com/seehiong/blender-mcp-community) — the lathe/SCREW pipeline.
- [StraySpark's Blender MCP guide](https://www.strayspark.studio/blog/blender-mcp-ai-assisted-3d-modeling-step-by-step-2026) — the three hard limits and the visual loop.
- SceneCraft (scene graphs before coordinates) and Fable Cities (separate builder/critic roles).

## License

MIT — see `LICENSE`.
