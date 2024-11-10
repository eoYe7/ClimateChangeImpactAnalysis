import csv
import numpy as np
from sklearn.linear_model import LinearRegression
import json
from django.db.models import Max, Avg
from .models import RegionData
from django.shortcuts import render
from django.db import models
from datetime import datetime
import plotly.express as px
import plotly.io as pio
from django.db.models import Avg
import pydeck as pdk
from django.http import HttpResponse
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

# def home(request):
#     return render(request, 'home.html')

def about(request):
    return render(request, 'climate_data/about.html')



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


    # إذا كانت هناك نتائج
    if results:
        # جمع البيانات المطلوبة: التاريخ ودرجة الحرارة واسم الدولة
        dates = [result.date for result in results]
        temperatures = [result.temperature for result in results]
        countries = [result.country for result in results]

        # رسم المخطط الزمني لدرجات الحرارة
        fig_temp = px.line(x=dates, y=temperatures, title="Temperature Over Time")
        temp_chart = pio.to_html(fig_temp, full_html=False)

        # تمرير البيانات إلى القالب temp.html
        return render(request, 'temp.html', {
            'results': results,
            'temp_chart': temp_chart,
        })
    else:
        return render(request, 'temp.html', {'results': None})

# def home_dash(request):
#     # your logic here
#     return render(request, 'home_dash.html')


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




from django.shortcuts import render
from django.db.models import Avg
import json

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

    # جمع البيانات
    heat_map_data = []
    
    for entry in data:
        country = entry['country']
        avg_temperature = RegionData.objects.filter(country=country).aggregate(Avg('temperature'))['temperature__avg']
        
        # إذا كان هناك درجة حرارة متاحة، قم بإضافتها إلى الخريطة الحرارية
        if avg_temperature is not None:
            heat_map_data.append({
                'country': country,
                'avg_temperature': avg_temperature,
                'coordinates': country_coordinates.get(country, {'latitude': 0, 'longitude': 0})
            })

    # تحويل البيانات إلى تنسيق JSON ليتم تمريرها إلى JavaScript
    heat_map_data_json = json.dumps(heat_map_data)

    # إرسال البيانات إلى القالب
    return render(request, 'heat_maps.html', {'heat_map_data': heat_map_data_json})
