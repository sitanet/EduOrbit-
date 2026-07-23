# Enterprise Communication & Engagement Hub (CEH) Documentation

This document describes the structure, opt-in rules settings, template formats, and delivery logging of the **communication** app.

---

## 1. Omnichannel Delivery Architecture
The CEH acts as a single centralized message dispatcher. Rather than sending emails or SMS directly, other business modules emit standard domain events which are consumed to render templates:
```
[ DomainEvent ] ──> Handled by central listener
       │
       ▼
[ NotificationTemplate ] ──> Dynamic string compile
       │
       ▼
[ Notification ] ──> Queue record matching recipient preferences
       │
       ▼
[ CommunicationLog ] ──> Immutable delivery log
```

---

## 2. Parent-Teacher Messaging Chat
- **Conversation**: Session threads between participants (e.g. Parent ↔ Teacher).
- **Message**: Single message lines containing text content.

---

## 3. Web & REST APIs
Endpoints are mapped under `/communication/api/v1/`:
- `GET/POST /communication/announcements/`: List or publish announcements.
- `GET/POST /communication/notifications/`: Inspect universal message queues.
- `GET/POST /communication/messages/`: Post message lines in threads.
