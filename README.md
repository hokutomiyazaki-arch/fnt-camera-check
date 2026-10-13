# fnt-camera-check（カメラで5つのチェック・試し版）

スマホやパソコンのカメラで顔の点を読み取って、5つの気づきを数字で出す試しの画面。
**カメラで本当に取れるかを確かめるためのもので、診断アプリの本体ではない。**

- 公開先：https://hokutomiyazaki-arch.github.io/fnt-camera-check/（カメラは https でないと起動しないので GitHub Pages）
- 道具：MediaPipe FaceLandmarker（tasks-vision 1.1.0・CDN）。映像は端末の外へ送らない（端末の中で数字にするだけ）
- 流れ：位置合わせ → ①首の8の字（鼻先の通り道）→ ②表情の左右差（口角・眉・目の閉じ）→ ③目の動き（点を目だけで追う）→ ④寄り目（黒目の寄り方）→ ⑤舌（写真に顔の中心線を重ねて本人が選ぶ）→ 結果をコピー
- 右・左はすべて本人から見た向き。大きさは目の間の長さを1とした値
- 経緯：~/dev/marketing-playbook/assessments/FNT店舗_コンセプトメイキング/（P8b・P8c）
