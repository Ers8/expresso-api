# Pastikan file private.pem kamu masih ada di folder yang sama untuk dibaca
with open("private.pem", "r") as file:
    isi_kunci = file.read()

# Mengganti enter asli menjadi teks \n
kunci_satu_baris = isi_kunci.replace("\n", "\\n")

print("\n--- COPY TEKS DI BAWAH INI ---")
print(kunci_satu_baris)
print("------------------------------\n")