import csv  # مكتبة CSV لقراءة وكتابة ملفات CSV (قيم مفصولة بفواصل)
from django.shortcuts import render  # استيراد دالة render لعرض الصفحات (تستخدم في عرض القوالب HTML في Django)
from .models import RegionData  # استيراد نموذج RegionData من الملف models.py للوصول إلى البيانات في قاعدة البيانات
import json  # مكتبة JSON للتعامل مع البيانات بصيغة JSON، مثل تحويل الكائنات إلى JSON والعكس
from django.http import HttpResponse  # استيراد HttpResponse لإنشاء استجابات HTTP في Django (مثل إرسال ملف أو رسالة للمستخدم)
from django.db.models import Max, Avg  # استيراد دوال Max وAvg لحساب القيم القصوى والمتوسط من قاعدة البيانات باستخدام Django ORM
from datetime import datetime  # استيراد datetime للعمل مع التواريخ والأوقات في Python
import plotly.express as px  # استيراد مكتبة Plotly Express لإنشاء الرسوم البيانية التفاعلية
import plotly.io as pio  # استيراد مكتبة Plotly IO للتعامل مع رسومات Plotly (مثل حفظ أو عرض الرسومات)
from reportlab.pdfgen import canvas  # استيراد Canvas من ReportLab لإنشاء رسومات PDF من خلال الكود
from reportlab.lib.pagesizes import letter  # استيراد مقاس "letter" من ReportLab لاستخدامه عند إنشاء ملفات PDF
import numpy as np  # استيراد مكتبة NumPy للعمل مع المصفوفات الرياضية والعمليات العددية
from sklearn.linear_model import LinearRegression  # استيراد LinearRegression من scikit-learn لإنشاء نماذج الانحدار الخطي للتنبؤ
import plotly.utils  # استيراد utils من plotl
import pandas as pd


