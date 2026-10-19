#!/bin/zsh
# 1回だけ動く：ElevenLabs の月の文字数が戻ったら（2026-10-22 13:08）、お客さん用のワークの声（voice_f）を作って公開する
# launchd: ~/Library/LaunchAgents/jp.legrandchariot.fnt-camera-check.voice-1022.plist（10/22 14:00・10/23 8:00・10/24 8:00）。終わったら自分を外す
# DRY=1 で、声を作らずに流れだけ確かめる
set -u
source ~/.zshenv
cd /Users/miyazakihokuto/FNT-Apps/fnt-camera-check || exit 1
L=jp.legrandchariot.fnt-camera-check.voice-1022
echo "== $(date '+%F %T')"
left=$(curl -s -H "xi-api-key: $ELEVENLABS_API_KEY" https://api.elevenlabs.io/v1/user/subscription | /opt/homebrew/bin/python3 -c "import json,sys;d=json.load(sys.stdin);print(d['character_limit']-d['character_count'])")
echo "残り文字数: $left"
if [ -z "$left" ] || [ "$left" -lt 400 ]; then echo "まだ戻っていない。次の回に回す"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then /opt/homebrew/bin/python3 tools/voice_build.py --funnel --dry | tail -3; echo "DRY 終わり"; exit 0; fi
/opt/homebrew/bin/python3 tools/voice_build.py --funnel || { echo "作成に失敗"; exit 1; }
rest=$(/opt/homebrew/bin/python3 tools/voice_build.py --funnel --dry | grep -c "^  ")
git add voice_f
if git diff --cached --quiet; then echo "足すファイルなし"; else
  git commit -q -m "ワーク（寄り目・鼻先で円）の声を女性の声で足す

10/19 に ElevenLabs の残りが0で作れず、端末の声で読んでいた分。月の文字数が戻った 10/22 に launchd で作った

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q && echo "push した"
fi
echo "dry の残り行: $rest"
launchctl bootout gui/$(id -u)/$L 2>/dev/null; mv ~/Library/LaunchAgents/$L.plist ~/Library/LaunchAgents/_retired/ 2>/dev/null; echo "自分を外した"
