"""
Dokumenttien tekstin erottelu DocChamp-sovellukseen.

Tämä moduuli käsittelee eri tiedostomuotojen tekstin erottelun:
- PDF-tiedostot: pdfplumber-kirjaston avulla
- Kuvatiedostot: Tesseract OCR:n avulla

Ominaisuudet:
- Automaattinen kuvan esikäsittely OCR:n tarkkuuden parantamiseksi
- Automaattinen kuitin tunnistus ja rajaus OpenCV:llä
- Manuaalinen rajaus-työkalu slider-pohjaisella UI:lla

Funktiot:
- extract_text(): Automaattinen tiedostotyypin tunnistus ja erottelu
- extract_from_pdf(): PDF-tiedostojen käsittely
- extract_from_image(): OCR-käsittely kuvatiedostoille
- preprocess_image_for_ocr(): Kuvan esikäsittely
- detect_and_crop_receipt(): Automaattinen kuitin tunnistus
"""
import io
import os
from typing import Union, Optional, Tuple
import pdfplumber
from PIL import Image, ImageEnhance, ImageOps
import pytesseract
import numpy as np

# Streamlit Cloud: Aseta Tesseract OCR:n polku jos se löytyy
# Tesseract asennetaan packages.txt:n kautta, mutta polku voi olla eri
if os.path.exists('/usr/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
elif os.path.exists('/usr/local/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'

# OpenCV on valinnainen - jos sitä ei ole, käytetään koko kuvaa
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False


def detect_white_background_region(image: Image.Image) -> Image.Image:
    """
    Tunnistaa valkoisen taustan alueen (todennäköisesti kuitti).
    Käyttää histogram-analyysiä ja morphological operations.
    
    Args:
        image: PIL Image -objekti
        
    Returns:
        Image.Image: Rajattu kuva (tai alkuperäinen jos tunnistus epäonnistui)
    """
    if not OPENCV_AVAILABLE:
        return image
    
    try:
        img_array = np.array(image)
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY) if len(img_array.shape) == 3 else img_array
        
        # 1. Histogram-analyysi: Etsi valkoiset alueet (pikselit > 200)
        # Kokeile useita threshold-arvoja
        for threshold in [200, 180, 220]:
            _, white_mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
            
            # 2. Morphological operations yhdistääksemme valkoiset alueet
            # Suuremmat kernelit yhdistävät paremmin
            kernel_size = 30
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
            white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
            white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
            
            # 3. Etsi kontuurit valkoisista alueista
            contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Etsi suurin kontuuri
                largest = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(largest)
                image_area = gray.shape[0] * gray.shape[1]
                
                # Jos kontuuri on riittävän suuri (10-90% kuvasta)
                if 0.10 < (area / image_area) < 0.90:
                    # Tarkista onko se suorakulmainen
                    epsilon = 0.02 * cv2.arcLength(largest, True)
                    approx = cv2.approxPolyDP(largest, epsilon, True)
                    
                    # Laske aspect ratio
                    x, y, w, h = cv2.boundingRect(largest)
                    aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
                    
                    # Jos löytyi 4 kulmaa tai järkevä aspect ratio, käytä sitä
                    if len(approx) >= 4 or (1.2 < aspect_ratio < 6.0):
                        # Lisää marginaali
                        margin = 20
                        x = max(0, x - margin)
                        y = max(0, y - margin)
                        w = min(img_array.shape[1] - x, w + 2 * margin)
                        h = min(img_array.shape[0] - y, h + 2 * margin)
                        
                        cropped = img_array[y:y+h, x:x+w]
                        if len(cropped.shape) == 3:
                            cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
                        return Image.fromarray(cropped)
    except:
        pass
    
    return image


def detect_and_crop_receipt(image: Image.Image) -> Image.Image:
    """
    Tunnistaa ja rajaa kuitin alueen kuvasta automaattisesti.
    Käyttää useita lähestymistapoja parhaan tuloksen saamiseksi.
    Priorisoi valkoisen taustan tunnistusta (kuitit ovat yleensä valkoisia).
    
    Args:
        image: PIL Image -objekti
        
    Returns:
        Image.Image: Rajattu kuva (tai alkuperäinen jos tunnistus epäonnistui)
    """
    if not OPENCV_AVAILABLE:
        # Jos OpenCV ei ole saatavilla, palauta alkuperäinen kuva
        return image
    
    # LÄHESTYMISTAPA 1: Valkoisen taustan tunnistus (usein paras kuiteille)
    result = detect_white_background_region(image)
    if result != image:
        # Tarkista että tulos on järkevä (ei liian pieni)
        result_array = np.array(result)
        original_array = np.array(image)
        if result_array.size > original_array.size * 0.1:
            return result
    
    # LÄHESTYMISTAPA 2: Parannettu edge detection ja threshold-menetelmät
    try:
        # Muunna PIL Image numpy-arrayksi
        img_array = np.array(image)
        original_shape = img_array.shape
        
        # Muunna RGB -> BGR (OpenCV käyttää BGR:ää)
        if len(img_array.shape) == 3:
            img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        # Muunna harmaasävyksi
        gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY) if len(img_array.shape) == 3 else img_array
        
        # Paranna kontrastia CLAHE:llä (parempi kuin yksinkertainen contrast enhancement)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Kokeile useita threshold-menetelmiä
        methods = [
            # Otsu threshold (automaattinen optimointi)
            ("otsu", lambda g: cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]),
            # Adaptiivinen threshold (pienempi block size - parempi pienille alueille)
            ("adaptive_small", lambda g: cv2.adaptiveThreshold(
                g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 9, 2)),
            # Adaptiivinen threshold (suurempi block size - parempi suurille alueille)
            ("adaptive_large", lambda g: cv2.adaptiveThreshold(
                g, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3)),
            # Yksinkertainen threshold (valkoiset alueet)
            ("white_thresh", lambda g: cv2.threshold(g, 200, 255, cv2.THRESH_BINARY)[1]),
        ]
        
        best_result = None
        best_score = 0
        
        for method_name, method in methods:
            try:
                thresh = method(enhanced)
                
                # Morphological operations yhdistääksemme alueet
                # Suuremmat kernelit yhdistävät paremmin erilliset alueet
                kernel_sizes = [(15, 15), (25, 25), (30, 30)]
                
                for kernel_size in kernel_sizes:
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
                    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
                    morph = cv2.morphologyEx(morph, cv2.MORPH_OPEN, kernel)
                    
                    # Etsi kontuurit
                    contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    if not contours:
                        continue
                    
                    # Etsi suurin kontuuri
                    largest = max(contours, key=cv2.contourArea)
                    area = cv2.contourArea(largest)
                    image_area = gray.shape[0] * gray.shape[1]
                    
                    # Suodata liian pienet/suuret
                    area_ratio = area / image_area
                    if not (0.10 < area_ratio < 0.90):
                        continue
                    
                    # Tarkista muoto (kuitti on yleensä suorakulmainen)
                    epsilon = 0.02 * cv2.arcLength(largest, True)
                    approx = cv2.approxPolyDP(largest, epsilon, True)
                    
                    # Laske suorakulmion suhde (aspect ratio)
                    x, y, w, h = cv2.boundingRect(largest)
                    aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
                    
                    # Pisteet: pinta-ala + 4 kulmaa + järkevä aspect ratio
                    score = area_ratio
                    if len(approx) == 4:
                        score *= 1.5  # Bonus jos löytyi 4 kulmaa
                    if 1.5 < aspect_ratio < 5.0:  # Kuitit ovat yleensä pituussuuntaisia
                        score *= 1.2
                    # Bonus jos käytettiin valkoisen taustan thresholdia
                    if method_name == "white_thresh":
                        score *= 1.3
                    
                    if score > best_score:
                        best_score = score
                        best_result = (largest, approx, x, y, w, h)
            except:
                continue
        
        if best_result is None:
            # Jos mikään ei toiminut, palauta alkuperäinen kuva
            return image
        
        largest_contour, approx, x, y, w, h = best_result
        
        # Jos löytyi 4 kulmaa, käytä perspektiivin korjausta
        if len(approx) == 4:
            # Järjestä kulmat: ylävasen, yläoikea, alaoikea, alavasen
            pts = approx.reshape(4, 2)
            rect = np.zeros((4, 2), dtype=np.float32)
            
            # Laske summa ja erotus löytääksemme kulmat
            s = pts.sum(axis=1)
            diff = np.diff(pts, axis=1)
            
            rect[0] = pts[np.argmin(s)]  # ylävasen (pienin summa)
            rect[2] = pts[np.argmax(s)]  # alaoikea (suurin summa)
            rect[1] = pts[np.argmin(diff)]  # yläoikea
            rect[3] = pts[np.argmax(diff)]  # alavasen
            
            # Laske suorakulmion koko
            (tl, tr, br, bl) = rect
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            
            # Varmista että koko on järkevä
            if maxWidth > 50 and maxHeight > 50:
                # Määritä kohdepisteet suorakulmiolle
                dst = np.array([
                    [0, 0],
                    [maxWidth - 1, 0],
                    [maxWidth - 1, maxHeight - 1],
                    [0, maxHeight - 1]
                ], dtype=np.float32)
                
                # Laske perspektiivin muunnosmatriisi
                M = cv2.getPerspectiveTransform(rect, dst)
                
                # Sovella perspektiivin korjaus
                warped = cv2.warpPerspective(img_array, M, (maxWidth, maxHeight))
                
                # Muunna takaisin PIL Image:ksi
                # Muunna BGR -> RGB
                if len(warped.shape) == 3:
                    warped = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
                else:
                    warped = cv2.cvtColor(warped, cv2.COLOR_GRAY2RGB)
                
                return Image.fromarray(warped)
        
        # Jos ei löytynyt 4 kulmaa tai perspektiivin korjaus epäonnistui, käytä bounding boxia
        # Lisää marginaali
        margin = 20
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(img_array.shape[1] - x, w + 2 * margin)
        h = min(img_array.shape[0] - y, h + 2 * margin)
        
        # Rajaa kuva
        cropped = img_array[y:y+h, x:x+w]
        
        # Muunna takaisin PIL Image:ksi
        if len(cropped.shape) == 3:
            cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        else:
            cropped = cv2.cvtColor(cropped, cv2.COLOR_GRAY2RGB)
        
        return Image.fromarray(cropped)
        
        # Jos löytyi 4 kulmaa, käytä perspektiivin korjausta
        if len(approx) == 4:
            # Järjestä kulmat: ylävasen, yläoikea, alaoikea, alavasen
            pts = approx.reshape(4, 2)
            rect = np.zeros((4, 2), dtype=np.float32)
            
            # Laske summa ja erotus löytääksemme kulmat
            s = pts.sum(axis=1)
            diff = np.diff(pts, axis=1)
            
            rect[0] = pts[np.argmin(s)]  # ylävasen (pienin summa)
            rect[2] = pts[np.argmax(s)]  # alaoikea (suurin summa)
            rect[1] = pts[np.argmin(diff)]  # yläoikea
            rect[3] = pts[np.argmax(diff)]  # alavasen
            
            # Laske suorakulmion koko
            (tl, tr, br, bl) = rect
            widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
            widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
            maxWidth = max(int(widthA), int(widthB))
            
            heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
            heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
            maxHeight = max(int(heightA), int(heightB))
            
            # Varmista että koko on järkevä
            if maxWidth > 50 and maxHeight > 50:
                # Määritä kohdepisteet suorakulmiolle
                dst = np.array([
                    [0, 0],
                    [maxWidth - 1, 0],
                    [maxWidth - 1, maxHeight - 1],
                    [0, maxHeight - 1]
                ], dtype=np.float32)
                
                # Laske perspektiivin muunnosmatriisi
                M = cv2.getPerspectiveTransform(rect, dst)
                
                # Sovella perspektiivin korjaus
                warped = cv2.warpPerspective(img_array, M, (maxWidth, maxHeight))
                
                # Muunna takaisin PIL Image:ksi
                # Muunna BGR -> RGB
                if len(warped.shape) == 3:
                    warped = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
                else:
                    warped = cv2.cvtColor(warped, cv2.COLOR_GRAY2RGB)
                
                return Image.fromarray(warped)
        
        # Jos ei löytynyt 4 kulmaa tai perspektiivin korjaus epäonnistui, käytä bounding boxia
        # Lisää marginaali
        margin = 20
        x = max(0, x - margin)
        y = max(0, y - margin)
        w = min(img_array.shape[1] - x, w + 2 * margin)
        h = min(img_array.shape[0] - y, h + 2 * margin)
        
        # Rajaa kuva
        cropped = img_array[y:y+h, x:x+w]
        
        # Muunna takaisin PIL Image:ksi
        if len(cropped.shape) == 3:
            cropped = cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)
        else:
            cropped = cv2.cvtColor(cropped, cv2.COLOR_GRAY2RGB)
        
        return Image.fromarray(cropped)
    
    except Exception as e:
        # Jos jokin meni pieleen, palauta alkuperäinen kuva
        # Tämä on turvallinen fallback
        return image


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Esikäsittelee kuvan OCR:ää varten.
    Optimoi kuvan tekstin tunnistusta varten parantamalla kontrastia ja terävyyttä.
    
    Args:
        image: PIL Image -objekti
        
    Returns:
        Image.Image: Esikäsitelty kuva
    """
    # Varmista että kuva on RGB
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 1. Muunna harmaasävyksi (OCR toimii usein paremmin harmaasävyllä)
    gray = image.convert('L')
    
    # 2. Autocontrast - parantaa musta-valko kontrastia automaattisesti
    # Tämä on tärkein - se korostaa tekstin taustaa vasten
    gray = ImageOps.autocontrast(gray, cutoff=1)  # Pieni cutoff, ei liian aggressiivinen
    
    # 3. Paranna kontrastia hieman lisää (maltillisesti)
    enhancer = ImageEnhance.Contrast(gray)
    gray = enhancer.enhance(1.3)  # 1.3x on maltillinen
    
    # 4. Paranna terävyyttä (maltillisesti)
    enhancer = ImageEnhance.Sharpness(gray)
    gray = enhancer.enhance(1.5)  # 1.5x on maltillinen
    
    # 5. Muunna takaisin RGB:ksi (pytesseract toimii hyvin myös L:llä, mutta RGB on turvallisempi)
    image = gray.convert('RGB')
    
    return image


def extract_from_pdf(file) -> str:
    """
    Erottaa tekstin PDF-tiedostosta.
    
    Args:
        file: Streamlit UploadedFile tai file-like object
        
    Returns:
        str: Erotettu teksti
    """
    try:
        # Lue PDF-tiedosto
        pdf_bytes = file.read()
        pdf_file = io.BytesIO(pdf_bytes)
        
        # Erota teksti kaikilta sivuilta
        text_parts = []
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    # Varmista että teksti on UTF-8 merkkijono
                    if isinstance(page_text, bytes):
                        page_text = page_text.decode('utf-8', errors='replace')
                    text_parts.append(page_text)
        
        result = "\n\n".join(text_parts)
        # Varmista että lopputulos on UTF-8
        if isinstance(result, bytes):
            result = result.decode('utf-8', errors='replace')
        return result
    except Exception as e:
        raise Exception(f"Virhe PDF-tiedoston lukemisessa: {str(e)}")


def extract_from_image(file) -> str:
    """
    Suorittaa OCR-analyysin kuvatiedostosta.
    
    Args:
        file: Streamlit UploadedFile tai file-like object
        
    Returns:
        str: Erotettu teksti OCR:llä
    """
    try:
        # Resetoi tiedosto-osoitin alkuun (jos mahdollista)
        if hasattr(file, 'seek'):
            file.seek(0)
        
        # Lue kuva
        image_bytes = file.read()
        
        # Tarkista että tiedosto ei ole tyhjä
        if not image_bytes or len(image_bytes) == 0:
            raise ValueError("Kuvatiedosto on tyhjä")
        
        # Resetoi taas (Streamlit UploadedFile tarvitsee tämän)
        if hasattr(file, 'seek'):
            file.seek(0)
        
        # Tarkista tiedostomuoto ennen avaamista
        try:
            # Yritä avata kuva BytesIO:sta
            image = Image.open(io.BytesIO(image_bytes))
            
            # MPO-kuvat (iPhone stereokuvat) tarvitsevat erityiskäsittelyn
            # MPO-kuvat ovat jo RGB-muodossa, mutta format on 'MPO'
            # Kopioi kuva uuteen objektin jotta se voidaan käsitellä normaalisti
            if image.format == 'MPO':
                image = image.copy()
            else:
                # Muille kuville, varmista että kuva on validi
                try:
                    image.verify()
                    # verify() poistaa kuvan, joten avataan uudelleen
                    image = Image.open(io.BytesIO(image_bytes))
                except Exception:
                    # Jos verify epäonnistui, käytä kuvaa sellaisenaan
                    pass
        
        except Exception as e:
            # Jos avaaminen epäonnistui, yritä uudelleen ilman verifya
            image = Image.open(io.BytesIO(image_bytes))
            # Jos se on MPO, kopioi se
            if image.format == 'MPO':
                image = image.copy()
        
        # Tarkista että kuva on validi
        if not image:
            raise ValueError("Kuvaa ei voitu avata")
        
        # Muunna kuva RGB-muotoon (tarvitaan OCR:lle)
        # Käsittele erilaiset kuvamuodot
        if image.mode in ('RGBA', 'LA', 'P'):
            # Luo taustakuva valkoisella
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if image.mode in ('RGBA', 'LA'):
                # Käsittele maski oikein
                if image.mode == 'RGBA':
                    background.paste(image, mask=image.split()[-1])
                else:
                    background.paste(image)
            image = background
        elif image.mode not in ('RGB', 'L', '1'):
            # Muunna kaikki muut muodot RGB:ksi
            try:
                image = image.convert('RGB')
            except Exception as e:
                raise ValueError(f"Kuvamuotoa {image.mode} ei voitu muuntaa RGB:ksi: {str(e)}")
        
        # Varmista että kuva on nyt RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # AUTOMAATTINEN KUITIN ALUEEN TUNNISTUS JA RAJAUS
        # Tämä yrittää tunnistaa kuitin rajat ja rajata kuvan vain kuitin alueelle
        image = detect_and_crop_receipt(image)
        
        # ESIKÄSITTELE KUVA OCR:ÄÄ VARTEN
        # Tämä parantaa kontrastia, terävyyttä ja optimoi kuvan tekstin tunnistusta varten
        image = preprocess_image_for_ocr(image)
        
        # Suorita OCR parannetuilla parametreilla
        # PSM 6 = Yksittäinen yhtenäinen tekstilohko (sopii kuiteille)
        # OEM 3 = Käytä parasta saatavilla olevaa OCR-moottoria
        try:
            text = pytesseract.image_to_string(
                image, 
                lang='fin+eng',
                config='--psm 6 --oem 3'
            )
        except Exception as lang_error:
            # Jos fin+eng ei toimi, kokeile pelkkää englantia
            try:
                text = pytesseract.image_to_string(
                    image, 
                    lang='eng',
                    config='--psm 6 --oem 3'
                )
            except Exception:
                # Jos kielituki ei toimi, käytä oletuskieltä
                text = pytesseract.image_to_string(
                    image,
                    config='--psm 6 --oem 3'
                )
        
        # Varmista että teksti on UTF-8 merkkijono
        if isinstance(text, bytes):
            text = text.decode('utf-8', errors='replace')
        
        # Poista ylimääräiset tyhjät rivit
        text = text.strip()
        
        if not text:
            return "Kuvasta ei löytynyt tekstiä. Varmista että kuva on selkeä ja sisältää luettavaa tekstiä."
        
        return text
    except Image.UnidentifiedImageError as e:
        raise Exception(f"Kuvatiedostoa ei voitu tunnistaa. Varmista että tiedosto on validi kuvatiedosto (JPG, PNG, jne.). Virhe: {str(e)}")
    except Exception as e:
        # Lisää tarkempi virheilmoitus
        error_msg = str(e)
        if "Unsupported image format" in error_msg or "cannot identify image file" in error_msg.lower():
            raise Exception(f"Kuvatiedostomuotoa ei tueta. Tuetut muodot: JPG, JPEG, PNG, GIF, BMP, TIFF. Virhe: {error_msg}")
        raise Exception(f"Virhe OCR-analyysissä: {error_msg}")


def extract_text(file) -> str:
    """
    Automaattinen tiedostotyypin tunnistus ja tekstin erottelu.
    
    Args:
        file: Streamlit UploadedFile tai file-like object
        
    Returns:
        str: Erotettu teksti
    """
    file_type = file.type.lower()
    file_name = file.name.lower()
    
    # Tunnista tiedostotyyppi
    if file_type == 'application/pdf' or file_name.endswith('.pdf'):
        return extract_from_pdf(file)
    elif file_type.startswith('image/') or any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff']):
        return extract_from_image(file)
    else:
        raise ValueError(f"Tiedostotyyppiä {file_type} ei tueta. Tuetut tyypit: PDF ja kuvatiedostot (JPG, PNG, jne.)")
