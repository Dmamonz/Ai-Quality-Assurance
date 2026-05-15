import os
import sys
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import coverage
import pytest
from pytest_jsonreport.plugin import JSONReport
from openai import OpenAI

# =====================================================================
# 1. STRUKTUR DATA MODEL PENJAMINAN MUTU (SCHEMA-FIRST DESIGN)
# =====================================================================

class CodeIssue(BaseModel):
    file_path: str = Field(description="Jalur absolut atau relatif menuju berkas kode yang dianalisis.")
    line_number: Optional[int] = Field(description="Nomor baris spesifik tempat ditemukannya anomali mutu.")
    severity: str = Field(description="Tingkat keparahan anomali, wajib bernilai: High, Medium, atau Low.")
    category: str = Field(description="Kategori cacat kode: Security, Performance, Logic Error, Style, Error Handling.")
    description: str = Field(description="Deskripsi analitis mengenai akar penyebab masalah semantik kode.")
    suggested_fix: str = Field(description="Rekomendasi blok kode korektif yang aman untuk diimplementasikan.")

class QualityManagementReport(BaseModel):
    executive_summary: str = Field(description="Analisis arsitektural tingkat tinggi mengenai kesehatan basis kode sumber.")
    global_quality_score: int = Field(description="Skor mutu kuantitatif kode dalam rentang numerik skala 1 hingga 100.")
    issues: List[CodeIssue] = Field(description="Daftar terperinci dari seluruh temuan anomali mutu perangkat lunak.")

# =====================================================================
# 2. KOMPONEN UTAMA ORKESTRASI MUTU (MUTU ARSITEKTUR ENGINE)
# =====================================================================

