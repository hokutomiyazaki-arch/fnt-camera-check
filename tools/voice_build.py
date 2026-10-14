#!/usr/bin/env python3
"""アプリが読み上げる文を、ElevenLabs で前もって音声にして voice/ に置く（2026-10-14）。

  python3 tools/voice_build.py          # 足りない分だけ作る（作る前に字数とクレジットを出す）
  python3 tools/voice_build.py --dry    # 一覧と字数だけ

- 読み上げる文は index.html から拾う（cue・near・fail の文字列、質問、表情の合図）＋ 数字が入る文は下の EXTRA で全部並べる
- 文 → 鍵（空白と「。」を抜いたもの）→ ファイル名 は voice/index.json。index.html の vkey() と同じ規則
- 無い文は、アプリが端末の声で読む（止まらない）。スタッフ表示ではコンソールに「音声ファイルなし」と出るので、それを EXTRA に足して走らせ直す
- 声と型は AI音読（skill ai-onodoku）で決めたもの：eleven_v3・リョウ。鍵は ~/.zshenv の ELEVENLABS_API_KEY（値は出さない）
"""
import hashlib, json, os, re, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'voice'
API = 'https://api.elevenlabs.io'
MODEL = 'eleven_v3'
VOICE = '1cOJcfrlMmUCGpeJbXg9'   # リョウ

def to_speech(h):   # index.html の toSpeech() と同じ変換
    t = re.sub(r'<br\s*/?>', '。', h).replace('<small>', '。')
    t = re.sub(r'<button.*?</button>', '', t, flags=re.S)
    t = re.sub(r'<[^>]+>', '', t)
    t = t.replace('「∞」', '8の字').replace('∞', '8の字')
    t = re.sub(r'(\d+)(周目|往復目)／\d+', r'\1\2', t).replace('／', '、')
    t = re.sub(r'\s+', ' ', t); t = re.sub(r'。+', '。', t); t = re.sub(r'^。|。$', '', t)
    return t.strip()

def vkey(t): return re.sub(r'[\s。]', '', t)

def texts():
    s = (ROOT / 'index.html').read_text(encoding='utf-8')
    H = set()
    for m in re.finditer(r"\b(?:cue|near|fail)\((?:[a-zA-Z]+,\s*)?(['`])((?:(?!\1).)*)\1", s, re.S):
        if '${' not in m.group(2): H.add(m.group(2))
    H |= set(re.findall(r"q: '([^']+)'", s))
    H |= set(re.findall(r"\['\w+', '([^']+)', \d+\]", s))   # 表情の合図
    S = {to_speech(h) for h in H}
    E = set()
    # 数字・組み合わせが入る文（index.html の該当箇所と合わせる）
    E |= {str(i) for i in range(1, 11)} | {f'{i}秒' for i in range(1, 11)}
    E |= {'白い線の上に。鼻先を置いて。3', '舌を出す準備。3', '鼻先を8の字の真ん中に置いて。矢印の向きへ動き出します 3', '点を見たまま 3'}
    for p in ['', '練習・']:
        for d in ['', '反対回り・']:
            E |= {f'{p}{d}{i}周目' for i in (1, 2, 3)} | {f'{p}{d}{i}周目。顔が見えません' for i in (1, 2, 3)}
    E |= {f'{i}周目' for i in (2, 3)}
    for a in ['左右', '上下']:
        E |= {f'{a}・{i}往復目' for i in (1, 2, 3)} | {f'{a}・{i}往復目。顔が見えません' for i in (1, 2, 3)}
    E |= {f'{i}往復目' for i in (2, 3)}
    E |= {'次は。' + k for k in ['よこ', 'たて', 'ななめ（右上↔左下）', 'ななめ（左上↔右下）']}
    E |= {'見つめたまま。あと10秒', '見つめたまま。あと4秒'}
    for w in ['顔が見つかりませんでした', '顔が見えている時間が短すぎました', '目が見えている時間が短すぎました', '目の位置を読み取れませんでした', '目の動きを読み取れませんでした']:
        E.add(f'{w}。顔を画面に入れて、もう一度どうぞ')
    E |= {'OK。下の「次へ」を押してください', '顔の位置を合わせます。顔が見つかりません。カメラに顔を向けてください', 'スマホをまっすぐ縦に'}
    for a in ['', 'もう少し近づいて', 'もう少し離れて']:
        for b in ['', '顔をまっすぐ正面に', '首のかしげをまっすぐに']:
            for c in ['', '暗いです。明るい所へ']:
                x = '。'.join(v for v in (a, b, c) if v)
                if x: E.add('顔の位置を合わせます。' + x)
    E |= {'顔が見えません。スマホを顔の正面に持ってください',
          'OK ✓。この近さのまま。目が大きく映るまで近づけます（目安：顔から20〜25cm）。緑の帯に白い線が入ればOK',
          'スマホを。顔に近づけて。目が大きく映るまで近づけます（目安：顔から20〜25cm）。緑の帯に白い線が入ればOK',
          '少し。離して。目が大きく映るまで近づけます（目安：顔から20〜25cm）。緑の帯に白い線が入ればOK',
          '戻してOK'}
    nt8 = '黄色い点が1周8秒で進むので、鼻先（赤い点）で追いかけてください。3周したら「反対回り」の合図で逆向きに3周。肩は動かさず首だけで。痛みが出たら止めてください'
    E |= {'白い8の字の線を。鼻先でなぞります。' + nt8, '練習おわり。次は本番です。' + nt8,
          '白い線の上を動く点を。鼻先で追います。はじめに左右へ3往復、次に上下へ3往復。1往復6秒です。肩は動かさず首だけで。痛みが出たら止めてください'}
    # 2026-10-14 足した3つ（口の開け方・のどの奥・肩すくめ）
    E |= {'ゆっくり開けて', 'ゆっくり閉じて', '口を閉じて。3', '大きく口を開けて。3', 'すくめたままキープ', 'あと20秒', 'あと5秒',
          'OK ✓。両肩が見えました。下の「始める」を押してください',
          'スマホを机などに立てて置き。両肩まで映る所まで。下がってください。顔と両肩が画面に入ればOK（青い線が両肩をつなぎます）。そのあと肩をすくめて30秒キープします'}
    for w in ['両肩が見えている時間が短すぎました', '口の開き方を読み取れませんでした', '写真を撮れませんでした', 'カメラを切り替えられませんでした']:
        E.add(f'{w}。顔を画面に入れて、もう一度どうぞ')
    return sorted(t for t in (S | E) if t)

