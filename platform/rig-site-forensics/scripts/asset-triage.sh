#!/usr/bin/env bash
# asset-triage.sh — Diagnose "live site has 404 assets" by tier.
# Run from the site root (e.g. ~/Developer/<repo>/site-v2).
#
# Tiers:
#   1. Right project responding?  (content-type oracle)
#   2. Apex DNS healthy?
#   3. Bundle contains all referenced assets?
#   4. Where do the originals live (search known archives)?
#   5. Categorize missing-by-fix-type
#
# Usage: ./asset-triage.sh <domain> [site-root]
# Example: ./asset-triage.sh rodgersintelligence.com ~/Developer/rig-design-studio/site-v2

set -uo pipefail

DOMAIN="${1:-}"
SITE_ROOT="${2:-.}"

if [[ -z "$DOMAIN" ]]; then
  echo "Usage: $0 <domain> [site-root]"
  exit 1
fi

echo "════════════════════════════════════════════════════════════"
echo "ASSET TRIAGE for $DOMAIN (root: $SITE_ROOT)"
echo "════════════════════════════════════════════════════════════"

# ─── Tier 1: right project responding? ───
echo ""
echo "─── TIER 1: Is the right project responding? ───"
echo "Testing 3 known assets (one that EXISTS in bundle, one srcset-only, one upload):"
for path in img/agents-130.webp img/deviation-cover.webp uploads/rig-logo.mp4; do
  hdrs=$(curl -sS -I "https://www.${DOMAIN}/${path}" --max-time 10 2>/dev/null || echo "000 TIMEOUT")
  code=$(echo "$hdrs" | head -1 | awk '{print $2}')
  ct=$(echo "$hdrs" | grep -i "^content-type" | head -1 | sed 's/^content-type: //I' | tr -d '\r')
  size=$(echo "$hdrs" | grep -i "^content-length" | head -1 | sed 's/^content-length: //I' | tr -d '\r')
  marker="OK"
  [[ "$code" != "200" ]] && marker="HTTP_ERR"
  [[ "$ct" == text/html* ]] && marker="WRONG_PROJECT"
  printf "  [%s] %-12s code=%s ct=%-35s bytes=%-8s %s\n" "$marker" "$path" "$code" "$ct" "${size:-?}"
done
echo ""
echo "If markers say WRONG_PROJECT — STOP. Fix DNS / domain routing first."

# ─── Tier 2: apex DNS healthy? ───
echo ""
echo "─── TIER 2: Apex DNS health ───"
apex_ip=$(dig +short "$DOMAIN" @1.1.1.1 2>/dev/null | head -1)
www_ip=$(dig +short "www.$DOMAIN" @1.1.1.1 2>/dev/null | head -1)
echo "  apex A: $apex_ip"
echo "  www   A: $www_ip"
echo "  apex HTTP status:"
curl -sS -o /dev/null -w "    %{http_code}\n" --max-time 10 "https://${DOMAIN}/" 2>&1 | head -1
echo "  apex via browser workaround (if curl fails):"
echo "    browser_navigate(url=\"https://${DOMAIN}/\")"

# ─── Tier 3: bundle completeness ───
echo ""
echo "─── TIER 3: Bundle completeness ───"
ASSET_LIST="/tmp/all_assets.$$.txt"
MISSING_LIST="/tmp/missing_assets.$$.txt"

cd "$SITE_ROOT" || { echo "Cannot cd to $SITE_ROOT"; exit 1; }

grep -rhoE '(src|href|poster|data-src)="[^"]*\.(mp4|webp|png|jpg|jpeg|svg|json|woff2?|ico|pdf|mp3|wav)"' \
  --include='*.html' . 2>/dev/null \
  | sed -E 's/^(src|href|poster|data-src)="//; s/"$//' \
  | sort -u > "$ASSET_LIST"

