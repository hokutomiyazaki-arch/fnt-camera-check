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
    H |= set(re.findall(r"\['\w+', '([^']+)', (?:\d+\]|null\]|bs =>)", s))   # 表情の合図
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
    nsub = '3秒後に鼻先の位置を確定します。「ピッ」と鳴ったら目を開ける'   # 鼻先を合わせる①②の説明（2026-10-18）
    for h in ['目をつぶって。顔を中心に戻せるかのテストです', '目をつぶって。覚えた点に顔を向けられるかのテストです']:
        E.add(h + '。' + nsub)
    E.add('次は目を閉じて同じ点へ。3秒後に鼻先の位置を確定します')
    E |= {'次は。' + k for k in ['よこ', 'たて', 'ななめ（右上↔左下）', 'ななめ（左上↔右下）']}
    E |= {'見つめたまま。あと10秒', '見つめたまま。あと4秒'}
    E |= {f'{d}へ。倒せるところまで' for d in ('右', '左')}   # 首を横に倒す（2026-10-16）
    for w in ['顔が見つかりませんでした', '顔が見えている時間が短すぎました', '目が見えている時間が短すぎました', '目の位置を読み取れませんでした', '目の動きを読み取れませんでした']:
        E.add(f'{w}。顔を画面に入れて、もう一度どうぞ')
    E |= {'スマホを顔に近づけて。画面で見える範囲がほぼ埋まるくらい', 'その近さのまま'}   # 線をまっすぐにする（svvMsg）の前の「近づけて」
    E |= {'OK。下の「次へ」を押してください', '顔の位置を合わせます。顔が見つかりません。カメラに顔を向けてください', 'スマホをまっすぐ縦に'}
    for a in ['', 'もう少し近づいて', 'もう少し離れて']:
        for b in ['', '顔をまっすぐ正面に', '首のかしげをまっすぐに']:
            for c in ['', '暗いです。明るい所へ']:
                x = '。'.join(v for v in (a, b, c) if v)
                if x: E.add('顔の位置を合わせます。' + x)
    E |= {'顔が見えません。スマホを顔の正面に持ってください',
          'OK ✓。この近さのまま。白い線が緑の帯に入ればOK',
          'スマホを。顔に近づけて。白い線が緑の帯に入ればOK',
          '少し。離して。白い線が緑の帯に入ればOK',
          '戻してOK'}
    nt8 = '黄色い点が1周8秒で進むので、鼻先（赤い点）で追いかけてください。3周したら「反対回り」の合図で逆向きに3周。肩は動かさず首だけで。痛みが出たら止めてください'
    E |= {'白い8の字の線を。鼻先でなぞります。' + nt8, '練習おわり。次は本番です。' + nt8,
          '白い線の上を動く点を。鼻先で追います。はじめに左右へ3往復、次に上下へ3往復。1往復6秒です。肩は動かさず首だけで。痛みが出たら止めてください'}
    # 2026-10-14 足した2つ（口の開け方・肩すくめ）
    E |= {'ゆっくり開けて', 'ゆっくり閉じて', '口を閉じて。3', 'すくめたままキープ', 'あと20秒', 'あと5秒',
          'OK ✓。両肩が見えました。下の「始める」を押してください',
          'スマホを持ったまま。腕を伸ばして。顔と両肩を映してください。顔と両肩が画面に入ればOK（青い線が両肩をつなぎます）。そのあと肩をすくめて30秒キープします。スマホはなるべく動かさず、顔はまっすぐ前のまま'}
    # 2026-10-14 足した VOR（頭を動かして点を見つめる）
    E |= {'真ん中の点を見つめたまま。光った線を鼻先で。素早くなぞって戻します。スマホは動かさずに持ったまま。黄色く光った線を、鼻先で素早くなぞって真ん中へ戻します。その間ずっと、目は真ん中の点を見つめたまま。動かす幅は小さくて大丈夫です。全部で24回。首に痛みが出たら止めてください',
          '点を見つめたまま。3'}
    # 2026-10-15 指示を最小限・大きくした（宮崎さん）・VOR は向きを字と声で・寄り目は3回・肩は付け根で
    E |= {'動く点を鼻先で追います。左右、次に上下', '動く点を鼻先で追います', '練習おわり。次は本番です',
          '目はずっと点を見たまま。3', '近づけて', '戻して', '右', '左', '上', '下', '右上', '左上', '右下', '左下',
          'OK ✓。「始める」を押す', '顔と首の付け根が。映るように持つ。肩の端は入らなくてOK'}
    # 2026-10-15 舌のキープ・流れる縞（OKN）
    E |= {'そのままキープ', '縞が右へ流れます。ぼんやり見る', '次は左へ流れます。ぼんやり見る'}
    E |= {'線をまっすぐ縦に。スマホを傾けて合わせ、止める。1回10秒', '次はまっすぐ横に。スマホを傾けて合わせ、止める。1回10秒', '真ん中に戻す', '真ん中'}   # 線をまっすぐにする（svvMsg は cue ではないので拾われない）
    E |= {'目を開けて'}   # 鼻先を合わせる（2026-10-18）：ズレの数字は字だけ、声は「目を開けて」
    for w in ['両肩が見えている時間が短すぎました', '肩が見えている時間が短すぎました', '口の開き方を読み取れませんでした']:
        E.add(f'{w}。顔を画面に入れて、もう一度どうぞ')
    return sorted(t for t in (S | E) if t)

YOMI = {'右': 'みぎ', '左': 'ひだり', '上': 'うえ', '下': 'した', '右上': 'みぎうえ', '左上': 'ひだりうえ', '右下': 'みぎした', '左下': 'ひだりした', '真ん中': 'まんなか', '眉間（赤い点）を。黄色い点に合わせて': 'みけん（赤い点）を。黄色い点に合わせて'}   # VOR の向き（1語だけだと読み違えるので、かなで読ませる）

def say_text(t):   # 音にする文。記号は読ませない
    if t in YOMI: return YOMI[t]
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
