import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import NewsletterSubscriber

@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'phone_number', 'full_name', 'source', 'subscribed_at')
    list_filter = ('source', 'subscribed_at')
    search_fields = ('email', 'phone_number', 'full_name')
    date_hierarchy = 'subscribed_at'
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response
    export_as_csv.short_description = "Export Selected as CSV"
