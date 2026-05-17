import streamlit as st
import cv2
import numpy as np
import easyocr
import re

# 1. База данни с Е-номера
E_NUMBERS = {
    "E102": {"name": "Тартразин", "status": "вреден", "reason": "Алерген, може да причини хиперактивност при деца."},
    "E122": {"name": "Азорубин", "status": "вреден", "reason": "Забранен в някои страни, съмнения за канцерогенност."},
    "E211": {"name": "Натриев бензоат", "status": "вреден", "reason": "Консервант. В комбинация с Витамин Ц образува бензен (канцероген)."},
    "E250": {"name": "Натриев нитрит", "status": "вреден", "reason": "Използва се в колбаси. Може да образува нитрозамини."},
    "E621": {"name": "Мононатриев глутамат", "status": "вреден", "reason": "Повреди на вкусовите рецептори, главоболие."},
    "E951": {"name": "Аспартам", "status": "вреден", "reason": "Изкуствен подсладител. Свързва се с главоболие и неврологични проблеми."},
    "E100": {"name": "Куркумин", "status": "полезен", "reason": "Естествени противовъзпалителни свойства."},
    "E160a": {"name": "Каротини", "status": "полезен", "reason": "Провитамин А. Мощен антиоксидант."},
    "E300": {"name": "Аскорбинова киселина", "status": "полезен", "reason": "Чист Витамин Ц. Антиоксидант."},
    "E322": {"name": "Лецитин", "status": "полезен", "reason": "Полезен за мозъка и черния дроб."},
    "E440": {"name": "Пектин", "status": "полезен", "reason": "Естествени фибри. Помага на храносмилането."}
}

# 2. Нова база данни за обикновени съставки (BG и EN)
INGREDIENTS = {
    # Вредни съставки
    "ЗАХАР": {"status": "вреден", "reason": "Високо съдържание на захар. Риск от диабет и затлъстяване.", "match": ["ЗАХАР", "SUGAR"]},
    "ПАЛМОВО МАСЛО": {"status": "вреден", "reason": "Хидрогенирани мазнини, лоши за сърцето и артериите.", "match": ["ПАЛМОВО", "PALM OIL"]},
    "ГЛЮКОЗО-ФРУКТОЗЕН СИРОП": {"status": "вреден", "reason": "Евтин подсладител, води до бързо натрупване на мазнини.", "match": ["ГЛЮКОЗО", "ФРУКТОЗЕН", "FRUCTOSE SYRUP"]},
    "МАРГАРИН": {"status": "вреден", "reason": "Източник на транс-мазнини, които запушват кръвоносните съдове.", "match": ["МАРГАРИН", "MARGARINE", "ХИДРОГЕНИРАНИ"]},
    "АСПАРТАМ": {"status": "вреден", "reason": "Изкуствен подсладител с негативно влияние върху нервната система.", "match": ["АСПАРТАМ", "ASPARTAME"]},
    
    # Полезни съставки
    "ОДЕСНИ ЯДКИ": {"status": "полезен", "reason": "Сложни въглехидрати и фибри. Дават дълготрайна енергия.", "match": ["ОВЕС", "OAT"]},
    "ПЪЛНОЗЪРНЕСТО БРАШНО": {"status": "полезен", "reason": "Богато на фибри и витамини от група B.", "match": ["ПЪЛНОЗЪРНЕСТО", "WHOLE GRAIN"]},
    "ЗЕХТИН": {"status": "полезен", "reason": "Полезни мононенаситени мазнини, предпазващи сърцето.", "match": ["ЗЕХТИН", "OLIVE OIL"]},
    "МЕД": {"status": "полезен", "reason": "Естествен антиоксидант и подсладител (ако е в умерени количества).", "match": ["МЕД", "HONEY"]},
    "ЧИЯ": {"status": "полезен", "reason": "Богата на Омега-3 мастни киселини и фибри.", "match": ["ЧИЯ", "CHIA"]},
    "ЛЕНЕНО СЕМЕ": {"status": "полезен", "reason": "Отличен източник на фибри и полезни мазнини.", "match": ["ЛЕНЕНО", "FLAXSEED"]}
}

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['bg', 'en'])

reader = load_ocr()

st.title("🍎 Интелигентен Скенер за Храни")
st.write("Качете снимка на етикета. Приложението ще анализира Е-номерата и съставките.")

uploaded_file = st.file_uploader("Изберете снимка на етикет...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)
    
    st.image(image, channels="BGR", caption="Качена снимка", use_container_width=True)
    
    with st.spinner("Четене и анализиране на текста..."):
        results = reader.readtext(image, detail=0)
        full_text = " ".join(results).upper()
        
    st.subheader("📝 Разпознат текст от опаковката:")
    st.write(full_text)
    
    has_harmful = False
    st.subheader("🔍 Резултати от анализа:")
    
    # --- ЧАСТ 1: Проверка за Е-номера ---
    found_codes = re.findall(r'E\s*\d{3}[A-Z]?', full_text)
    cleaned_codes = list(set([code.replace(" ", "") for code in found_codes]))
    
    if cleaned_codes:
        st.write(f"**Открити Е-номера:** {', '.join(cleaned_codes)}")
        for code in cleaned_codes:
            if code in E_NUMBERS:
                info = E_NUMBERS[code]
                if info["status"] == "вреден":
                    st.error(f"🚨 **{code} ({info['name']})** - ВРЕДЕН: {info['reason']}")
                    has_harmful = True
                else:
                    st.success(f"✅ **{code} ({info['name']})** - ПОЛЕЗЕН: {info['reason']}")
            else:
                st.warning(f"⚠️ **{code}** - Няма детайли в базата данни за това Е.")

    # --- ЧАСТ 2: Проверка за думи в състава ---
    found_ingredients = False
    for ing_name, details in INGREDIENTS.items():
        # Проверяваме дали някоя от ключовите думи (BG/EN) присъства в текста
        if any(keyword in full_text for keyword in details["match"]):
            found_ingredients = True
            if details["status"] == "вреден":
                st.error(f"🚨 **{ing_name}** - ВРЕДНА СЪСТАВКА: {details['reason']}")
                has_harmful = True
            else:
                st.success(f"✅ **{ing_name}** - ПОЛЕЗНА СЪСТАВКА: {details['reason']}")
                
    if not cleaned_codes and not found_ingredients:
        st.info("Не открихме специфични Е-номера или ключови съставки от базата данни. Опитайте с по-ясна снимка.")

    # --- ЧАСТ 3: Крайна присъда ---
    st.subheader("📊 Крайна оценка за продукта:")
    if has_harmful:
        st.error("❌ Внимание! Продуктът съдържа съставки, които могат да бъдат вредни за здравето.")
    elif found_ingredients or cleaned_codes:
