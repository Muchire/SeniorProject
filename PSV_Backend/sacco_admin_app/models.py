from django.db import models
from django.conf import settings
from sacco.models import Sacco

class SaccoAdmin(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sacco_admin'
    )
    sacco = models.ForeignKey(
        Sacco, 
        on_delete=models.CASCADE, 
        related_name='admins'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'sacco')
        verbose_name = 'Sacco Admin'
        verbose_name_plural = 'Sacco Admins'
    
    def __str__(self):
        return f"{self.user.username} - {self.sacco.name} Admin"
