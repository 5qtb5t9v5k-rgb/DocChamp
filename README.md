# DocChamp

**DocChamp** on tekoälypohjainen dokumenttianalyysi-sovellus, joka yhdistää OCR-tekniikan, kuvan esikäsittelyn ja moderneja kielimalleja tarjotakseen tehokkaan ratkaisun dokumenttien analysointiin ja tietojen erotteluun.

## Yleiskuvaus

DocChamp on Streamlit-pohjainen web-sovellus, joka mahdollistaa:
- **Automaattisen tekstin erottelun** PDF- ja kuvatiedostoista
- **Älykkään dokumenttianalyysin** tekoälyn avulla
- **Strukturoidun tietojen erottelun** (erityisesti kuiteille)
- **Vuorovaikutteisen chat-käyttöliittymän** dokumentin sisällöstä keskusteluun

Sovellus on suunniteltu modulaarisesti ja tukee useita AI-palveluntarjoajia, mikä mahdollistaa joustavan käytön eri käyttötapauksissa.

## Arkkitehtuuri

DocChamp koostuu kolmesta päämoduulista:

### 1. Dokumenttien käsittely (`document_extractor.py`)
- **PDF-käsittely**: Käyttää `pdfplumber`-kirjastoa tekstin erotteluun
- **OCR-käsittely**: Käyttää Tesseract OCR:ää kuvatiedostojen tekstin tunnistukseen
- **Kuvan esikäsittely**: Automaattinen kontrastin ja terävyyden parannus OCR:n tarkkuuden optimoimiseksi
- **Automaattinen kuitin rajaus**: OpenCV-pohjainen algoritmi, joka tunnistaa ja rajaa kuitin alueen kuvasta
- **Manuaalinen rajaus**: Käyttäjäystävällinen slider-pohjainen rajaus-työkalu

### 2. AI-palvelut (`ai_service.py`)
- **Abstrakti rajapinta**: `AIService`-luokka määrittelee yhteisen rajapinnan kaikille AI-palveluille
- **OpenAI-integraatio**: Tuki OpenAI:n GPT-malleille (gpt-4o-mini, gpt-4o)
- **Ollama-integraatio**: Tuki paikallisille Ollama-malleille (esim. llama3.2)
- **Erikoistuneet toiminnot**:
  - Kuittitietojen erottelu strukturoidulla JSON-skeemalla
  - Ostosten semanttinen analyysi ja kategorisointi
  - Dokumenttikeskustelu chat-tyylisellä käyttöliittymällä

### 3. Käyttöliittymä (`app.py`)
- **Streamlit-pohjainen UI**: Moderni, responsiivinen web-käyttöliittymä
- **Kaksisarakkeinen layout**: Chat-vasemmalla, dokumentti- ja kuittitiedot oikealla
- **Reaaliaikainen esikatselu**: Kuvan rajaus päivittyy reaaliajassa sliderien mukaan
- **Automaattinen laadun tarkistus**: Tunnistaa heikon OCR-laadun ja ehdottaa parannuksia

## Ominaisuudet

### Dokumenttien käsittely
- 📄 **PDF-tiedostot**: Automaattinen tekstin erottelu kaikilta sivuilta
- 🖼️ **Kuvatiedostot**: OCR-tekniikka tekstin tunnistukseen (JPG, PNG, GIF, BMP, TIFF)
- 🔍 **Automaattinen kuitin tunnistus**: OpenCV-pohjainen algoritmi tunnistaa kuitin rajat kuvasta
- ✂️ **Manuaalinen rajaus**: Slider-pohjainen työkalu tarkkaan rajaamiseen

### AI-analyysi
- 💬 **Chat-käyttöliittymä**: Keskustele dokumentin sisällöstä luonnollisella kielellä
- 🔍 **Automaattinen tietojen erottelu**: Erottaa tärkeimmät tiedot dokumentista
- 🧾 **Kuittitietojen erottelu**: Strukturoitu JSON-muotoinen erottelu kuiteista
- 🛒 **Ostosten analyysi**: Semanttinen kategorisointi ja yhteenveto ostoksista

### Laadunvarmistus
- ✅ **Automaattinen validointi**: Tarkistaa kuittitietojen loogisuuden (summat, ALV-erittely)
- ⚠️ **Laadun seuranta**: Tunnistaa heikon OCR-laadun ja ehdottaa parannuksia
- 🔄 **Automaattinen uudelleenkäsittely**: Suorittaa OCR:n ja erottelun uudelleen rajaamisen jälkeen

## Asennus

### Vaatimukset
- Python 3.8 tai uudempi
- Tesseract OCR (kuvatiedostojen käsittelyyn)
- OpenAI API-avain (tai paikallinen Ollama-asennus)

### 1. Kloonaa repositorio

```bash
git clone <repository-url>
cd liitealy
```