class SoftwareQualityOrchestrator:
    def __init__(self, api_key: Optional[str] = None):
        """Inisialisasi klien kecerdasan buatan dengan konfigurasi model terikat skema."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Kunci otentikasi API OpenAI tidak ditemukan dalam variabel lingkungan.")
        # Mengonfigurasi klien OpenAI standar sesuai dokumentasi SDK terbaru
        self.client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="API KEY BUATAN UNTUK OPENROUTER"
    )
        # Menggunakan salah satu model koding berskala besar yang disediakan gratis
        self.analysis_model = "google/gemini-2.5-flash"

    def run_static_semantic_review(self, target_files: List[str]) -> QualityManagementReport:
        """Mengeksekusi peninjauan kode statis semantik dengan kompatibilitas OpenRouter Gratis."""
        code_payload_accumulator = ""
        
        for file_path in target_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as file_stream:
                        content = file_stream.read()
                        code_payload_accumulator += f"\n\n--- BERKAS: {file_path} ---\n{content}\n"
                except Exception as read_exception:
                    print(f"[-] Gagal membaca komponen berkas {file_path}: {str(read_exception)}")
        
        if not code_payload_accumulator:
            raise ValueError("Tidak ada muatan kode sumber yang valid untuk dikirimkan ke mesin inferensi AI.")

        # Memasukkan skema struktur JSON langsung ke dalam prompt sebagai instruksi model gratisan
        system_instruction = (
            "Anda adalah pakar penjaminan mutu perangkat lunak senior dan arsitek sistem komputer.\n"
            "Tugas Anda adalah melakukan audit semantik mendalam terhadap kode sumber yang dikirimkan. "
            "Identifikasi celah keamanan kritis (seperti SQL Injection, Command Injection, kebocoran kredensial), "
            "cacat logika kondisional, kegagalan penanganan eksepsi, inefisiensi performa algoritma, "
            "serta ketidakpatuhan terhadap pola pemrograman idionatis Python.\n\n"
            "Anda WAJIB mengembalikan respon dalam format JSON murni tanpa dekorasi markdown (tanpa ```json) yang mengikuti skema berikut:\n"
            f"{json.dumps(QualityManagementReport.model_json_schema())}"
        )

        try:
            # Mengubah dari.beta.chat.completions.parse menjadi.chat.completions.create biasa
            api_completion = self.client.chat.completions.create(
                model=self.analysis_model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": f"Lakukan audit kualitas komprehensif pada kode berikut:\n{code_payload_accumulator}"}
                ],
                response_format={"type": "json_object"},  # Menggunakan format objek umum yang didukung model gratisan
                max_tokens=1500 # Membatasi jumlah token untuk menjaga respons tetap fokus dan dalam batasan model gratisan
            )
            
            raw_json_output = api_completion.choices[0].message.content
            
            # Pydantic akan memvalidasi teks mentah JSON tersebut menjadi objek Python secara lokal
            return QualityManagementReport.model_validate_json(raw_json_output)
            
        except Exception as api_error:
            print(f"[-] Terjadi kesalahan fatal selama proses inferensi AI: {str(api_error)}")
            raise
        
    def run_dynamic_functional_testing(self, test_dir: str, source_dir: str) -> Dict[str, Any]:
        """Menjalankan unit testing secara programatik dan mengekstrak metrik cakupan baris kode."""
        if not os.path.exists(test_dir):
            return {
                "execution_status": "FAILED",
                "error_message": f"Direktori lokasi unit pengujian '{test_dir}' tidak ditemukan."
            }

        # Mengonfigurasi pelacak cakupan kode secara programatik untuk menghindari polusi berkas eksternal
        coverage_tracker = coverage.Coverage(source=[source_dir], branch=True)
        coverage_tracker.erase()
        coverage_tracker.start()

        # Menginisialisasi objek plugin json-report untuk menangkap hasil uji langsung dari memori runtime
        json_report_plugin = JSONReport()

        print(f"[*] Meluncurkan sub-proses Pytest secara programatik pada direktori: {test_dir}")
        # Memanggil pytest.main tanpa menulis berkas fisik.report.json ke sistem penyimpanan lokal
        pytest_exit_code = pytest.main(
            ["-q", "--tb=no", test_dir], 
            plugins=[json_report_plugin]
        )

        coverage_tracker.stop()
        coverage_tracker.save()

        global_coverage_percent = 0.0
        coverage_breakdown_data = {}

        try:
            # Memanfaatkan metode internal untuk mengekstrak data persentase tanpa memicu kerusakan I/O
            temp_json_artifact = ".temp_coverage_data.json"
            coverage_tracker.json_report(outfile=temp_json_artifact)
            if os.path.exists(temp_json_artifact):
                with open(temp_json_artifact, "r") as json_stream:
                    parsed_coverage = json.load(json_stream)
                global_coverage_percent = parsed_coverage.get("totals", {}).get("percent_covered", 0.0)
                coverage_breakdown_data = parsed_coverage.get("files", {})
                os.remove(temp_json_artifact)
        except Exception as coverage_exception:
            print(f"[-] Kegagalan ekstraksi data cakupan kode secara mekanis: {str(coverage_exception)}")

        # Mengekstrak hasil ringkasan pytest dari objek plugin runtime
        pytest_report_summary = {}
        if hasattr(json_report_plugin, "report") and "summary" in json_report_plugin.report:
            pytest_report_summary = json_report_plugin.report["summary"]

        is_test_success = "PASSED" if pytest_exit_code == 0 else "FAILED"

        return {
            "execution_status": "SUCCESS",
            "test_outcome": is_test_success,
            "pytest_exit_value": int(pytest_exit_code),
            "statement_coverage_score": round(global_coverage_percent, 2),
            "pytest_summary": pytest_report_summary,
            "individual_file_coverage": coverage_breakdown_data
        }

# =====================================================================
# 3. GLOBAL PIPELINE PIPING & EXECUTION INTERFACE
# =====================================================================

def execute_quality_assurance_pipeline(src_path: str, test_path: str):
    """Fungsi pembungkus alur kerja terintegrasi untuk mengevaluasi mutu komprehensif sistem."""
    print("=" * 80)
    print("[*] MEMULAI SISTEM AUTOMATED TESTING DAN CODE REVIEW BERBASIS KECERDASAN BUATAN")
    print("=" * 80)

    # Memindai struktur direktori untuk mengumpulkan berkas Python yang valid secara otomatis
    files_to_review = []
    for root_dir, _, current_files in os.walk(src_path):
        for single_file in current_files:
            if single_file.endswith(".py") and not single_file.startswith("test_"):
                files_to_review.append(os.path.join(root_dir, single_file))

    if not files_to_review:
        print(f"[-] Pembatalan Proses: Tidak ditemukan komponen kode sumber Python dalam direktori '{src_path}'.")
        return

    print(f"[+] Terdeteksi {len(files_to_review)} berkas komponen utama yang siap diaudit.")

    try:
        # Instansiasi mesin orkestrator utama
        quality_engine = SoftwareQualityOrchestrator(api_key="API KEY BUATAN UNTUK OPENROUTER")

        # Eksekusi Tahap I: Peninjauan Semantik Statis AI
        print("[*] Fase 1: Memulai AI Structured Code Review via Constrained Decoding...")
        static_analysis_result = quality_engine.run_static_semantic_review(files_to_review)

        # Eksekusi Tahap II: Pengujian Dinamis fungsional
        print("[*] Fase 2: Meluncurkan Skenario Uji Fungsional dan Pengukuran Cakupan Kode...")
        dynamic_testing_result = quality_engine.run_dynamic_functional_testing(test_path, src_path)

        # Integrasi Laporan Hasil Akhir Terpadu Pada Konsol Pengembang
        print("\n" + "=" * 24 + " MANIFEST TATA KELOLA MUTU AKHIR PROYEK " + "=" * 24)
        print(f"Skor Kualitas Kode Statis (AI Engine)    : {static_analysis_result.global_quality_score} / 100")
        print(f"Status Kelayakan Pengujian Dinamis       : {dynamic_testing_result.get('test_outcome')}")
        print(f"Persentase Cakupan Baris Kode (Coverage) : {dynamic_testing_result.get('statement_coverage_score')}%")
        print("-" * 88)
        print("Ringkasan Eksekutif Mutu Arsitektural:")
        print(static_analysis_result.executive_summary)
        print("-" * 88)
        print(f"Daftar Temuan Cacat Semantik dan Kerentanan Kode ({len(static_analysis_result.issues)} Masalah):")

        for index, anomaly in enumerate(static_analysis_result.issues, start=1):
            print(f"\n({index}) Kategori: {anomaly.category} | Skala Bahaya: {anomaly.severity}")
            print(f"    Lokasi Berkas : {anomaly.file_path} (Baris Kode: {anomaly.line_number or 'N/A'})")
            print(f"    Uraian Masalah : {anomaly.description}")
            print(f"    Rekomendasi Struktur Perbaikan Kode:\n{anomaly.suggested_fix}")
        print("=" * 88)

        # Pengeksporan artifak hasil uji konsolidasi untuk kebutuhan integrasi pipa CI/CD
        consolidated_manifest = {
            "meta_metrics": {
                "ai_score": static_analysis_result.global_quality_score,
                "test_status": dynamic_testing_result.get("test_outcome"),
                "coverage_percent": dynamic_testing_result.get("statement_coverage_score")
            },
            "static_review": static_analysis_result.model_dump(),
            "dynamic_testing": {
                "pytest_summary": dynamic_testing_result.get("pytest_summary")
            }
        }

        with open("quality_assurance_manifest.json", "w", encoding="utf-8") as manifest_writer:
            json.dump(consolidated_manifest, manifest_writer, indent=4, ensure_ascii=False)
        print("[+] Sukses mengekspor dokumen penjaminan mutu ke 'quality_assurance_manifest.json'")

    except Exception as pipeline_exception:
        print(f"[-] Kegagalan katastropik sistem pada alur pipa manajemen mutu: {str(pipeline_exception)}")

if __name__ == "__main__":
    # Konfigurasi parameter masukan default untuk memudahkan eksekusi langsung dari terminal
    # Contoh eksekusi: python quality_orchestrator.py ./src ./tests
    source_directory_parameter = sys.argv[1] if len(sys.argv) > 2 else "./src"
    test_directory_parameter = sys.argv[2] if len(sys.argv) > 2 else "./tests"
    execute_quality_assurance_pipeline(source_directory_parameter, test_directory_parameter)
    
    
    
    
    