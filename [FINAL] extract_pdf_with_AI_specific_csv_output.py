import streamlit as st
import pdfplumber
import openai
import tiktoken
import pandas as pd
import io
import re

# Set API key
# Insert your API Key here
openai.api_key = ''


# Fungsi untuk menghitung jumlah token dalam teks
def count_tokens(text, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Fungsi untuk ekstrak teks dari PDF
def extract_text_from_pdf(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text()
    return text

# Fungsi untuk ekstraksi data menggunakan OpenAI API terbaru
def extract_data_with_llm(text):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant who extracts data from text."},
            {"role": "user", "content": f"Extract data from the following text: {text}"}
        ]
    )
    return response.choices[0].message.content

# Fungsi untuk melakukan ekstraksi spesifik PPh, PPh Total, dan status approval
def extract_tax_information(text):
    prompt = (
        f"Dari teks diatas, extract informasi berikut ini:\n"
        f"1. PPh Total (Total Income Tax)\n"
        f"2. Apakah terdapat nomor dinas permohonan pembayaran\n"
        f"3. Apakah dokumen disetujui atau tidak\n"
        f"Kembalikan hasil dengan format: pph<comma>nomor dinas<comma>disetujui/tidak.\n"
        f"Buat format output comma separated value dan hanya berisi angka pph, nomor dinas, 'disetujui' atau 'tidak disetujui' tidak ada kata atau nomor lain \n\n"
        f"Text: {text}"
    )
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an assistant specialized in financial document analysis."},
            {"role": "user", "content": prompt}
        ]
    )
    # Parsing hasil dari LLM
    extracted_info = response.choices[0].message.content
    parsed_data = extracted_info.split(',')
    
    # Parsing hasil LLM menjadi nilai yang bisa digunakan
    if len(parsed_data) == 3:
        pph_total_value = float(parsed_data[0].strip().replace('.', '').replace(',', '.'))  # Mengubah format ke float
        nomor_dinas_value = parsed_data[1].strip()  # Nomor dinas
        approval_status_value = parsed_data[2].strip()  # Status approval (disetujui / tidak disetujui)
    else:
        # Jika format tidak sesuai, kembalikan nilai default
        pph_total_value, nomor_dinas_value, approval_status_value = 0.0, "Tidak ada nomor dinas", "Tidak diketahui"

    return pph_total_value, nomor_dinas_value, approval_status_value

# Fungsi untuk membandingkan PPh Total dengan data di Excel dan menghasilkan Excel baru
def compare_with_excel(extracted_pph_total, extracted_nomor_dinas, extracted_approval_status, excel_file):
    # Membaca file Excel
    df = pd.read_excel(excel_file)

    # Bandingkan PPh Total
    df['RESULT'] = df['Total Pajak'].apply(lambda x: 'Match' if x == extracted_pph_total else 'No Match')

    # Persiapkan data untuk ditulis ke Excel
    sequence_number = 1  # Kita gunakan 1 sebagai contoh
    sap_value = df['Total Pajak'].iloc[0]  # Ambil nilai dari Excel, asumsikan baris pertama
    result_value = df['RESULT'].iloc[0]  # Ambil hasil perbandingan


    # Tambahkan kolom Nomor Dinas dan Approval Status dari hasil LLM
    #df['Extracted Nomor Dinas'] = extracted_nomor_dinas
    #df['Extracted Approval Status'] = extracted_approval_status

    # Menghasilkan Excel baru dengan hasil perbandingan
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book
        worksheet = workbook.add_worksheet('PAJAK')
        writer.sheets['PAJAK'] = worksheet
        #df.to_excel(writer, index=False, sheet_name='Sheet1')

        # Menulis "Checklist" di A1
        worksheet.write('A1', 'Checklist')

        # Menggabungkan sel A2:B3 dan menulis "PAJAK"
        worksheet.merge_range('A2:B3', 'PAJAK')

        # Menulis Nomor Dinas di B12
        worksheet.write('B12', extracted_nomor_dinas)

        # Menulis header di baris 13
        worksheet.write('A13', 'No')
        worksheet.write('B13', 'Dokumen Pajak')
        worksheet.write('C13', 'SAP')
        worksheet.write('D13', 'RESULT')

        # Menulis data mulai dari baris 14
        worksheet.write('A14', sequence_number)
        worksheet.write('B14', extracted_pph_total)
        worksheet.write('C14', sap_value)
        worksheet.write('D14', result_value)

        # Atur lebar kolom agar lebih rapi
        worksheet.set_column('A:A', 5)    # Kolom No
        worksheet.set_column('B:B', 20)   # Kolom Dokumen Pajak
        worksheet.set_column('C:C', 20)   # Kolom SAP
        worksheet.set_column('D:D', 10)   # Kolom RESULT

    return output


# Upload multi PDF
uploaded_files = st.file_uploader("Upload multiple PDFs", type="pdf", accept_multiple_files=True)
uploaded_excel = st.file_uploader("Upload Excel for comparison", type="xlsx")


if uploaded_files and uploaded_excel:
#    all_extracted_texts = []
    for uploaded_file in uploaded_files:
        st.write(f"Processing file: {uploaded_file.name}")
        
        # Ekstraksi teks dari PDF
        text_from_pdf = extract_text_from_pdf(uploaded_file)

        # Menghitung jumlah token
        token_count = count_tokens(text_from_pdf)
        st.write(f"Jumlah token: {token_count}")

        if token_count > 16000:
            st.error("Teks terlalu panjang untuk diproses oleh OpenAI API. Silakan coba dengan file yang lebih kecil atau teks yang lebih singkat.")
        else:
            # Ekstraksi data dengan OpenAI API jika dalam batas token
            extracted_data = extract_data_with_llm(text_from_pdf)
            st.write(f"Extracted Data from {uploaded_file.name}:")
            st.write(extracted_data)

            # Ekstraksi informasi PPh Total, Nomor Dinas, dan Approval Status
            extracted_pph_total, extracted_nomor_dinas, extracted_approval_status = extract_tax_information(text_from_pdf)
            st.write(f"PPh Total: {extracted_pph_total}")
            st.write(f"Nomor Dinas: {extracted_nomor_dinas}")
            st.write(f"Approval Status: {extracted_approval_status}")

            # Bandingkan PPh Total, Nomor Dinas, dan Approval Status dengan data di Excel
            output_excel = compare_with_excel(extracted_pph_total, extracted_nomor_dinas, extracted_approval_status, uploaded_excel)

            # Download Excel yang baru dengan hasil perbandingan
            st.download_button(
                label="Download comparison result as Excel",
                data=output_excel.getvalue(),
                file_name="comparison_result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )