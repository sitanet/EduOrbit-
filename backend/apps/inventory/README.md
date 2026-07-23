# Enterprise Inventory, Procurement & Asset Management (EIPAM) Documentation

This document describes the suppliers, procurement requests, purchase orders, warehouses, stock batch items, stock movements ledger, capital assets, and depreciation logs of the **inventory** app.

---

## 1. Procurement Engine
- **Supplier**: Contact details, tax info, rating scores.
- **PurchaseRequest**: Demands workflow (draft, submitted, approved).
- **PurchaseOrder**: Outbound suppliers orders.

---

## 2. Warehouse & Stocks
- **Warehouse**: Campus storage locations.
- **InventoryItem**: Item parameters, sku, reorder limits.
- **InventoryBatch**: FIFO/FEFO tracking.
- **StockMovement**: Logs adjustments, transfers, and disposals.

---

## 3. Assets & Depreciation
- **Asset**: Acquisition costs, residuals, useful lives.
- **AssetDepreciation**: Depreciation runs logs.
- **AssetMaintenance**: Service records.

---

## 4. REST APIs
Endpoints are mapped under `/inventory/api/v1/`:
- `GET/POST /inventory/items/`: Item stock registers.
- `GET/POST /inventory/warehouses/`: Warehouses list.
- `GET/POST /inventory/orders/`: Issued purchase orders.
