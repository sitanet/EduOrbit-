import csv
from io import StringIO
from django.http import HttpResponse

class EnterpriseReportEngine:
    """
    Shared Report Engine for exporting tabular dataset reports as CSV, Excel, or PDF across modules.
    """
    @classmethod
    def export_to_csv(cls, filename, headers, rows):
        buffer = StringIO()
        writer = csv.writer(buffer)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
        
        response = HttpResponse(buffer.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        return response
