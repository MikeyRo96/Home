---
videomd: 1
name: test3
description: '“test3”. Made with (inferred): code / template render 100%'
source:
  file: test3.mp4
  sha256: e96f51b1dafaf20b6b68bf8ae8ee94a5b135d16ce0cefd701a6fc41e1ba4e076
  duration: 9.0
  size: 640x360
  fps: 25.0
  aspect: '16:9'
shots: 3
lang: en
made_mix:
  code_render: 1.0
confidence: 0.861
readers:
- tools
open_questions: 2
generator:
  name: rea-video
  version: 0.1.0
---

# test3.mp4

**Verdict** (inferred): code / template render 100%
**Made with** (inferred, by duration): code / template render 100%
**Remake**: code render / screen capture 3 shots → 1 code project

## Next steps

- No VLM ran: if you can see images, review first: `rea-video review <this dir>` → fill `review_answers.json` → `rea-video apply-review <this dir>`
- Remake: Capsule Cinema does the generation, assembly and checks. `rea-video remake <this dir>` hands over to it, does what can be done automatically and keeps the original elsewhere; `remake/status.md` says per shot what is left. Add incoming clips to `remake/mine.json` and run it again
- Code-rendered shots are best rebuilt in code by a strong coding model (such as Claude Opus 5.5 or later, or the Gemini 4 series), optionally on HyperFrames or Remotion, from the rhythm and key frames in `video/rhythm.md`; `rea-video code-remake <this dir>` only makes a quick draft for particles / data-visualisation pictures

## Open questions

- The VLM did not run (No VLM; live action / AI / 3D are told apart from pixel statistics only, so confidence is limited. An agent that can see images: run rea-vi…
- No AI listened to the soundtrack: real voice versus TTS is inferred from the waveform; the effects were picked off the mix where the sound jumps, so plosives an…

## Map

Read this page first; for detail, open only the file you need. Each line is `path | ~tokens | what is in it · when to read it`; paths are relative to this directory.

```videomd-map
video/timeline.md | 293 | Timeline: one line per shot · what a stretch says, which shots need review, how a shot was made
video/content.md | 75 | Content and structure · what it says, the narrative line, structure, the script
video/cast.md | 32 | Cast, scenes and props · reference images for characters, first-frame prompts
video/sound.md | 84 | Sound · voice, music, sound effects, beats and sources
video/rhythm.md | 80 | Rhythm and key frames · when cuts and transitions happen, shot lengths, the change curve, key frames of each shot
video/remake.md | 1261 | Remake plan · generation units, shoots, code builds, real material to collect, acting and emotion
video/shots/*.md | 389 | Per-shot detail, tokens per file on average · checking one shot: what is seen, the inference and its basis, prompts, frames
breakdown.json | 6836 | Full raw data · for programs; a model rarely needs it
shots/ | - | contact sheet, first and last frame of each shot · checking by eye
storyboard.jpg | - | storyboard of the whole video · the whole video at a glance
stems/ | - | voice, music and effects stems · listening, remaking the sound
frames/ | - | picture scenes: full-size frames, the drawn layer cut out and sampled, measurements · remaking rendered pictures
audio.png | - | waveform and beat chart · seeing the rhythm
```

## How to read

- One shot per line: `#<n> start-end (s) | key value | …`. A key ending in `~` is the tools' inference; keys without it are visible on screen or measured directly.
- `story` job in the story and the point · `seen` what is on screen · `act` acting (emotion, strength, face) · `camera` camera move · `overlay` overlays · `made~` how it was made (inferred) · `material~` where the material came from (inferred) · `remake` remake route · `flag` needs a second look
- Full detail for a shot is in `video/shots/<n>.md` (e.g. `video/shots/07.md`).
- What is “seen” can be checked against the frames; what is “inferred” is the tools' and image readers' judgement, with the basis in each shot file. When they disagree, trust the frames.
