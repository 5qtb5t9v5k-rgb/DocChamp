# GitHub Actions & CI/CD

Tämä hakemisto sisältää GitHub Actions -workflowt automaattiselle testaamiselle ja CI/CD:lle.

## Workflowt

### `ci.yml` - Continuous Integration
Ajaa automaattisesti kun:
- Pushataan `main` tai `develop` -branchiin
- Luodaan Pull Request `main` tai `develop` -branchiin

**Mitä se tekee:**
- ✅ Testaa koodin Python-versioilla 3.8, 3.9, 3.10, 3.11
- ✅ Asentaa Tesseract OCR:n
- ✅ Tarkistaa koodin laadun (flake8, black)
- ✅ Testaa että kaikki importit toimivat
- ✅ Varmistaa että Python-tiedostot kääntyvät

### `deploy.yml` - Deployment Verification
Ajaa automaattisesti kun:
- Pushataan `main` -branchiin
- Manuaalisesti workflow_dispatch:lla

**Mitä se tekee:**
- ✅ Varmistaa että sovellus on valmis deployattavaksi
- ✅ Tarkistaa että kaikki riippuvuudet ovat oikein

## Dependabot

`dependabot.yml` päivittää automaattisesti Python-riippuvuudet viikoittain ja luo Pull Requestit päivityksistä.

## Käyttö

### Pull Request -prosessi

1. **Luo uusi branch:**
   ```bash
   git checkout -b feature/uusi-ominaisuus
   ```

2. **Tee muutokset ja commitoi:**
   ```bash
   git add .
   git commit -m "feat: lisää uusi ominaisuus"
   ```

3. **Pushaa GitHubiin:**
   ```bash
   git push origin feature/uusi-ominaisuus
   ```

4. **Luo Pull Request:**
   - Mene GitHub-repositorioon
   - Klikkaa "New Pull Request"
   - Valitse branchit
   - Täytä PR-template
   - Klikkaa "Create Pull Request"

5. **CI ajaa automaattisesti:**
   - GitHub Actions ajaa testit
   - Näet tulokset PR:ssä
   - Vihreä tikku = kaikki OK
   - Punainen X = korjaa virheet

### Status Badge

Voit lisätä README.md:hen status-badgen näyttämään CI-tilan:

```markdown
![CI](https://github.com/kayttajanimi/docchamp/workflows/CI/badge.svg)
```

## Ongelmatilanteet

### CI epäonnistuu
1. Tarkista GitHub Actions -välilehti
2. Katso virhelokit
3. Korjaa virheet paikallisesti
4. Pushaa uudelleen

### Dependabot PR:t
- Tarkista että päivitykset eivät riko sovellusta
- Testaa paikallisesti ennen mergeä
- Mergeä jos kaikki OK
