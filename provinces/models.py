from django.db import models


class Province(models.Model):
    name = models.CharField(max_length=50)
    visited_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name
