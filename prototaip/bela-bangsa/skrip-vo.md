# Skrip VO — Bela Bangsa: Di Mana Batasnya? (versi 80 saat)

Disyorkan untuk jana di ElevenLabs:
- **Model:** Eleven v4 atau v3 (kedua-duanya menyokong tag ekspresi dalam `[ ]`).
- **Suara:** Shahrul – Resonant Documentary Narrator (atau suara Melayu lain yang tenang).
- **Speed:** 1.05; naikkan ke 1.10 jika klip melebihi sasaran. **Stability:** sederhana–tinggi supaya nada sekata antara babak.
- Jana **satu klip bagi setiap babak**. Klip mesti berakhir ≤ 9.2 s; letakkan pada saat 0.4 setiap babak (0.4, 10.4, 20.4 …).
- Jika masih terlalu panjang, buang `[short pause]` dahulu sebelum mengubah perkataan.

| # | Masa | Sasaran | Teks untuk ElevenLabs |
|---|---|---|---|
| 1 | 00–10 s | ≤ 9.2 s | `[calmly] Membela bangsa… [curious] adakah itu perkauman? [calmly] Tulisan Abdul Hadi Awang ini menolak penyamaan itu. [short pause] Mari lihat hujahnya.` |
| 2 | 10–20 s | ≤ 9.2 s | `[warmly] Kasih kepada keluarga dan bangsa ialah sifat manusia. [calmly] Bagi penulis, kasih bukan bermaksud membenci kaum lain.` |
| 3 | 20–30 s | ≤ 9.2 s | `[calmly] Penulis merujuk Surah al-Hujurat, ayat 13, tentang manusia berbangsa dan bersuku untuk saling mengenal. [short pause] Kemuliaan dikaitkan dengan takwa.` |
| 4 | 30–40 s | ≤ 9.2 s | `[calmly] Beliau juga menekankan: berbuat baik dan berlaku adil kepada bukan Islam yang tidak memerangi — merujuk Surah al-Mumtahanah.` |
| 5 | 40–50 s | ≤ 9.2 s | `[calmly] Dari prinsip ini, penulis berhujah: mempertahankan Melayu Islam tidak wajar terus dilabel perkauman. [short pause] [firmly] Itulah pendirian utamanya.` |
| 6 | 50–60 s | ≤ 9.2 s | `[serious] Namun, tulisan ini turut mengandungi dakwaan sejarah dan tuduhan politik semasa. [calmly] Dakwaan itu perlukan sumber dan konteks tambahan.` |
| 7 | 60–70 s | ≤ 9.2 s | `[calmly] Contoh hipotesis: memperjuangkan bantuan untuk komuniti yang memerlukan. [curious] Adakah alasannya jelas? [short pause] Pelaksanaannya adil? [short pause] Hak orang lain dipelihara?` |
| 8 | 70–80 s | ≤ 9.0 s | `[calmly] Penulis membezakan kasih kepada bangsa daripada fanatik perkauman. [warmly] Untuk menilainya, periksa tindakan, bukti, dan layanan terhadap orang lain.` |

Nota:
- Tag hanya mengubah cara sebutan. Ia tidak dibaca dan tidak dipaparkan dalam sari kata.
- Elakkan tag yang dramatik (contohnya `[dramatically]`, `[excited]`) supaya nada kekal neutral.
- Rujukan ayat ialah parafrasa penulis, bukan petikan. Jangan baca dengan nada seperti memetik ayat.
- Jika model tersilap menyebut “al-Hujurat”, cuba eja “al-Hujuraat”.
- Selepas menjana, sambungkan klip dengan ffmpeg (lihat README) atau muatkan setiap klip pada saat permulaan babaknya dalam penyunting video.