### 2. Asenna Python-riippuvuudet

```bash
pip install -r requirements.txt
```

### 3. Asenna Tesseract OCR

**macOS:**
```bash
brew install tesseract
brew install tesseract-lang  # Vapaaehtoinen: lisäkielituki
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-fin  # Suomalainen kielituki
```

**Windows:**
Lataa ja asenna [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) ja lisää se PATH-muuttujaan.

### 4. Konfiguroi ympäristömuuttujat (valinnainen)

Kopioi `.env.example` tiedosto `.env`-tiedostoksi:

```bash
cp .env.example .env
```

Muokkaa `.env`-tiedostoa ja lisää OpenAI API-avain:

```
OPENAI_API_KEY=your_api_key_here
```

**Huomio**: Voit myös syöttää API-avaimen suoraan sovelluksen käyttöliittymässä.

### 5. Ollama (vapaaehtoinen)

Jos haluat käyttää paikallista Ollama-mallia:

1. Asenna Ollama: https://ollama.ai
2. Lataa malli:
   ```bash
   ollama pull llama3.2
   ```
3. Käynnistä Ollama-palvelin (yleensä käynnistyy automaattisesti)

## Käyttö

### Käynnistä sovellus

```bash
streamlit run app.py
```

Sovellus avautuu selaimessa (yleensä `http://localhost:8501`).

### Käyttöohjeet

1. **Valitse AI-palvelu** sidebarista:
   - **OpenAI**: Vaatii API-avaimen (voi syöttää UI:ta tai `.env`-tiedostoon)
   - **Ollama**: Vaatii paikallisen Ollama-asennuksen

2. **Alusta AI-palvelu**:
   - Syötä API-avain (jos OpenAI)
   - Valitse malli
   - Klikkaa "Alusta AI-palvelu" -nappia

3. **Lataa dokumentti**:
   - Klikkaa "Browse files" sidebarissa
   - Valitse PDF- tai kuvatiedosto
   - Klikkaa "Käsittele dokumentti"

4. **Käytä sovellusta**:
   - **Chat**: Kirjoita kysymyksiä dokumentin sisällöstä
   - **Erota tärkeät tiedot**: Automaattinen analyysi dokumentista
   - **Erota kuitti**: Strukturoitu JSON-erottelu kuiteista
   - **Rajaa kuitti**: Jos OCR-laatu on heikko, rajaa kuva haitarin alla oikealla

## Tekninen dokumentaatio

### Tiedostorakenne

```
liitealy/
├── app.py                    # Streamlit-sovellus (pääsovellus)
├── document_extractor.py     # Dokumenttien tekstin erottelu (PDF, OCR)
├── ai_service.py             # AI-palveluiden abstraktio (OpenAI, Ollama)
├── requirements.txt          # Python-riippuvuudet
├── .env.example             # Esimerkki ympäristömuuttujille
├── README.md                # Tämä tiedosto
└── .gitignore               # Git-ignore tiedosto
```

### Moduulien kuvaus

#### `document_extractor.py`
- `extract_text(file)`: Automaattinen tiedostotyypin tunnistus ja tekstin erottelu
- `extract_from_pdf(file)`: PDF-tiedostojen tekstin erottelu
- `extract_from_image(file)`: OCR-tekniikka kuvatiedostojen käsittelyyn
- `preprocess_image_for_ocr(image)`: Kuvan esikäsittely OCR:n tarkkuuden parantamiseksi
- `detect_and_crop_receipt(image)`: Automaattinen kuitin tunnistus ja rajaus
- `detect_white_background_region(image)`: Valkoisen taustan tunnistus

#### `ai_service.py`
- `AIService`: Abstrakti perusluokka AI-palveluille
- `OpenAIService`: OpenAI API:n toteutus
- `OllamaService`: Ollama-paikallisen mallin toteutus
- `create_ai_service()`: Factory-funktio AI-palvelun luomiseen

#### `app.py`
- `process_document()`: Dokumentin käsittely ja automaattinen kuittien erottelu
- `display_chat_message()`: Chat-viestien näyttäminen
- `extract_json_from_text()`: JSON-vastauksen puhdistus markdownista
- `initialize_ai_service()`: AI-palvelun alustus

### Tuetut tiedostotyypit

- **PDF**: `.pdf` (pdfplumber)
- **Kuvatiedostot**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.tiff` (Tesseract OCR)

### AI-mallit

**OpenAI:**
- `gpt-4o-mini` (oletus, suositeltu)
- `gpt-4o`

**Ollama:**
- `llama3.2` (oletus)
- Muut Ollama-mallit (syötä manuaalisesti)

## Ongelmatilanteet

### Tesseract ei löydy

**Ongelma**: `TesseractNotFoundError`

**Ratkaisu**:
- Varmista että Tesseract on asennettuna
- Tarkista että Tesseract on PATH-muuttujassa
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install tesseract-ocr`

