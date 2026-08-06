#!/usr/bin/env python3
"""Clean YouTube auto-generated VTT into a single plain-text transcript.

YouTube's auto-captions emit progressive-overlap cues: each cue carries the
previous cue's words PLUS the new tail. Raw concatenation produces a garbage
transcript where words repeat 3x back-to-back.

Real session example (Denis Shatalin PACE video, 30:35 monologue):
  - Raw cues concatenated:        71,071 chars (broken)
  - Consecutive-dup cue removal:   47,384 chars (still broken)
  - After this script:            23,541 chars / 4,411 words (correct)

Two passes:
  1. Macro-repeat detector — finds repeated 4-gram windows within 30 words and
     removes the duplicate.
  2. Inline phrase-collapse — folds back-to-back identical phrases (2-10 words)
     and consecutive-identical-word bursts ("and and and" -> "and").

Usage:
    python3 clean_auto_subs.py VIDEO_ID.en.vtt --out-dir ./transcripts/ --youtube-id VIDEO_ID

Outputs into --out-dir:
    transcript.txt               # clean plain text (canonical)
    transcript_timestamped.txt   # all cues with timestamps, consecutive dups collapsed
    transcript_paragraphs.txt    # plain text re-chunked into ~700-char paragraphs
"""
import argparse
import re
import sys
from pathlib import Path


def parse_vtt(text: str):
    """Parse VTT text into list of (timestamp_str, words_list) tuples."""
    blocks = re.split(r"\n\n+", text.strip())
    ts_re = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> ")
    cues = []
    for block in blocks:
        if block.startswith("WEBVTT") or block.startswith("Kind:"):
            continue
        lines = block.split("\n")
        if not lines:
            continue
        m = ts_re.search(lines[0])
        if not m:
            continue
        ts = m.group(1)
        text_block = " ".join(lines[1:])
        text_block = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", text_block)
        text_block = re.sub(r"</?c>", "", text_block)
        text_block = re.sub(r"</?[^>]+>", "", text_block)
        text_block = re.sub(r"\s+", " ", text_block).strip()
        if text_block:
            cues.append((ts, text_block.split(" ")))
    return cues


def collapse_macro_repeats(s: str) -> str:
    """Find repeated 4-gram windows within 30 words and remove the duplicate.

    Operates on whitespace-tokenized words. Returns the cleaned string.
    """
    changed = True
    passes = 0
    while changed and passes < 50:
        changed = False
        passes += 1
        words = s.split(" ")
        n = len(words)
        new_words = []
        i = 0
        while i < n:
            if i + 4 <= n:
                gram = " ".join(words[i:i+4])
                # Look forward within 30 words
                j = i + 4
                limit = min(n, i + 30)
                found_at = -1
                while j + 4 <= limit:
                    cand = " ".join(words[j:j+4])
                    if cand == gram:
                        found_at = j
                        break
                    j += 1
                if found_at > 0:
                    blk_len = found_at - i
                    new_words.extend(words[i:i+blk_len])
                    i = found_at + blk_len
                    changed = True
                    continue
            new_words.append(words[i])
            i += 1
        new_s = " ".join(new_words)
        if new_s != s:
            s = new_s
            changed = True
        else:
            break
    return re.sub(r"\s+", " ", s).strip()


def collapse_inline_repeats(s: str, max_phrase_words: int = 10) -> str:
    """Collapse consecutive-identical-word bursts and back-to-back phrase dups."""
    # "and and and" -> "and"; "from the from the" -> "from the"
    s = re.sub(r"\b(\w+)(\s+\1\b){2,}", r"\1", s)
    s = re.sub(r"\b(\w+)(\s+\1\b)", r"\1", s)

    # 2-N word phrase repeats that are immediately adjacent
    out = []
    i = 0
    words = s.split(" ")
    n = len(words)
    while i < n:
        matched = False
        for plen in range(min(max_phrase_words, n - i), 1, -1):
            phrase = " ".join(words[i:i+plen])
            after = " ".join(words[i+plen:i+2*plen])
            if phrase == after:
                out.append(phrase)
                i += 2 * plen
                matched = True
                break
        if not matched:
            out.append(words[i])
            i += 1
    return " ".join(out)


def cut_trailing_dup(s: str) -> str:
    """Detect and cut trailing 200-40 char blocks that re-appear earlier."""
    if len(s) < 200:
        return s
    for cut in (200, 150, 100, 80, 60, 40):
        if len(s) <= cut:
            continue
        tail = s[-cut:]
        head = s[:-cut]
        if tail in head:
            s = head
    return s


def chunk_paragraphs(text: str, every: int = 700) -> str:
    """Re-chunk plain text into ~700-char paragraph blocks on sentence boundaries."""
    out = []
    cur = ""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    for sent in sentences:
        if len(cur) + len(sent) + 1 > every and cur:
            out.append(cur.strip())
            cur = sent
        else:
            cur = (cur + " " + sent).strip() if cur else sent
    if cur:
        out.append(cur.strip())
    return "\n\n".join(out)


def sanitize_punct(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s([,.!?;:])", r"\1", s)
    return s


def main():
    p = argparse.ArgumentParser(description="Clean YouTube auto-sub VTT into plain text transcript.")
    p.add_argument("vtt", help="Input .vtt file from yt-dlp")
    p.add_argument("--out-dir", required=True, help="Output directory")
    p.add_argument("--youtube-id", default=None, help="Video ID (used for output naming if provided)")
    p.add_argument("--verbose", action="store_true", help="Print pass-level stats")
    args = p.parse_args()

    src = Path(args.vtt)
    if not src.exists():
        print(f"error: {src} not found", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw = src.read_text(encoding="utf-8")
    cues = parse_vtt(raw)
    if args.verbose:
        print(f"cues in: {len(cues)}")

    # Drop consecutive-identical cues
    dedup_cues = []
    prev = None
    for ts, words in cues:
        text = " ".join(words)
        if text == prev:
            continue
        dedup_cues.append((ts, words))
        prev = text
    if args.verbose:
        print(f"cues after consecutive-dup removal: {len(dedup_cues)}")

    # Plain text
    joined = " ".join(" ".join(w) for _, w in dedup_cues)
    joined = re.sub(r"\s+", " ", joined).strip()

    # Pass 1: macro-repeat collapse
    s1 = collapse_macro_repeats(joined)
    if args.verbose:
        print(f"chars after macro-repeat collapse: {len(s1)}")

    # Pass 2: inline phrase-collapse
    s2 = collapse_inline_repeats(s1)
    if args.verbose:
        print(f"chars after inline phrase-collapse: {len(s2)}")

    # Pass 3: trailing-dup cut
    s3 = cut_trailing_dup(s2)

    # Final sanitization
    plain = sanitize_punct(s3)

    # Write outputs
    (out_dir / "transcript.txt").write_text(plain, encoding="utf-8")
    ts_lines = [f"[{ts}] {' '.join(w)}" for ts, w in dedup_cues]
    (out_dir / "transcript_timestamped.txt").write_text("\n".join(ts_lines), encoding="utf-8")
    (out_dir / "transcript_paragraphs.txt").write_text(chunk_paragraphs(plain), encoding="utf-8")

    print(f"chars (plain): {len(plain)}")
    print(f"words (plain): {len(plain.split())}")
    print(f"cues after dedup: {len(dedup_cues)}")
    print(f"outputs: {out_dir}/transcript.txt, transcript_timestamped.txt, transcript_paragraphs.txt")


if __name__ == "__main__":
    main()