"""
DocChamp - Tekoälypohjainen dokumenttianalyysi-sovellus

Tämä moduuli sisältää Streamlit-pohjaisen käyttöliittymän DocChamp-sovellukseen.
Sovellus mahdollistaa dokumenttien analysoinnin, OCR-käsittelyn ja tekoälypohjaisen
tietojen erottelun.

Päämoduulit:
- document_extractor: Dokumenttien tekstin erottelu (PDF, OCR)
- ai_service: AI-palveluiden abstraktio (OpenAI)
"""
import streamlit as st
from document_extractor import extract_text
from ai_service import create_ai_service, AIService
import os
from dotenv import load_dotenv
import json
import io
from PIL import Image

# Lataa ympäristömuuttujat
load_dotenv()

# Sivun konfiguraatio
st.set_page_config(
    page_title="DocChamp",
    page_icon="📄",
    layout="wide"
)


# Alusta session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "document_text" not in st.session_state:
    st.session_state.document_text = None

if "document_name" not in st.session_state:
    st.session_state.document_name = None

if "ai_service" not in st.session_state:
    st.session_state.ai_service = None

if "receipt_data" not in st.session_state:
    st.session_state.receipt_data = None

if "receipt_image" not in st.session_state:
    st.session_state.receipt_image = None

if "purchase_analysis" not in st.session_state:
    st.session_state.purchase_analysis = None


def initialize_ai_service(model: str = None, temperature: float = 0.2) -> AIService:
    """Alusta OpenAI-palvelu Streamlit Secretsista tai ympäristömuuttujista."""
    try:
        # Hae API-avain Streamlit Secretsista (Streamlit Cloud) tai ympäristömuuttujista
        api_key = None
        try:
            # Yritä lukea Streamlit Secretsista (Streamlit Cloud)
            if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                api_key = st.secrets['OPENAI_API_KEY']
        except Exception:
            pass
        
        # Jos ei löytynyt Secretsista, kokeile ympäristömuuttujaa
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            st.error("⚠️ OpenAI API-avain puuttuu. Aseta se Streamlit Cloud -secrets-kohtaan tai .env-tiedostoon.")
            return None
        
        return create_ai_service("openai", api_key=api_key, model=model or "gpt-4o", temperature=temperature)
    except Exception as e:
        st.error(f"Virhe AI-palvelun alustamisessa: {str(e)}")
        return None


