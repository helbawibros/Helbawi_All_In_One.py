# استخدام نسخة بايثون مستقرة
FROM python:3.9

# تحديد مكان العمل داخل الحاوية
WORKDIR /code

# نسخ ملف المتطلبات وتثبيتها
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# نسخ باقي ملفات المشروع
COPY . .

# الأمر التشغيلي لتشغيل سريم ليت على المنفذ 7860 (المنفذ الافتراضي لهجينج فيس)
CMD ["streamlit", "run", "app.py", "--server.port", "7860", "--server.address", "0.0.0.0"]
