# Enterprise Analytics, Business Intelligence & AI Decision Support (EABI) Documentation

This document describes the dashboard configurations, dashboard widgets, key performance indicators, report definitions, executions, analytical snapshot caches, OLAP multidimensional cubes, and AI predictions of the **analytics** app.

---

## 1. Dashboards & Indicators
- **Dashboard**: Role-restricted dashboard parameters.
- **DashboardWidget**: Chart and graph metrics layouts.
- **KPI**: Reusable performance averages caches.

---

## 2. Report Pipelines
- **ReportDefinition**: Custom report layout metadata templates.
- **ReportExecution**: Immutable archives of executed files.

---

## 3. OLAP Data Cubes & AI Predictions
- **AnalyticsSnapshot**: Daily metric caches.
- **DataCube**: Multi-dimensional OLAP summaries.
- **PredictiveInsight**: Dropout/fee-default AI forecasts.

---

## 4. REST APIs
Endpoints are mapped under `/analytics/api/v1/`:
- `GET/POST /analytics/dashboards/`: Dashboard lists.
- `GET/POST /analytics/kpis/`: Cached KPIs.
- `GET/POST /analytics/reports/`: Reports list templates.