def process_document(uploaded_file):
    """Käsittele ladattu dokumentti."""
    try:
        with st.spinner("Erotetaan tekstiä dokumentista..."):
            text = extract_text(uploaded_file)
            st.session_state.document_text = text
            st.session_state.document_name = uploaded_file.name
            st.session_state.chat_history = []  # Tyhjennä historia uudelle dokumentille
            st.session_state.receipt_data = None  # Tyhjennä vanhat kuittitiedot
            st.session_state.receipt_image = None  # Tyhjennä vanha kuva
            
            # Tallenna kuva jos kyseessä on kuvatiedosto
            if uploaded_file.type and uploaded_file.type.startswith('image/'):
                uploaded_file.seek(0)  # Resetoi tiedosto-osoitin
                st.session_state.receipt_image = uploaded_file.read()
                uploaded_file.seek(0)  # Resetoi taas
            
            st.success(f"Dokumentti '{uploaded_file.name}' käsitelty onnistuneesti!")
            
            # Automaattinen kuittitietojen erottelu jos AI-palvelu on alustettu
            if st.session_state.ai_service and hasattr(st.session_state.ai_service, 'extract_receipt'):
                try:
                    with st.spinner("🔄 Yritetään automaattisesti erottaa kuittitiedot..."):
                        json_result = st.session_state.ai_service.extract_receipt(
                            st.session_state.document_text
                        )
                        import json
                        try:
                            # Puhdista JSON markdown-koodiblokeista ja selitysteksteistä
                            clean_json = extract_json_from_text(json_result)
                            receipt_data = json.loads(clean_json)
                            st.session_state.receipt_data = receipt_data
                            
                            # Tarkista onko viesti siitä että tiedot eivät ole luettavissa
                            notes = receipt_data.get('notes', '')
                            notes_lower = notes.lower() if notes else ''
                            validation_errors = receipt_data.get('validation_errors', [])
                            validation_errors_lower = [str(err).lower() for err in validation_errors]
                            
                            # Tarkista eri avainsanoja
                            unreadable_keywords = [
                                'ei ole luettavissa',
                                'eivät ole luettavissa',
                                'ei luettavissa',
                                'eivät luettavissa',
                                'tiedot eivät ole',
                                'tiedot ei ole',
                                'ei voida lukea',
                                'eivät voida lukea',
                                'not readable',
                                'does not contain relevant',
                                'no valid receipt data',
                                'not contain relevant receipt'
                            ]
                            
                            # Tarkista notes-kentästä
                            is_unreadable_notes = any(keyword in notes_lower for keyword in unreadable_keywords)
                            
                            # Tarkista validointivirheet
                            is_unreadable_validation = any(
                                'no valid receipt data' in err or 
                                'not readable' in err or 
                                'does not contain' in err
                                for err in validation_errors_lower
                            )
                            
                            is_unreadable = is_unreadable_notes or is_unreadable_validation
                            
                            # Tarkista laatu
                            items = receipt_data.get('items', [])
                            
                            # Jos tiedot eivät ole luettavissa, näytä selkeä ohje rajaamisesta HETI YLÄHÄÄLLÄ
                            if is_unreadable:
                                st.warning("⚠️ **Kuitin tiedot eivät ole luettavissa.**")
                                st.info("💡 **Ratkaisu:** Rajaa kuva slidereillä oikealla puolella valitsemalla vain kuitin alue. Tämän jälkeen OCR ja kuittitietojen erottelu suoritetaan automaattisesti uudelleen.")
                            # Jos on paljon validointivirheitä tai vähän tuotteita, ehdotetaan rajausta
                            elif len(validation_errors) > 2 or (len(items) == 0 and len(text.strip()) > 100):
                                st.warning("⚠️ Kuittitietojen laatu voi olla heikohko. Kokeile rajaa kuvaa slidereillä oikealla puolella parantaaksesi OCR:n tarkkuutta!")
                            else:
                                st.success("✅ Kuittitiedot erotettu automaattisesti!")
                        except (json.JSONDecodeError, ValueError) as e:
                            # JSON-parsinta epäonnistui - ehdotetaan rajausta
                            st.warning("⚠️ Automaattinen kuittien erottelu epäonnistui. Kokeile rajaa kuvaa slidereillä oikealla puolella parantaaksesi OCR:n tarkkuutta!")
                except Exception as e:
                    st.info("💡 Automaattinen kuittien erottelu ei onnistunut. Voit yrittää manuaalisesti '🧾 Erota kuitti' -napilla tai rajaa kuvaa ensin.")
            
            return True
    except Exception as e:
        st.error(f"Virhe dokumentin käsittelyssä: {str(e)}")
        return False


def display_chat_message(role: str, content: str):
    """Näytä chat-viesti."""
    if role == "user":
        with st.chat_message("user"):
            st.write(content)
    else:
        with st.chat_message("assistant"):
            st.write(content)


def extract_json_from_text(text: str) -> str:
    """
    Poistaa markdown-koodiblokit ja selitystekstit JSON-vastauksesta.
    
    Args:
        text: Raaka JSON-vastaus, joka voi sisältää markdownia ja selitystekstiä
        
    Returns:
        str: Puhdas JSON-merkkijono
    """
    import re
    import json
    
    if not text or not text.strip():
        raise ValueError("Tyhjä vastaus")
    
    # Poista markdown-koodiblokit (```json ... ``` tai ``` ... ```)
    # Poista kaikki markdown-koodiblokit
    text = re.sub(r'```json\s*\n?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```\s*\n?', '', text)
    
    # Poista yleiset selitystekstit ennen JSONia
    # Poista tekstit kuten "Tässä on kuitin tietojen poiminta OCR-tekstistä:"
    text = re.sub(r'^[^{]*?(?=\{)', '', text, flags=re.DOTALL)
    
    # Poista tekstit JSONin jälkeen
    # Etsi JSON-objektin loppu ja poista kaikki sen jälkeen
    start_idx = text.find('{')
    if start_idx == -1:
        raise ValueError("JSON-objektia ei löytynyt vastauksesta")
    
    # Etsitään vastaava sulkeva } laskemalla aaltosulkeet
    brace_count = 0
    end_idx = start_idx
    for i in range(start_idx, len(text)):
        if text[i] == '{':
            brace_count += 1
        elif text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i + 1
                break
    
    if brace_count != 0:
        raise ValueError("JSON-objekti on epätäydellinen (sulkevia aaltosulkeita puuttuu)")
    
    # Poimi JSON-osa
    json_text = text[start_idx:end_idx].strip()
    
    # Varmista että se on validi JSON
    try:
        json.loads(json_text)  # Testaa että se on validi
    except json.JSONDecodeError as e:
        raise ValueError(f"Poimittu teksti ei ole validi JSON: {str(e)}")
    
    return json_text


