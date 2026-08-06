# Higgsfield Image Generation for App Assets

Proven workflow for generating cinematic app imagery at scale.

## Batch Pattern (3 parallel terminal calls)

```bash
higgsfield generate create gpt_image_2 --prompt "..." --aspect_ratio 16:9 --resolution 2k --wait --wait-timeout 5m
higgsfield generate create gpt_image_2 --prompt "..." --aspect_ratio 4:3 --resolution 2k --wait --wait-timeout 5m
higgsfield generate create gpt_image_2 --prompt "..." --aspect_ratio 1:1 --resolution 2k --wait --wait-timeout 5m
```

## Prompt Template
```
Cinematic [SCENE DESCRIPTION]. [SUBJECT ACTION/STATE], [LIGHTING DESCRIPTION] with [COLOR] tones. [ENVIRONMENT DETAILS]. Professional [TYPE] photography, 8K. No text.
```

## Download + Register
```bash
cd /path/to/app/assets/imagery
curl -sL "URL" -o filename.png
# Register in pubspec.yaml under flutter > assets
```

## Failure Handling
- 502 errors: retry with same prompt
- Timeouts: use `--wait-timeout 5m` (default 120s is too short)
- If fails twice: skip and generate others

## Cost
~2-5 credits per image at 2K. Budget 50-100 credits for 15-20 images.
