# Financial Document Extraction Engine (RegexEngineForBills)

A high-performance Python microservice designed to extract, clean, and structure critical billing data (writable lines, due dates, and values) from natively generated electronic invoices (PDFs) using geometric text-mapping and optimized regular expressions.

## 🚀 Live Demo
Experience the extraction engine in real-time with zero installation:
👉 **[Click here to launch the Web Interface (GitHub Pages)](#)** *(Replace this with your GitHub Pages URL)*

---

## 🎯 The Business Problem
Manual data entry of bank slips (boletos) into corporate ERPs or financial spreadsheets is slow, highly prone to human error, and costly. This engine eliminates the administrative friction by programmatically transforming unstructured document layouts into structured, reliable JSON payloads ready to feed any financial automation pipeline or gateway (e.g., Asaas API).

## 🛠️ Tech Stack & Architecture
- **Language:** Python 3.10+
- **Core Engine:** `pdfplumber` (for precise geometric text extraction and layout mapping)
- **Data Parsing:** Native `re` (Regular Expressions optimized for Brazilian billing standards / Febraban standards)
- **API Layer:** Lightweight web server deployed on Render
- **Frontend Demo:** Single-file static HTML/JavaScript with Tailwind CSS CDN, hosted entirely on GitHub Pages.

---

## 🔌 API Reference

### Extract Data from PDF

```http
POST /api/extrair
ParameterTypeDescriptionarquivofile (binary)Required. The native PDF invoice file to be processed.Request Example (cURL)Bashcurl -X POST [https://regexengineforbills.onrender.com/api/extrair](https://regexengineforbills.onrender.com/api/extrair) \
  -F "arquivo=@fatura_internet.pdf"
Response Example (Success 200 OK)JSON{
  "status": "sucesso",
  "total_processado": 1,
  "boletos": [
    {
      "codigo": "00190.00009 02621.522009 12345.678904 5 98120000049900",
      "vencimento": "15/07/2026",
      "valor": "499.00"
    }
  ]
}
Response Example (Error 400 Bad Request)JSON{
  "status": "erro",
  "mensagem": "Formato de arquivo inválido. Apenas PDFs nativos são suportados."
}
🛡️ Built-in Production GuardrailsZero DB Coupling: The core engine is stateless. It operates independently of authorization states, maximizing throughput and horizontal scalability.Deduplication Logic: Built-in array-filtering that automatically identifies and drops duplicate barcodes within the same document payload before compilation, preventing double-billing or artificial quota consumption.Client-Side Payload Throttling: The demo interface strictly limits uploads to 5MB, cutting off resource-exhaustion attacks (DDoS via heavy files) before network payloads strike the server.⚠️ Known Limitations & Future ScopeNative PDFs Only: The current version relies on the document's vector text layer. Scanned documents or image-based invoices (JPEGs/PNGs) lack this layer.Next Iteration (Roadmap): Integrating an isolated OCR layer (e.g., Google Vision API or Tesseract binaries wrapped inside a custom Docker container) to handle low-resolution scans without degrading current regex parsing performance.Developed by João Gabriel — Focused on high-utility corporate automation.
###