# Sidebar
with st.sidebar:
    st.title("⚙️ Asetukset")
    
    st.markdown("**AI-palvelu:** OpenAI")
    
    # Mallin valinta
    model = st.selectbox(
        "Malli:",
        ["gpt-4o", "gpt-4o-mini"],
        index=0,  # gpt-4o oletuksena
        help="Valitse OpenAI-malli"
    )
    
    # Temperature on vakio 0.2 (faktapohjainen dokumentti-QA)
    temperature = 0.2
    
    # Automaattinen alustus jos API-avain löytyy
    if st.session_state.ai_service is None:
        # Yritä alustaa automaattisesti
        try:
            # Tarkista onko API-avain saatavilla
            api_key_available = False
            try:
                if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                    api_key_available = True
            except Exception:
                pass
            
            if not api_key_available:
                api_key_available = bool(os.getenv("OPENAI_API_KEY"))
            
            if api_key_available:
                service = initialize_ai_service(model, temperature)
                if service:
                    st.session_state.ai_service = service
                    st.success("✅ AI-palvelu alustettu automaattisesti!")
            else:
                st.warning("⚠️ OpenAI API-avain puuttuu. Aseta se Streamlit Cloud -secrets-kohtaan.")
        except Exception as e:
            st.warning(f"⚠️ AI-palvelun automaattinen alustus epäonnistui: {str(e)}")
    
    # Manuaalinen alustusnappi (jos automaattinen ei toiminut)
    if st.session_state.ai_service is None:
        if st.button("🔄 Alusta AI-palvelu"):
            service = initialize_ai_service(model, temperature)
            if service:
                st.session_state.ai_service = service
                st.success("✅ AI-palvelu alustettu onnistuneesti!")
                st.rerun()
    else:
        st.success("✅ AI-palvelu on käytössä")
    
    st.divider()
    
    # Dokumenttien upload
    st.title("📄 Dokumentit")
    uploaded_file = st.file_uploader(
        "Lataa dokumentti",
        type=["pdf", "png", "jpg", "jpeg", "gif", "bmp", "tiff"],
        help="Tuetut tiedostotyypit: PDF ja kuvatiedostot"
    )
    
    if uploaded_file is not None:
        if st.button("Käsittele dokumentti"):
            process_document(uploaded_file)
    
    # Näytä nykyinen dokumentti
    if st.session_state.document_text:
        st.info(f"📄 Dokumentti: {st.session_state.document_name}")
        if st.button("Tyhjennä dokumentti"):
            st.session_state.document_text = None
            st.session_state.document_name = None
            st.session_state.chat_history = []
            st.rerun()
    
    st.divider()
    
    # Tyhjennä keskustelu
    if st.button("🗑️ Tyhjennä keskustelu"):
        st.session_state.chat_history = []
        st.rerun()


# Pääalue
st.title("📄 DocChamp")
st.markdown("**DocChamp - Kuittien mestari**")
st.markdown("Lataa PDF tai kuva ja keskustele sisällöstä — kuiteista saat myös rakenteisen yhteenvedon ja ostoanalyysin.")

# Tarkista, onko dokumentti käsitelty
if st.session_state.document_text is None:
    st.info("👈 Aloita lataamalla dokumentti sivupalkista.")
    st.markdown("""
    ### Näin se toimii:
    1. **Lataa dokumentti** (PDF / kuva)
    2. **DocChamp poimii tekstin** (OCR tarvittaessa)
    3. **Valitse mitä haluat:**
       - 💬 **Keskustele dokumentista** chatissa
       - 🧾 **Poimi kuittitiedot** (summa, ALV, rivit)
       - 🛒 **Ostoanalyysi:** kategorisointi + tiivis yhteenveto ostoksista
    """)