### Ollama-yhteys ei toimi

**Ongelma**: Ollama-palvelimeen ei saada yhteyttä

**Ratkaisu**:
- Varmista että Ollama on käynnissä: `ollama serve`
- Tarkista että malli on asennettu: `ollama list`
- Varmista että oikea malli on valittu sidebarissa
- Tarkista että Ollama-palvelin kuuntelee porttia 11434

### OpenAI API-virheet

**Ongelma**: API-virheet tai yhteysongelmat

**Ratkaisu**:
- Tarkista että API-avain on oikein
- Varmista että sinulla on API-krediittejä
- Tarkista että käyttämäsi malli on saatavilla
- Tarkista internet-yhteys

### Heikko OCR-laatu

**Ongelma**: OCR ei tunnista tekstiä oikein

**Ratkaisu**:
- Käytä kuitin rajausta: Avaa "📐 Rajaa kuitti" -haitari oikealla
- Säädä sliderit valitsemaan vain kuitin alue
- Klikkaa "Rajaa kuva näillä koordinaateilla"
- OCR ja erottelu suoritetaan automaattisesti uudelleen

## Kehitys

### Arkkitehtuurin periaatteet

1. **Modulaarisuus**: Jokainen moduuli on itsenäinen ja helppo testata
2. **Abstraktio**: AI-palvelut on abstrahoitu yhteisellä rajapinnalla
3. **Lajittelevuus**: Helppo lisätä uusia AI-palveluntarjoajia
4. **Käyttäjäystävällisyys**: Selkeä UI ja automaattiset laadun tarkistukset

### Laajentaminen

**Uuden AI-palvelun lisääminen**:
1. Periy `AIService`-luokka
2. Toteuta `chat()`, `extract_receipt()` ja `analyze_purchases()` -metodit
3. Lisää factory-funktio `create_ai_service()` -funktioon

**Uuden dokumenttityypin lisääminen**:
1. Lisää tunnistus `extract_text()` -funktioon
2. Toteuta erottelufunktio (esim. `extract_from_docx()`)
3. Päivitä `requirements.txt` tarvittaessa

## Julkaisu Streamlit Cloudissa

### Vaatimukset
- GitHub-tili
- Streamlit Cloud -tili (ilmainen): https://share.streamlit.io
- OpenAI API-avain (jos käytät OpenAI:ta)

### Julkaisuohjeet

1. **Luo GitHub-repositorio:**
   ```bash
   cd /Users/juhorissanen/Desktop/DocChamp
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/kayttajanimi/docchamp.git
   git push -u origin main
   ```

2. **Yhdistä Streamlit Cloudiin:**
   - Mene https://share.streamlit.io
   - Klikkaa "New app"
   - Valitse GitHub-repositorio
   - Valitse branch (yleensä `main`)
   - Valitse pääsovellus: `app.py`

3. **Aseta ympäristömuuttujat (valinnainen):**
   - Streamlit Cloud → App settings → Secrets
   - Lisää:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```
   - **HUOM**: Voit myös syöttää API-avaimen suoraan sovelluksen käyttöliittymässä

4. **Käynnistä sovellus:**
   - Streamlit Cloud käynnistää sovelluksen automaattisesti
   - Sovellus on saatavilla julkisella URL-osoitteella

### Tärkeää Streamlit Cloudissa

- **Ollama ei toimi**: Ollama vaatii paikallisen asennuksen, joten se ei toimi Streamlit Cloudissa. Käytä OpenAI:ta.
- **Tesseract OCR**: Streamlit Cloudissa Tesseract on yleensä saatavilla, mutta varmista että se toimii.
- **API-avaimet**: Älä koskaan commitoi `.env`-tiedostoa. Käytä Streamlit Secrets -toimintoa.
- **Testitiedostot**: Testitiedostot (testi1.jpeg, testi2.png, jne.) eivät kuulu julkaisuun - ne on `.gitignore`-tiedostossa.

### Ongelmatilanteet Streamlit Cloudissa

**Sovellus ei käynnisty:**
- Tarkista että `requirements.txt` on oikein
- Tarkista että `app.py` on pääsovellus
- Tarkista virhelokit Streamlit Cloud -konsolissa

**Tesseract ei toimi:**
- Streamlit Cloudissa Tesseract pitäisi olla saatavilla
- Jos ei toimi, tarkista virhelokit

**API-avain ei toimi:**
- Varmista että avain on oikein Streamlit Secrets -kohdassa
- Tarkista että avain on voimassa

## Lisenssi

Tämä projekti on vapaasti käytettävissä.

## Tuki

Jos kohtaat ongelmia tai sinulla on kysymyksiä, tarkista:
1. Tämä dokumentaatio
2. Koodin kommentit
3. Virheilmoitukset sovelluksessa
