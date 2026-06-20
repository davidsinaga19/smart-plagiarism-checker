# Smart Plagiarism Checker 🚀

Sistem Deteksi Kemiripan Dokumen Akademik Otomatis yang dibangun menggunakan framework **Flask (Python)** dan pemrosesan bahasa alami (NLP). Aplikasi ini memanfaatkan metode **TF-IDF (Term Frequency - Inverse Document Frequency)** dan **Cosine Similarity** untuk menghitung persentase tingkat kemiripan antar dokumen PDF secara akurat dan interaktif.

## 📁 Struktur Direktori Projek

```text
smart-plagiarism-checker/
├── app.py                 # File utama aplikasi Flask & Logic NLP
├── templates/             # Folder berisi file tampilan HTML
│   ├── dashboard.html     # Halaman interaktif hasil analisis
│   └── report.html        # Halaman detail laporan kecocokan
├── uploads/               # Direktori penyimpanan sementara file PDF
├── .gitignore             # Pengaturan berkas sampah yang diabaikan oleh Git
└── README.md              # Dokumentasi projek