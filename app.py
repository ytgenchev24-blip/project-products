import streamlit as st
import cv2
import numpy as np
import easyocr
import re

# 1. База данни с Е-номера (примерна, може да се допълва)
E_NUMBERS = {
    # Вредни / Опасни
    "E102": {"name": "Тартразин", "status": "вреден", "reason": "Алерген, може да причини хиперактивност при деца."},
    "E122": {"name": "Азорубин", "status": "вреден", "reason": "Забранен в някои страни, съмнения за канцерогенност."},
    "E211": {"name": "Натриев бензоат", "status": "вреден", "reason": "Консервант, който в комбинация с Витамин Ц образува бензен (канцероген)."},
    "E250": {"name": "Натриев нитрит", "status": "вреден", "reason": "Използва се в колбасите. Може да образува нитрозамини, които са канцерогенни."},
    "E621": {"name": "Мононатриев глутамат", "status": "вреден", "reason": "Повреди на вкусовите рецептори, главоболие (синдром на китайския ресторант)."},
    "E951": {"name": "Аспартам", "status": "вреден", "reason": "Изкуствен подсладител. Свързва се с главоболие и неврологични проблеми."},
    
    # Безопасни / Полезни
    "E100": {"name": "Куркумин", "status": "полезен", "reason": "Естествен оцветител от куркума. Има противовъзпалителни свойства."},
    "E160a": {"name": "Каротини", "status": "полезен", "reason": "Провитамин А, извлечен от моркови. Мощен антиоксидант."},
    "E300": {"name": "Аскорбинова киселина", "status": "полезен", "reason": "Чист Витамин Ц. Антиоксидант и естествен консервант."},
    "E322": {"name": "Лецитин", "status": "полезен", "reason": "Естествен емулгатор (често от соя или яйца). Полезен за мозъка и черния дроб."},
    "E440": {"name": "Пектин", "status": "полезен", "reason": "Естествени фибри от ябълки или цитруси. Помага на храносмилането."}
}

# Инициализиране на EasyOCR (зарежда се веднъж)
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['bg', 'en']) # Поддържа български и английски

reader = load_ocr()

# Заглавие на приложението
st.title("🍎 Скенер за Е-номера в храните")
st.write("Качете снимка на етикета със съставките, за да проверите дали продуктът е вреден.")

# Качване на снимка
uploaded_file = st.file_uploader("Изберете снимка...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Конвертиране на файла в изображение за OpenCV (КОРИГИРАНО НА np.uint8)
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    image = cv2.imdecode(file_bytes, 1)
    
    # Показване на качената снимка
    st.image(image, channels="BGR", caption="Качена снимка", use_container_width=True)
    
    with st.spinner("Четене на текста от снимката..."):
        # Извличане на текст чрез EasyOCR
        results = reader.readtext(image, detail=0)
        full_text = " ".join(results).upper()
        
    st.subheader("Намерен текст:")
    st.write(full_text)
    
    # Търсене на Е-номера чрез Regular Expressions (напр. Е102, Е 300, E621)
    found_codes = re.findall(r'E\s*\d{3}[A-Z]?', full_text)
    # Изчистване на шпациите (напр. "E 300" става "E300")
    cleaned_codes = [code.replace(" ", "") for code in found_codes]
    # Премахване на дубликати
    unique_codes = list(set(cleaned_codes))
    
    st.subheader("🔍 Анализ на съставките:")
    
    if not unique_codes:
        st.info("Не бяха открити разпознаваеми Е-номера на снимката. Проверете дали текстът се вижда ясно.")
    else:
        st.write(f"Открити Е-номера: {', '.join(unique_codes)}")
        
        has_harmful = False
        
        for code in unique_codes:
            if code in E_NUMBERS:
                info = E_NUMBERS[code]
                name = info["name"]
                status = info["status"]
                reason = info["reason"]
                
                if status == "вреден":
                    st.error(f"🚨 **{code} ({name})** - ВРЕДЕН")
                    st.write(f"👉 *Причина:* {reason}")
                    has_harmful = True
                else:
                    st.success(f"✅ **{code} ({name})** - ПОЛЕЗЕН / БЕЗОПАСЕН")
                    st.write(f"👉 *Полза:* {reason}")
            else:
                st.warning(f"⚠️ **{code}** - Няма информация за това Е-номер в нашата база данни.")
        
        # Обща оценка
        st.subheader("📊 Крайна оценка за продукта:")
        if has_harmful:
            st.error("❌ Продуктът съдържа вредни съставки! Не се препоръчва за честа консумация.")
        else:
            st.success("🍏 Продуктът изглежда безопасен (няма открити вредни Е-номера).")
