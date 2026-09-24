# Video Promo: Program Kemahiran Menghasilkan Bahan AI (Bro Aiman)

- `Promo_Program_AI_Bro_Aiman.mp4`: video siap, 60 saat, 1080x1920 (9:16, untuk TikTok/Reels/Shorts), dengan muzik latar
- `promo.html`: animasi (boleh dibuka terus dalam pelayar untuk pratonton)
- `render.js`: rakam setiap frame dengan Playwright dan enkod dengan ffmpeg
- `music.py`: jana muzik latar dan kesan bunyi "whoosh"
- `assets/`: gambar Bro Aiman (latar dibuang) dan fon

Render semula:
```
python3 music.py music.wav
NODE_PATH=$(npm root -g) node render.js video silent.mp4
ffmpeg -i silent.mp4 -i music.wav -c:v copy -c:a aac -shortest Promo_Program_AI_Bro_Aiman.mp4
```
