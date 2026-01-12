# DocChamp - Julkaisuohjeet Streamlit Cloudiin

## Vaihe 1: GitHub-repositorion luominen

### 1.1 Luo uusi repositorio GitHubissa

1. Mene https://github.com/new
2. Täytä tiedot:
   - **Repository name**: `docchamp` (tai haluamasi nimi)
   - **Description**: "AI-powered document analysis application"
   - **Visibility**: Public (tai Private jos haluat)
   - **Älä** valitse "Add a README file" (meillä on jo)
   - **Älä** valitse lisenssiä tai .gitignore (meillä on jo)
3. Klikkaa "Create repository"

### 1.2 Yhdistä paikallinen repositorio GitHubiin

Aja seuraavat komennot DocChamp-kansiossa:

```bash
# Siirry projektikansioon
cd DocChamp

# Alusta git (jos ei vielä tehty)
git init

# Lisää tiedostot
git add .gitignore README.md requirements.txt app.py ai_service.py document_extractor.py

# Commit
git commit -m "Initial commit: DocChamp - AI-powered document analysis application"

# Yhdistä GitHub-repositorioon (korvaa YOUR_USERNAME omalla GitHub-käyttäjänimelläsi)
git remote add origin https://github.com/YOUR_USERNAME/docchamp.git

# Pushaa GitHubiin
git branch -M main
git push -u origin main
```

**HUOM**: Korvaa `YOUR_USERNAME` omalla GitHub-käyttäjänimelläsi.

## Vaihe 2: Streamlit Cloud -sovelluksen luominen

### 2.1 Luo sovellus Streamlit Cloudissa

1. Mene https://share.streamlit.io
2. Kirjaudu sisään GitHub-tililläsi
3. Klikkaa "New app"
4. Täytä tiedot:
   - **Repository**: Valitse `YOUR_USERNAME/docchamp`
   - **Branch**: `main`
   - **Main file path**: `app.py`
5. Klikkaa "Deploy"

### 2.2 Aseta API-avain (valinnainen)

1. Streamlit Cloud → Valitse sovelluksesi
2. Klikkaa "⋮" (kolme pistettä) → "Settings"
3. Klikkaa "Secrets"
4. Lisää:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
5. Klikkaa "Save"

**HUOM**: Voit myös syöttää API-avaimen suoraan sovelluksen käyttöliittymässä.

## Vaihe 3: Tarkista että kaikki toimii

1. Odota että Streamlit Cloud käynnistää sovelluksen (1-2 minuuttia)
2. Avaa sovelluksen URL-osoite
3. Testaa että sovellus toimii

## Ongelmatilanteet

### Git push epäonnistuu
- Tarkista että olet kirjautunut GitHubiin: `gh auth status`
- Tarkista että remote on oikein: `git remote -v`
- Kokeile käyttää SSH:ta: `git remote set-url origin git@github.com:YOUR_USERNAME/docchamp.git`

### Streamlit Cloud ei käynnisty
- Tarkista että `requirements.txt` on oikein
- Tarkista virhelokit Streamlit Cloud -konsolissa
- Varmista että `app.py` on pääsovellus

### Tesseract ei toimi
- Streamlit Cloudissa Tesseract asennetaan automaattisesti `packages.txt`-tiedoston kautta
- Tiedosto sisältää: `tesseract-ocr` ja `tesseract-ocr-fin`
- Jos ei toimi, tarkista virhelokit Streamlit Cloud -konsolissa
- Varmista että `packages.txt` on repositoriossa

## Tärkeää

- **Ollama ei toimi pilvessä**: Käytä OpenAI:ta Streamlit Cloudissa
- **API-avaimet**: Älä koskaan commitoi `.env`-tiedostoa
- **Testitiedostot**: Ne eivät mene versionhallintaan (`.gitignore`)
