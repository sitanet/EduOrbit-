# Enterprise AI Platform & Automation Engine (EAPAE) Documentation

This document describes the AI providers, model contexts limits, chat conversation sessions, prompt versions, embedding vectors, RAG documents chunks, and event automation rules of the **ai** app.

---

## 1. Providers & Chat Sessions
- **AIProvider & AIModel**: Pluggable models mapping context limits.
- **AIConversation & AIMessage**: Message bubble history logs.

---

## 2. Prompts & Knowledge Base
- **PromptTemplate & PromptVersion**: Prompts system instructions revisions histories.
- **KnowledgeDocument & KnowledgeChunk**: Split text content for semantic RAG queries.

---

## 3. Automation Rules
- **AutomationRule**: Configures custom triggers mapping target actions.

---

## 4. REST APIs
Endpoints are mapped under `/ai/api/v1/`:
- `GET/POST /ai/conversations/`: Active chat conversations.
- `GET/POST /ai/messages/`: Appends message queries.
- `GET/POST /ai/prompts/`: Template settings.