else:
    # Näytä dokumentin tiedot
    st.success(f"✅ Dokumentti '{st.session_state.document_name}' on valmis analysoitavaksi")
    
    # Kaksisarakkeinen layout: vasen = chat, oikea = kuitti
    left_col, right_col = st.columns([1.2, 0.8])
    
    with left_col:
        # Vasen sarake: Chat-historia ja syöttökenttä
        st.subheader("💬 Keskustelu")
        
        # Näytä chat-historia
        for message in st.session_state.chat_history:
            display_chat_message(message["role"], message["content"])
        
        # Tietojen irroitusta - napit
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔍 Erota tärkeät tiedot", help="Pyytää AI:ta erottamaan tärkeät tiedot automaattisesti", use_container_width=True):
                if st.session_state.ai_service:
                    with st.spinner("Erotetaan tärkeitä tietoja..."):
                        extraction_prompt = """Analysoi tämä dokumentti ja erota tärkeimmät tiedot. 
                        Listaa:
                        1. Päivämäärät
                        2. Summat/rahasummat
                        3. Henkilönimet ja yhteystiedot
                        4. Tärkeimmät faktat
                        5. Muut merkittävät tiedot
                        
                        Esitä tiedot selkeästi ja strukturoidusti."""
                        
                        try:
                            response = st.session_state.ai_service.chat(
                                st.session_state.document_text,
                                extraction_prompt,
                                st.session_state.chat_history
                            )
                            st.session_state.chat_history.append({"role": "user", "content": extraction_prompt})
                            st.session_state.chat_history.append({"role": "assistant", "content": response})
                            st.rerun()
                        except Exception as e:
                            st.error(f"Virhe: {str(e)}")
                else:
                    st.warning("Alusta AI-palvelu ensin sidebarista!")
        
        with col2:
            if st.button("🧾 Erota kuitti", help="Erottaa kuittitiedot strukturoidusti JSON-muotoon", use_container_width=True):
                if st.session_state.ai_service:
                    with st.spinner("Erotetaan kuittitiedot..."):
                        try:
                            # Tarkista onko palvelulla extract_receipt-metodi
                            if hasattr(st.session_state.ai_service, 'extract_receipt'):
                                json_result = st.session_state.ai_service.extract_receipt(
                                    st.session_state.document_text
                                )
                                # Parsitaan ja tallennetaan session stateen
                                import json
                                try:
                                    # Puhdista JSON markdown-koodiblokeista ja selitysteksteistä
                                    clean_json = extract_json_from_text(json_result)
                                    receipt_data = json.loads(clean_json)
                                    st.session_state.receipt_data = receipt_data
                                    st.session_state.purchase_analysis = None  # Tyhjennä vanha analyysi
                                    
                                    # Lisää chat-historiaan
                                    st.session_state.chat_history.append({
                                        "role": "user", 
                                        "content": "Erota kuittitiedot JSON-muotoon"
                                    })
                                    st.session_state.chat_history.append({
                                        "role": "assistant", 
                                        "content": "Kuittitiedot erotettu! Tarkista oikealla puolella."
                                    })
                                    st.rerun()
                                except (json.JSONDecodeError, ValueError) as e:
                                    st.error("JSON-parsinta epäonnistui.")
                                    st.error(f"Virhe: {str(e)}")
                                    with st.expander("🔍 Raakavastaus (debug)", expanded=False):
                                        st.code(json_result)
                            else:
                                st.warning("Tämä AI-palvelu ei tue kuittien erottelua.")
                        except Exception as e:
                            st.error(f"Virhe: {str(e)}")
                else:
                    st.warning("Alusta AI-palvelu ensin sidebarista!")
        
        with col3:
            if st.button("🛒 Analysoi ostokset", help="Analysoi kuitin ostokset semanttisesti (kategorisointi, yhteenveto)", use_container_width=True):
                if st.session_state.ai_service:
                    if st.session_state.receipt_data:
                        with st.spinner("Analysoidaan ostoksia..."):
                            try:
                                if hasattr(st.session_state.ai_service, 'analyze_purchases'):
                                    analysis = st.session_state.ai_service.analyze_purchases(
                                        st.session_state.receipt_data
                                    )
                                    st.session_state.purchase_analysis = analysis
                                    
                                    # Lisää chat-historiaan
                                    st.session_state.chat_history.append({
                                        "role": "user",
                                        "content": "Analysoi ostokset"
                                    })
                                    st.session_state.chat_history.append({
                                        "role": "assistant",
                                        "content": f"Ostosanalyysi valmis! Tarkista oikealla puolella.\n\n{analysis}"
                                    })
                                    st.rerun()
                                else:
                                    st.warning("Tämä AI-palvelu ei tue ostosten analysointia.")
                            except Exception as e:
                                st.error(f"Virhe: {str(e)}")
                    else:
                        st.warning("Erota ensin kuitti '🧾 Erota kuitti' -napilla!")
                else:
                    st.warning("Alusta AI-palvelu ensin sidebarista!")
        
        # Chat-syöttökenttä
        user_input = st.chat_input("Kysy jotain dokumentista...")
        
        if user_input:
            # Tarkista, onko AI-palvelu alustettu
            if st.session_state.ai_service is None:
                st.warning("⚠️ Alusta AI-palvelu ensin sidebarista!")
            else:
                # Lisää käyttäjän viesti historiaan
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                
                # Näytä käyttäjän viesti
                display_chat_message("user", user_input)
                
                # Hae AI:n vastaus
                with st.spinner("Ajatellaan..."):
                    try:
                        response = st.session_state.ai_service.chat(
                            st.session_state.document_text,
                            user_input,
                            st.session_state.chat_history[:-1]  # Älä sisällytä juuri lisättyä viestiä
                        )
                        
                        # Lisää vastaus historiaan
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        
                        # Näytä vastaus
                        display_chat_message("assistant", response)
                    except Exception as e:
                        error_msg = f"Virhe AI-vastauksessa: {str(e)}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
    
    with right_col:
        # Oikea sarake: Kuittikuvan ja JSON-tulosten näyttäminen
        st.subheader("🧾 Kuitti")
        
        # Näytä kuittikuva jos saatavilla
        if st.session_state.receipt_image:
            from PIL import ImageOps
            try:
                image = Image.open(io.BytesIO(st.session_state.receipt_image))
                
                # Korjaa orientaatio EXIF-tietojen perusteella
                try:
                    image = ImageOps.exif_transpose(image)
                except Exception:
                    pass
                
                # Hae kuvan koko
                img_width, img_height = image.size
                
                # Alusta sliderien arvot jos ne eivät ole olemassa TAI jos kuvan koko on muuttunut
                if "crop_left" not in st.session_state or "crop_image_width" not in st.session_state or st.session_state.crop_image_width != img_width:
                    st.session_state.crop_left = 0
                    st.session_state.crop_top = 0
                    st.session_state.crop_right = img_width
                    st.session_state.crop_bottom = img_height
                    st.session_state.crop_image_width = img_width
                    st.session_state.crop_image_height = img_height
                
                # Varmista että sliderien arvot ovat kuvan sisällä
                if st.session_state.crop_right > img_width:
                    st.session_state.crop_right = img_width
                if st.session_state.crop_bottom > img_height:
                    st.session_state.crop_bottom = img_height
                if st.session_state.crop_left > img_width:
                    st.session_state.crop_left = 0
                if st.session_state.crop_top > img_height:
                    st.session_state.crop_top = 0
                
                # Näytä kuva ylhäällä
                # Tarkista onko koordinaatit järkevät ja näytä joko rajattu tai alkuperäinen kuva
                if (st.session_state.crop_right > st.session_state.crop_left and 
                    st.session_state.crop_bottom > st.session_state.crop_top):
                    preview_cropped = image.crop((
                        st.session_state.crop_left, 
                        st.session_state.crop_top, 
                        st.session_state.crop_right, 
                        st.session_state.crop_bottom
                    ))
                    st.image(preview_cropped, caption=st.session_state.document_name, use_container_width=True)
                else:
                    st.image(image, caption=st.session_state.document_name, use_container_width=True)
                
                # Manuaalinen rajaus -käyttöliittymä slidereillä
                st.markdown("**📐 Rajaa kuitti:**")
                
                # Sliderit koordinaateille (käytä session statea suoraan ilman value-parametria)
                col1, col2 = st.columns(2)
                with col1:
                    left = st.slider("Vasen reuna (X)", 0, img_width, key="crop_left")
                    top = st.slider("Yläreuna (Y)", 0, img_height, key="crop_top")
                with col2:
                    right = st.slider("Oikea reuna (X)", 0, img_width, key="crop_right")
                    bottom = st.slider("Alareuna (Y)", 0, img_height, key="crop_bottom")
                
                # Tarkista että koordinaatit ovat järkevät
                if right > left and bottom > top:
                    # Nappi rajaamiseen ja automaattiseen erotteluun
                    if st.button("✅ Raja kuva näillä koordinaateilla", use_container_width=True):
                        # Rajaa kuva
                        cropped = image.crop((left, top, right, bottom))
                        
                        # Päivitä receipt_image rajattuun kuvaan (korvaa alkuperäinen)
                        buffered_cropped = io.BytesIO()
                        cropped.save(buffered_cropped, format="PNG")
                        st.session_state.receipt_image = buffered_cropped.getvalue()
                        
                        # Poista vanhat crop-arvot jotta ne alustetaan uudelleen seuraavalla renderöinnillä
                        # Kun kuvan koko muuttuu, sliderit alustetaan automaattisesti rivillä 433
                        if "crop_image_width" in st.session_state:
                            del st.session_state.crop_image_width
                        if "crop_image_height" in st.session_state:
                            del st.session_state.crop_image_height
                        
                        # Päivitä myös document_text OCR:lla rajatuusta kuvasta
                        try:
                            from document_extractor import extract_from_image
                            buffered_cropped.seek(0)
                            cropped_text = extract_from_image(buffered_cropped)
                            st.session_state.document_text = cropped_text
                            st.session_state.receipt_data = None  # Tyhjennä vanhat kuittitiedot
                            st.session_state.purchase_analysis = None  # Tyhjennä vanha analyysi
                            
                            st.success("✅ Kuva rajattu ja OCR suoritettu uudelleen!")
                            
                            # Automaattinen kuittien erottelu jos AI-palvelu on alustettu
                            if st.session_state.ai_service and hasattr(st.session_state.ai_service, 'extract_receipt'):
                                try:
                                    with st.spinner("🔄 Erotetaan kuittitiedot..."):
                                        json_result = st.session_state.ai_service.extract_receipt(
                                            st.session_state.document_text
                                        )
                                        import json
                                        try:
                                            # Puhdista JSON markdown-koodiblokeista ja selitysteksteistä
                                            clean_json = extract_json_from_text(json_result)
                                            receipt_data = json.loads(clean_json)
                                            st.session_state.receipt_data = receipt_data
                                            
                                            # Tarkista laatu
                                            validation_errors = receipt_data.get('validation_errors', [])
                                            items = receipt_data.get('items', [])
                                            
                                            if len(validation_errors) > 2 or (len(items) == 0 and len(cropped_text.strip()) > 100):
                                                st.warning("⚠️ Kuittitietojen laatu voi olla vielä heikohko. Kokeile säätää koordinaatteja tarkemmin.")
                                            else:
                                                st.success("✅ Kuittitiedot erotettu onnistuneesti!")
                                        except (json.JSONDecodeError, ValueError) as e:
                                            st.warning("⚠️ Kuittitietojen erottelu epäonnistui. Kokeile säätää koordinaatteja tarkemmin.")
                                except Exception as e:
                                    st.warning(f"⚠️ Kuittitietojen erottelu epäonnistui: {str(e)}")
                            
                            st.rerun()
                        except Exception as e:
                            st.error(f"OCR rajatuusta kuvasta epäonnistui: {str(e)}")
                else:
                    # Jos koordinaatit eivät ole järkevät, näytä alkuperäinen kuva
                    st.image(image, caption=st.session_state.document_name, use_container_width=True)
                    st.warning("⚠️ Tarkista koordinaatit: oikea reunan pitää olla vasemman oikealla puolella ja alareunan yläreunan alapuolella.")
                    
            except Exception as e:
                st.warning(f"Kuvan näyttäminen epäonnistui: {str(e)}")
        
        # Näytä JSON-tulokset jos saatavilla
        if st.session_state.receipt_data:
            import json
            
            # Tarkista onko tiedot luettavissa - näytä varoitus HETI YLÄHÄÄLLÄ jos ei
            notes = st.session_state.receipt_data.get('notes', '')
            notes_lower = notes.lower() if notes else ''
            validation_errors = st.session_state.receipt_data.get('validation_errors', [])
            validation_errors_lower = [str(err).lower() for err in validation_errors]
            
            unreadable_keywords = [
                'ei ole luettavissa',
                'eivät ole luettavissa',
                'ei luettavissa',
                'eivät luettavissa',
                'tiedot eivät ole',
                'tiedot ei ole',
                'ei voida lukea',
                'eivät voida lukea',
                'not readable',
                'does not contain relevant',
                'no valid receipt data',
                'not contain relevant receipt'
            ]
            
            is_unreadable_notes = any(keyword in notes_lower for keyword in unreadable_keywords)
            is_unreadable_validation = any(
                'no valid receipt data' in err or 
                'not readable' in err or 
                'does not contain' in err
                for err in validation_errors_lower
            )
            
            if is_unreadable_notes or is_unreadable_validation:
                st.warning("⚠️ **Kuitin tiedot eivät ole luettavissa.**")
                st.info("💡 **Ratkaisu:** Rajaa kuva slidereillä yläpuolella valitsemalla vain kuitin alue. Tämän jälkeen OCR ja kuittitietojen erottelu suoritetaan automaattisesti uudelleen.")
                st.divider()
            
            st.markdown("### 📋 Erotetut tiedot")
            
            # Näytä tärkeimmät tiedot selkeästi
            if st.session_state.receipt_data.get('merchant'):
                merchant = st.session_state.receipt_data['merchant']
                if merchant.get('name'):
                    st.markdown(f"**Myyjä:** {merchant['name']}")
            
            if st.session_state.receipt_data.get('receipt'):
                receipt = st.session_state.receipt_data['receipt']
                if receipt.get('date'):
                    st.markdown(f"**Päivämäärä:** {receipt['date']}")
                if receipt.get('receipt_number'):
                    st.markdown(f"**Kuittinumero:** {receipt['receipt_number']}")
            
            if st.session_state.receipt_data.get('totals'):
                totals = st.session_state.receipt_data['totals']
                if totals.get('total_gross'):
                    st.markdown(f"**Yhteensä:** {totals['total_gross']} €")
            
            st.divider()
            
            # Näytä koko JSON
            with st.expander("📄 Koko JSON-data", expanded=False):
                st.json(st.session_state.receipt_data)
            
            # Näytä validointivirheet jos löytyy
            if st.session_state.receipt_data.get('validation_errors'):
                st.warning("⚠️ **Validointivirheitä löytyi:**")
                for error in st.session_state.receipt_data['validation_errors']:
                    st.error(f"  • {error}")
            
            st.divider()
            
            # Analyysi-nappi
            if st.button("🛒 Analysoi ostokset", use_container_width=True, help="Analysoi kuitin ostokset semanttisesti"):
                if st.session_state.ai_service and hasattr(st.session_state.ai_service, 'analyze_purchases'):
                    with st.spinner("Analysoidaan ostoksia..."):
                        try:
                            analysis = st.session_state.ai_service.analyze_purchases(
                                st.session_state.receipt_data
                            )
                            st.session_state.purchase_analysis = analysis
                            st.rerun()
                        except Exception as e:
                            st.error(f"Virhe: {str(e)}")
                else:
                    st.warning("AI-palvelu ei tue ostosten analysointia.")
            
            # Näytä analyysi jos saatavilla
            if st.session_state.purchase_analysis:
                st.markdown("### 🛒 Ostosanalyysi")
                st.markdown(st.session_state.purchase_analysis)
        else:
            st.info("💡 Klikkaa '🧾 Erota kuitti' -nappia erottaaksesi kuittitiedot.")
