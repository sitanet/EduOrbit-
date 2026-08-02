import json
import os

backend_dir = r"c:\Users\user\Desktop\Development\SMS\backend"
with open(os.path.join(backend_dir, "scratch", "urlconf_rbac_audit.json"), "r") as f:
    data = json.load(f)

total_routes = len(data)
parameterized_routes = sum(1 for r in data if r['is_parameterized'])
static_routes = sum(1 for r in data if not r['is_parameterized'])

status_500_routes = []
status_404_routes = []
public_routes = []
protected_routes = []

for r in data:
    if not r['is_parameterized'] and r['responses']:
        statuses = set(r['responses'].values())
        if 500 in statuses:
            status_500_routes.append(r)
        if 404 in statuses:
            status_404_routes.append(r)
        if statuses == {200}:
            public_routes.append(r)
        elif 403 in statuses or 302 in statuses:
            protected_routes.append(r)

print(f"Total Routes Registered: {total_routes}")
print(f"Parameterized Routes: {parameterized_routes}")
print(f"Static Routes Audited: {static_routes}")
print(f"Public Unprotected Routes (200 for all roles): {len(public_routes)}")
print(f"Protected Routes (403 for unauthorized roles): {len(protected_routes)}")
print(f"HTTP 500 Exception Routes: {len(status_500_routes)}")
print(f"HTTP 404 Not Found Routes: {len(status_404_routes)}")

# Dump structured report file
with open(os.path.join(backend_dir, "scratch", "urlconf_summary.json"), "w") as out:
    json.dump({
        'total_routes': total_routes,
        'parameterized_routes': parameterized_routes,
        'static_routes': static_routes,
        'public_routes_count': len(public_routes),
        'protected_routes_count': len(protected_routes),
        'status_500_count': len(status_500_routes),
        'status_404_count': len(status_404_routes),
        'protected_routes': protected_routes,
        'public_routes': public_routes,
        'status_500_routes': status_500_routes
    }, out, indent=2)
