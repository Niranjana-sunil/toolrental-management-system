from django.db import models

# Create your models here.

class Customers(models.Model):
    username=models.CharField(max_length=10)
    address=models.CharField(max_length=100)
    phone=models.CharField(max_length=10)
    password=models.CharField(max_length=20)


class Tool(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    description = models.TextField()
    price_per_day = models.DecimalField(max_digits=10,decimal_places=2)
    image = models.ImageField(upload_to='tools/',blank=True,null=True)
    count=models.IntegerField(default=0)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name



class Rental(models.Model):
    STATUS_CHOICES = [
    ('Pending', 'Pending'),
    ('Approved', 'Approved'),
    ('Rejected', 'Rejected'),
    ('Active', 'Active'),
    ('Completed', 'Completed'),
    ('Cancelled', 'Cancelled'),
]

    customer = models.ForeignKey(Customers,on_delete=models.CASCADE,related_name='rentals')
    tool = models.ForeignKey(Tool,on_delete=models.CASCADE,related_name='rentals')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10,decimal_places=2)
    status = models.CharField(max_length=20,choices=STATUS_CHOICES,default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.username} - {self.tool.name}"

    def calculate_total_days(self):
        days = (self.end_date - self.start_date).days + 1
        return max(days, 1)

    def calculate_total_price(self):
        return self.calculate_total_days() * self.tool.price_per_day