def say_text(t):   # 音にする文。記号は読ませない
    t = re.sub(r'[①②③④]\s*', '', t).replace('3・2・1', '3、2、1').replace(' → ', '、').replace('→', '、')
    return t.replace('✓', '').replace('↔', 'と').replace('〜', 'から').replace('cm', 'センチ').replace('OK', 'オーケー').strip('。 ')

def tts(text, path):
    k = os.environ.get('ELEVENLABS_API_KEY') or sys.exit('ELEVENLABS_API_KEY が無い（~/.zshenv）')
    body = json.dumps({'text': text, 'model_id': MODEL, 'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}}).encode()
    req = urllib.request.Request(f'{API}/v1/text-to-speech/{VOICE}?output_format=mp3_22050_32', data=body,
                                 headers={'xi-api-key': k, 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as r: path.write_bytes(r.read())

def main():
    T = texts(); OUT.mkdir(exist_ok=True)
    idx_f = OUT / 'index.json'; idx = json.loads(idx_f.read_text()) if idx_f.exists() else {}
    todo = []
    for t in T:
        k = vkey(t); f = hashlib.md5(say_text(t).encode()).hexdigest()[:12] + '.mp3'
        idx[k] = f
        if not (OUT / f).exists(): todo.append((t, f))
    n = sum(len(say_text(t)) for t, _ in todo)
    print(f'文 {len(T)}・作るもの {len(todo)}・{n}字（eleven_v3 は約 {n // 2} クレジット）')
    if '--dry' in sys.argv:
        for t, _ in todo: print('  ', t)
        return
    for i, (t, f) in enumerate(todo, 1):
        tts(say_text(t), OUT / f); print(f'  {i}/{len(todo)} {t[:40]}')
    if not (OUT / 'unlock.mp3').exists():
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=22050:cl=mono', '-t', '0.2', '-b:a', '32k', str(OUT / 'unlock.mp3')], check=True)
    idx_f.write_text(json.dumps(dict(sorted(idx.items())), ensure_ascii=False, indent=0))
    print('voice/index.json', len(idx))

main()
