import streamlit as st
import cv2
import numpy as np
import easyocr
import re

# 1. База данни за Е-номера
E_NUMBERS = {
    "E102": {"name": "Тартразин", "status": "вреден", "reason": "Изкуствен оцветител.", "diseases": "Хиперактивност при деца, тежки алергични реакции и астма."},
    "E211": {"name": "Натриев бензоат", "status": "вреден", "reason": "Химически консервант.", "diseases": "В комбинация с Витамин Ц образува бензен, който уврежда ДНК и увеличава риска от левкемия."},
    "E250": {"name": "Натриев нитрит", "status": "вреден", "reason": "Фиксатор на цвета в месата.", "diseases": "Образува нитрозамини в стомаха, които са пряко свързани с рак на дебелото черво."},
    "E621": {"name": "Мононатриев глутамат", "status": "вреден", "reason": "Подобрител на вкуса.", "diseases": "Пристрастяване към храната, главоболие, сърцебиене и увреждане на нервните клетки (невротоксичност)."},
    "E951": {"name": "Аспартам", "status": "вреден", "reason": "Изкуствен подсладител.", "diseases": "Мигрена, световъртеж, депресия и потенциални дългосрочни неврологични увреждания."}
}

# 2. База данни за съставки на изследвания продукт (Течен шоколад)
INGREDIENTS = {
    "ЗАХАР": {
        "status": "вреден", 
        "reason": "Рафинирана бяла захар на първо място в състава.", 
        "diseases": "Диабет тип 2, затлъстяване, зъбен кариес, мастен черен дроб и хронични възпаления.",
        "alternative": "Домашен течен шоколад, подсладен с фурми, мед или стевия.",
        "match": ["ЗАХАР", "SUGAR"]
    },
    "ПАЛМОВО МАСЛО": {
        "status": "вреден", 
        "reason": "Рафинирана наситена мазнина за евтина текстура.", 
        "diseases": "Запушване на артериите (атеросклероза), повишаване на лошия холестерол (LDL) и висок риск от инфаркт.",
        "alternative": "Продукти с чисто какаово масло, кокосово масло или студено пресован зехтин.",
        "match": ["ПАЛМОВО", "PALM OIL", "PALM FAT"]
    },
    "ОБЕЗМАСЛЕНО МЛЯКО НА ПРАХ": {
        "status": "внимание", 
        "reason": "Млечен концентрат с високо съдържание на лактоза.", 
        "diseases": "Лактозна непоносимост, подуване на корема, газове и кожни проблеми (акне).",
        "alternative": "Ядкови млека (бадемово, овесено, кокосово) без добавена захар.",
        "match": ["МЛЯКО НА ПРАХ", "POWDERED MILK", "СУРОВАТКА"]
    },
    "ЛЕШНИЦИ": {
        "status": "полезен", 
        "reason": "Естествен източник на полезни мазнини и протеини.", 
        "diseases": "Няма налични (полезен продукт, освен при алергия).",
        "alternative": "Сурови или печени лешници без сол и захар.",
        "match": ["ЛЕШНИЦИ", "HAZELNUTS", "ЛЕШНИКОВА"]
    },
    "КАКАО НА ПРАХ": {
        "status": "полезен", 
        "reason": "Богато на антиоксиданти и магнезий.", 
        "diseases": "Няма налични (намалява стреса и подобрява кръвообращението).",
        "alternative": "Чисто 100% сурово какао или какаови зърна.",
        "match": ["КАКАО", "COCOA", "CACAO"]
    }
}

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['bg', 'en'])

reader = load_ocr()

st.title("🍎 Проект: Скенер на Хранителни Етикети")
st.write("Качете снимка на хранителен продукт за изчисляване на здравен рейтинг.")

uploaded_file = st.file_uploader("Изберете снимка на етикет...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)
    st.image(image, channels="BGR", caption="Качен етикет за анализ", use_container_width=True)
    
    with st.spinner("Четене на съставките..."):
        results = reader.readtext(image, detail=0)
        full_text = " ".join(results).upper()
        
    st.subheader("📝 Разпознати съставки от снимката:")
    st.write(full_text)
    
    score = 100
    analyzed_any = False
    has_harmful = False
    alternatives_to_show = []
    
    st.subheader("🔍 Здравен анализ на състава:")
    
    # 1. Анализ на Е-номера
    found_codes = re.findall(r'E\s*\d{3}[A-Z]?', full_text)
    cleaned_codes = list(set([code.replace(" ", "") for code in found_codes]))
    
    if cleaned_codes:
        analyzed_any = True
        for code in cleaned_codes:
            if code in E_NUMBERS:
                info = E_NUMBERS[code]
                if info["status"] == "вреден":
                    st.error(f"🚨 **{code} ({info['name']})** - ВРЕДЕН")
                    st.write(f"ℹ️ *Защо:* {info['reason']}")
                    st.write(f"⚠️ *Здравни проблеми:* {info['diseases']}")
                    score -= 25
                    has_harmful = True
            else:
                st.warning(f"⚠️ **{code}** - Намерено Е-число, което липсва в базата данни.")

    # 2. Анализ на обикновени съставки
    for ing_name, details in INGREDIENTS.items():
        if any(keyword in full_text for keyword in details["match"]):
            analyzed_any = True
            if details["status"] == "вреден":
                st.error(f"🚨 **{ing_name}** - ВРЕДНА СЪСТАВКА")
                st.write(f"ℹ️ *Защо:* {details['reason']}")
                st.write(f"⚠️ *Здравни проблеми:* {details['diseases']}")
                score -= 25
                has_harmful = True
                if "alternative" in details:
                    alternatives_to_show.append((ing_name, details["alternative"]))
            elif details["status"] == "внимание":
                st.warning(f"⚠️ **{ing_name}** - С повишено внимание: {details['reason']}")
                st.write(f"🛑 *Проблеми:* {details['diseases']}")
                score -= 10
            else:
                st.success(f"✅ **{ing_name}** - ПОЛЕЗНА СЪСТАВКА: {details['reason']}")
                score += 5

    # Ограничаване на крайния резултат между 0 и 100
    score = max(0, min(score, 100))
    
    # 3. Крайно заключение и визуализиране на резултата
    st.subheader("📊 Генерално заключение за продукта:")
    
    if not analyzed_any:
        st.info("Текстът на опаковката не съдържа съставки, съвпадащи с нашата база данни.")
    else:
        if score >= 80:
            st.success(f"🍏 Здравен рейтинг: {score}/100. Продуктът е чист и безопасен!")
            st.balloons()
        elif score >= 50:
            st.warning(f"🥦 Здравен рейтинг: {score}/100. Средно качество, консумирайте умерено.")
        else:
            st.error(f"❌ Здравен рейтинг: {score}/100. Продуктът е силно преработен и вреден!")

        # Показване на алтернативи при открити вредни елементи
        if has_harmful and alternatives_to_show:
            st.subheader("💡 Здравословни алтернативи на пакетираната храна:")
            for ing, alt in alternatives_to_show:
                st.info(f"🌿 Вместо продукт с **{ing}**, изберете: **{alt}**")
                
