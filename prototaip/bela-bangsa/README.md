# Bela Bangsa: Di Mana Batasnya? — prototaip motion graphic

Video penerangan neutral, 9:16 (1080×1920), 80 saat. Semuanya dalam satu fail HTML (CSS, SVG, JavaScript) dan tidak memerlukan rangkaian.

## Pratonton
Buka `index.html` dalam pelayar.
- Main/jeda, mula semula, peluncur masa dan lompat babak terletak di panel kawalan, di luar kawasan komposisi.
- Semua animasi dan sari kata dikira terus daripada satu nilai masa `t` (`render(t)`), jadi lompat ke mana-mana saat tetap menghasilkan keadaan visual yang betul.
- "Margin selamat" memaparkan kawasan selamat teks (72 px sisi, 110 px atas, 140 px bawah).
- **Pratonton belum mengandungi suara latar.** Gunakan butang "Muat suara latar…" untuk menguji fail audio tempatan. Audio itu menjadi jam induk semasa dimainkan.
- "Muat turun SRT" menjana fail sari kata daripada jadual pemasaan yang sama.

## Eksport MP4
```bash
npm i playwright        # atau guna Playwright/Chromium sedia ada
node export.mjs 30 bela-bangsa.mp4            # tanpa audio
node export.mjs 30 bela-bangsa.mp4 vo.wav     # dengan suara latar
```
Skrip ini membuka `index.html?export=1` pada saiz 1080×1920, merender setiap bingkai dengan `window.renderFrame(t)`, kemudian menyalurkan tangkapan skrin ke ffmpeg (H.264, yuv420p). Set `CHROMIUM_PATH` jika perlu.

## Kawalan kandungan
- Rujukan al-Quran dipaparkan sebagai nama surah dan nombor ayat sahaja. Tiada petikan langsung dan tiada teks Arab.
- Label: *Pendirian penulis*, *Pandangan penulis*, *Ringkasan rujukan dalam tulisan*, *Contoh hipotesis*, *Perlu semakan sumber*.
- Tiada fakta disemak melalui sumber luar. Video menyatakan bahawa ia tidak menyemak kesahihan dakwaan.
- Biru dan jingga mewakili konsep (hujah/prinsip berbanding label/dakwaan yang perlu disemak), bukan kaum atau parti. Semua komuniti dilukis dengan saiz dan warna yang sama.
