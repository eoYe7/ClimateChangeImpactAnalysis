from django.db import models

class RegionData(models.Model):
        
    country = models.CharField(max_length=100, default="Unknown")  # إضافة قيمة افتراضية
    date = models.DateField()  # لتخزين التاريخ فقط
    temperature = models.FloatField()
    co2_emissions = models.FloatField()

    def __str__(self):
        return f"{self.date} - {self.country} - {self.temperature}°C - {self.co2_emissions} ppm"
