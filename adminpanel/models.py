from django.db import models
from django.contrib.auth.models import User

class SystemLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('IMPORT', 'Import'),
        ('EXPORT', 'Export'),
        ('BULK_UPDATE', 'Bulk Update'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=50)
    object_id = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action_type} - {self.object_type} by {self.user} at {self.timestamp}"