def load_data_from_csv(request):
    with open('D:/Project_django/climate_selected_columns.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            date_only = datetime.strptime(row['Date'].split()[0], "%Y-%m-%d").date()
            RegionData.objects.create(
                country=row['Country'],
                date=date_only,
                temperature=float(row['Temperature']),
                co2_emissions=float(row['CO2 Emissions'])
            )
    return render(request, 'climate_data/data_loaded.html')


def search(request):
    query = request.GET.get('country', None)
    results = RegionData.objects.filter(country__icontains=query) if query else None

    # إضافة الرسوم البيانية إذا كانت هناك نتائج
    if results:
        # جمع البيانات
        dates = [result.date for result in results]
        temperatures = [result.temperature for result in results]
        co2_emissions = [result.co2_emissions for result in results]

        # رسم المخطط الزمني لدرجات الحرارة
        fig_temp = px.line(x=dates, y=temperatures, title="Temperature Over Time")
        temp_chart = pio.to_html(fig_temp, full_html=False)

        # رسم المخطط الزمني لانبعاثات CO2
        fig_co2 = px.line(x=dates, y=co2_emissions, title="CO2 Emissions Over Time")
        co2_chart = pio.to_html(fig_co2, full_html=False)

        # رسم العلاقة بين درجة الحرارة وانبعاثات CO2
        fig_relation = px.scatter(x=co2_emissions, y=temperatures, title="Temperature vs CO2 Emissions", labels={'x': 'CO2 Emissions (ppm)', 'y': 'Temperature (°C)'})
        relation_chart = pio.to_html(fig_relation, full_html=False)

        # تمرير الرسوم البيانية إلى القالب
        return render(request, 'home.html', {
            'results': results,
            'temp_chart': temp_chart,
            'co2_chart': co2_chart,
            'relation_chart': relation_chart
        })
    else:
        return render(request, 'home.html', {'results': None})



def home(request):
    # العثور على أحدث سنة متاحة في قاعدة البيانات
    latest_year = RegionData.objects.aggregate(latest_date=Max('date'))['latest_date'].year

    # استرجاع البيانات لتلك السنة فقط
    data_latest_year = RegionData.objects.filter(date__year=latest_year)

    # العثور على الدولة ذات أعلى متوسط درجة حرارة وانبعاثات CO₂
    highest_impact_country = data_latest_year.values('country').annotate(
        avg_temperature=Avg('temperature'),
        avg_co2=Avg('co2_emissions')
    ).order_by('-avg_temperature', '-avg_co2').first()

    # إعداد الإحصائيات لعرضها
    if highest_impact_country:
        statistics = {
            'country': highest_impact_country['country'],
            'global_temperature_rise': "Global temperature has risen by 1.2°C since the early 21st century.",
            'co2_increase': "CO2 emissions have increased by 40% in recent decades.",
            'agriculture_impact': "Crop yields have been affected by climate change by 30%.",
            'avg_temperature': round(highest_impact_country['avg_temperature'], 2),
            'avg_co2': round(highest_impact_country['avg_co2'], 2),
            'latest_year': latest_year
        }
    else:
        # في حال لم توجد بيانات
        statistics = {
            'country': "No data",
            'global_temperature_rise': "Global temperature has risen by 1.2°C since the early 21st century.",
            'co2_increase': "CO2 emissions have increased by 40% in recent decades.",
            'agriculture_impact': "Crop yields have been affected by climate change by 30%.",
            'avg_temperature': "No data",
            'avg_co2': "No data",
            'latest_year': "No data"
        }
    
    return render(request, 'home_dash.html', {'statistics': statistics})




def temp(request):
    # استعلام لجلب بيانات درجة الحرارة من RegionData
    results = RegionData.objects.all()

    # تجهيز البيانات للرسم البياني
    dates = [result.date.strftime('%Y-%m-%d') for result in results]  # تحويل التواريخ إلى نصوص
    temperatures = [result.temperature for result in results]

    # إنشاء JSON للبيانات
    temp_data = {
        'dates': dates,
        'temperatures': temperatures,
    }
    temp_data_json = json.dumps(temp_data)  # تحويل البيانات إلى JSON

    # تمرير البيانات إلى القالب
    return render(request, 'temp.html', {'results': results, 'temp_data_json': temp_data_json})


def co2(request):
    # استعلام لجلب بيانات انبعاثات CO2 من RegionData
    results = RegionData.objects.all()

    # تجهيز البيانات للرسم البياني
    dates = [result.date.strftime('%Y-%m-%d') for result in results]  # تحويل التواريخ إلى نصوص
    co2_emissions = [result.co2_emissions for result in results]

    # إنشاء JSON للبيانات
    co2_data = {
        'dates': dates,
        'co2_emissions': co2_emissions,
    }
    co2_data_json = json.dumps(co2_data)  # تحويل البيانات إلى JSON

    # تمرير البيانات إلى القالب
    return render(request, 'co2.html', {'co2_data_json': co2_data_json})


def Climaforecast(request):
    # استعلام لجلب بيانات انبعاثات CO2 ودرجات الحرارة من RegionData
    results = RegionData.objects.all()

    # تجهيز البيانات لانبعاثات CO2
    dates = [result.date for result in results]  # تواريخ
    co2_emissions = [result.co2_emissions for result in results]  # انبعاثات CO2

    # تجهيز البيانات لدرجات الحرارة
    temperatures = [result.temperature for result in results]  # درجات الحرارة

    # تحويل التواريخ إلى أرقام (عدد الأيام منذ تاريخ معين)
    base_date = min(dates)  # تحديد أول تاريخ في البيانات
    days_since_base = [(date - base_date).days for date in dates]  # تحويل التواريخ إلى عدد الأيام

    # نموذج الانحدار لCO2
    X = np.array(days_since_base).reshape(-1, 1)  # المتغير المستقل: الأيام
    y_co2 = np.array(co2_emissions)  # المتغير التابع: انبعاثات CO2
    model_co2 = LinearRegression()
    model_co2.fit(X, y_co2)

    # التنبؤ بالانبعاثات المستقبلية لمدة 10 سنوات (3650 يوم)
    future_days = np.array([days_since_base[-1] + i for i in range(1, 3661)]).reshape(-1, 1)
    future_co2_emissions = model_co2.predict(future_days)

    # نموذج الانحدار لدرجة الحرارة
    y_temp = np.array(temperatures)  # المتغير التابع: درجة الحرارة
    model_temp = LinearRegression()
    model_temp.fit(X, y_temp)

    # التنبؤ بدرجات الحرارة المستقبلية لمدة 10 سنوات
    future_temperatures = model_temp.predict(future_days)

    # تجهيز البيانات للرسم البياني
    future_dates = [base_date + np.timedelta64(int(day), 'D') for day in future_days.flatten()]
    future_dates_str = [date.strftime('%Y-%m-%d') for date in future_dates]

    future_co2_data = {
        'dates': future_dates_str,
        'co2_emissions': future_co2_emissions.tolist(),
    }

    future_temp_data = {
        'dates': future_dates_str,
        'temperatures': future_temperatures.tolist(),
    }

    co2_data_json = json.dumps(future_co2_data)  # تحويل البيانات إلى JSON
    temp_data_json = json.dumps(future_temp_data)  # تحويل بيانات درجات الحرارة إلى JSON

    # تمرير البيانات إلى القالب
    return render(request, 'climaforecast.html', {'co2_data_json': co2_data_json, 'temp_data_json': temp_data_json})



def heatMaps(request):
    # جلب بيانات درجات الحرارة واسم البلد من قاعدة البيانات
    data = RegionData.objects.values('country').distinct()

    # جلب إحداثيات البلدان
    country_coordinates = {
        'USA': {'latitude': 37.0902, 'longitude': -95.7129},
        'Canada': {'latitude': 56.1304, 'longitude': -106.3468},
        'India': {'latitude': 20.5937, 'longitude': 78.9629},
        'Brazil': {'latitude': -14.2350, 'longitude': -51.9253},
        'Australia': {'latitude': -25.2744, 'longitude': 133.7751}
    }

    # جمع البيانات للحرارة
    heat_map_data = []
    
    for entry in data:
        country = entry['country']
        avg_temperature = RegionData.objects.filter(country=country).aggregate(Avg('temperature'))['temperature__avg']
        
        # إذا كان هناك درجة حرارة متاحة، قم بإضافتها إلى الخريطة الحرارية
        if avg_temperature is not None:
            # جلب الإحداثيات من القاموس أو وضع إحداثيات افتراضية
            coordinates = country_coordinates.get(country, {'latitude': 0, 'longitude': 0})
            heat_map_data.append({
                'country': country,
                'avg_temperature': avg_temperature,
                'coordinates': coordinates
            })

    # تحويل البيانات إلى تنسيق JSON ليتم تمريرها إلى JavaScript
    heat_map_data_json = json.dumps(heat_map_data)

    # إرسال البيانات إلى القالب
    return render(request, 'heat_maps.html', {'heat_map_data': heat_map_data_json})

def export_data(request):
    # افتراضياً نستخدم CSV كصيغة
    export_format = request.POST.get('format', 'csv')  # إذا لم يتم اختيار، سيكون الافتراضي CSV
    include_charts = request.POST.get('include_charts', False)  # إذا كان البيانات مع الرسوم البيانية أو لا

    # تحديد البيانات التي سيتم تصديرها
    data = RegionData.objects.all()

    if export_format == 'pdf':
        # تصدير البيانات إلى PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="climate_data.pdf"'

        c = canvas.Canvas(response, pagesize=letter)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 750, "Climate Change Data Report")

        c.setFont("Helvetica", 10)
        y_position = 730
        for record in data:
            c.drawString(100, y_position, f"Country: {record.country}")
            c.drawString(200, y_position, f"Date: {record.date}")
            c.drawString(300, y_position, f"Temperature: {record.temperature}")
            c.drawString(400, y_position, f"CO2 Emissions: {record.co2_emissions}")
            y_position -= 20
            if y_position < 50:
                c.showPage()
                c.setFont("Helvetica", 10)
                y_position = 750
        c.save()
        return response

    elif export_format == 'csv':
        # تصدير البيانات إلى CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="climate_data.csv"'

        writer = csv.writer(response)
        writer.writerow(['Country', 'Date', 'Temperature', 'CO2 Emissions'])

        for record in data:
            writer.writerow([record.country, record.date, record.temperature, record.co2_emissions])

        return response


def heatMaps(request):
    # تأكد من أنك تقوم بجلب البيانات الصحيحة في التطبيق الخاص بك
    data = {
        'Country': ['USA', 'Canada', 'Brazil', 'India', 'China'],
        'Precipitation': [1200, 1500, 2000, 800, 1000]
    }
    df = pd.DataFrame(data)

    # تجميع البيانات حسب الدولة وحساب متوسط المتساقطات
    precipitation_by_country = df.groupby('Country').agg({'Precipitation': 'mean'}).reset_index()

    # إنشاء الرسم البياني باستخدام Plotly
    fig_precipitation = px.choropleth(
        precipitation_by_country,
        locations="Country",
        locationmode="country names",
        color="Precipitation",
        hover_name="Country",
        color_continuous_scale="Viridis",
        title="Global Precipitation Heat Map"
    )

    # تحويل الرسم البياني إلى JSON باستخدام PlotlyJSONEncoder
    graph_json = json.dumps(fig_precipitation, cls=plotly.utils.PlotlyJSONEncoder)

    # تمرير البيانات إلى القالب
    return render(request, 'heat_maps.html', {'graph_json': graph_json})