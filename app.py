import os
import re
from flask import Flask, request, render_template, redirect, url_for
from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'Documents', 'skripsi_checker', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def extract_pdf_text(path):
    """Mengekstrak teks digital dari PDF"""
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + " "
        return text.strip()
    except Exception as e:
        print(f"Gagal membaca file {path}: {e}")
        return ""

def split_into_sentences(text):
    """Memecah teks panjang menjadi daftar kalimat berdasarkan tanda baca"""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]

@app.route('/')
def dashboard():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
    return render_template('dashboard.html', files=files)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        return redirect(url_for('dashboard'))
    except Exception as e:
        return f"Gagal menghapus file: {e}", 500

@app.route('/check', methods=['POST'])
def check_plagiarism():
    if 'file' not in request.files:
        return "Tidak ada file yang diunggah", 400
    file = request.files['file']
    if file.filename == '':
        return "Nama file kosong", 400

    if file and file.filename.endswith('.pdf'):
        new_file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(new_file_path)

        new_text = extract_pdf_text(new_file_path)
        
        if not new_text.strip():
            return "<h3>Error: PDF berupa gambar scan! Sistem membutuhkan PDF teks asli.</h3><br><a href='/'>Kembali</a>", 400

        db_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.pdf')]
        db_texts = []
        valid_files = []

        for f in db_files:
            if f == file.filename:
                continue
            path = os.path.join(UPLOAD_FOLDER, f)
            txt = extract_pdf_text(path)
            if txt:
                db_texts.append(txt)
                valid_files.append(f)

        if not db_texts:
            return render_template('report.html', filename=file.filename, score=0, matches=[], highlighted_text=new_text)

        # 1. Hitung total skor similarity dokumen secara keseluruhan
        all_docs = [new_text] + db_texts
        vectorizer = TfidfVectorizer(analyzer='word', ngram_range=(1, 3), lowercase=True).fit_transform(all_docs)
        vectors = vectorizer.toarray()
        results = cosine_similarity([vectors[0]], vectors[1:])[0]
        
        matches = []
        max_score = 0
        
        for idx, score in enumerate(results):
            percentage = round(score * 100, 2)
            if percentage >= 10.0:
                matches.append({'filename': valid_files[idx], 'score': percentage})
                if percentage > max_score:
                    max_score = percentage
            
        matches = sorted(matches, key=lambda x: x['score'], reverse=True)

        # 2. FITUR CANGGIH: Deteksi Kalimat yang Mirip untuk Fitur Stabilo (Highlight)
        # Ambil semua kalimat dari file baru
        new_sentences = split_into_sentences(new_text)
        plagiarized_sentences = []

        # Kumpulkan semua kalimat dari database dokumen sebagai basis pembanding mikro
        db_sentences = []
        for txt in db_texts:
            db_sentences.extend(split_into_sentences(txt))

        # Cek kecocokan kalimat (jika ada kalimat baru yang mirip dengan salah satu kalimat di database)
        if db_sentences and new_sentences:
            for s_new in new_sentences:
                # Normalisasi teks sederhana untuk perbandingan frasa mikro
                s_new_clean = re.sub(r'[^\w\s]', '', s_new.lower()).strip()
                for s_db in db_sentences:
                    s_db_clean = re.sub(r'[^\w\s]', '', s_db.lower()).strip()
                    
                    # Jika kalimat sama persis atau menjadi bagian di dalamnya
                    if s_new_clean in s_db_clean or s_db_clean in s_new_clean:
                        plagiarized_sentences.append(s_new)
                        break

        # Bangun teks dengan tanda khusus untuk frontend HTML
        highlighted_text = new_text
        if max_score >= 10.0:
            for plagiarized in set(plagiarized_sentences):
                # Ganti teks asli dengan tag penanda khusus agar nanti di HTML otomatis diberi warna stabilo
                highlighted_text = highlighted_text.replace(plagiarized, f"<mark class='plagiat-text'>{plagiarized}</mark>")

        return render_template('report.html', filename=file.filename, score=max_score, matches=matches, highlighted_text=highlighted_text)

    return "Format wajib PDF", 400

if __name__ == '__main__':
    app.run(debug=True, port=8080)