# Also catch srcset / url() patterns
grep -rhoE 'srcset="[^"]+"' --include='*.html' . 2>/dev/null \
  | sed -E 's/^srcset="//; s/"$//' | tr ',' '\n' \
  | sed -E 's/^[[:space:]]+//; s/[[:space:]].*$//' \
  | sort -u >> "$ASSET_LIST"

grep -rhoE 'url\([^)]+\)' --include='*.html' . 2>/dev/null \
  | sed -E 's/^url\(//; s/\)$//; s/^["\x27]//; s/["\x27]$//' \
  | grep -vE '^(data:|https?://|#)' \
  | sort -u >> "$ASSET_LIST"

sort -u "$ASSET_LIST" -o "$ASSET_LIST"

> "$MISSING_LIST"
while IFS= read -r p; do
  [[ -z "$p" ]] && continue
  [[ "$p" =~ ^(data:|https?://|#|javascript:|mailto:|tel:|\$) ]] && continue
  clean="${p#./}"
  if [[ ! -e "$clean" ]]; then
    echo "MISSING: $p" | tee -a "$MISSING_LIST"
  fi
done < "$ASSET_LIST"

echo ""
echo "Total unique asset references: $(wc -l < "$ASSET_LIST" | tr -d ' ')"
echo "Missing from bundle:           $(wc -l < "$MISSING_LIST" | tr -d ' ')"

# ─── Tier 4: archive search ───
echo ""
echo "─── TIER 4: Searching known archives for missing assets ───"
ARCHIVES=(
  "$HOME/RIG-Inbox/Direct-Transfer/Michaels-MacBook-Pro-2/Home-mikerodgers/Downloads/RIG Website (4)/uploads"
  "$HOME/RIG-Inbox/Direct-Transfer/Michaels-MacBook-Pro-2/Home-mikerodgers/rig-site-assets/stills"
  "$HOME/RIG-Inbox/Direct-Transfer/Michaels-MacBook-Pro-2/Home-mikerodgers/rig-site-assets/reels"
  "$HOME/rigintelligence-repos/rig-site-assets/stills"
  "$HOME/rigintelligence-repos/rig-site-assets/reels"
  "$HOME/Desktop/RIG-Estate-Map/_cf_migrate/mike-rodgers-site/assets"
)

while IFS= read -r line; do
  fname=$(basename "${line#MISSING: }")
  echo ""
  echo "Looking for: $fname"
  found=0
  for archive in "${ARCHIVES[@]}"; do
    [[ ! -d "$archive" ]] && continue
    if [[ -e "$archive/$fname" ]]; then
      sz=$(stat -f%z "$archive/$fname" 2>/dev/null || stat -c%s "$archive/$fname" 2>/dev/null)
      echo "  FOUND  $archive/$fname  (${sz} bytes)"
      found=1
    fi
  done
  # Also check the source repo build dir (often has them in img/ re-named)
  for alt in "$SITE_ROOT/../build/img" "$SITE_ROOT/f1" "$SITE_ROOT/uploads"; do
    [[ ! -d "$alt" ]] && continue
    while IFS= read -r hit; do
      [[ -e "$hit" ]] && echo "  ALT    $hit"
    done < <(find "$alt" -maxdepth 3 -name "$fname" -type f 2>/dev/null)
  done
  [[ $found -eq 0 ]] && echo "  NOT FOUND in known archives — candidate for regenerate"
done < "$MISSING_LIST"

# ─── Tier 5: fix-type categorization ───
echo ""
echo "─── TIER 5: Missing-asset fix-type categorization ───"
echo "(review and assign fix_type per row)"
echo ""
echo "Pattern → fix_type:"
echo "  filename-doesn't-exist + in archive   → copy"
echo "  reference .webp + on-disk .png        → rename | patch-html"
echo "  reference points to f1/...webp only   → symlink-fix | include-f1-in-deploy"
echo "  not found anywhere on disk            → regenerate"
echo "  decorative (srcset, fallback)         → patch-html"

echo ""
echo "════════════════════════════════════════════════════════════"
echo "DONE. Lists saved: $ASSET_LIST, $MISSING_LIST"