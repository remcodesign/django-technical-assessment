> Django Technical Assessment - LogBook Diagrams

# Diagrams

## Mermaid :: ER Diagram for polls + auth_user Models

```mermaid
erDiagram
    AUTH_USER {
      int id PK
      string username
    }

    QUESTION {
      int id PK
      string question_text
      datetime pub_date
    }

    CHOICE {
      int id PK
      int question_id FK
      string choice_text
      int votes
    }

    USERVOTE {
      int id PK
      int user_id FK
      int choice_id FK
      int question_id FK
      datetime created_at
    }

    AUDITLOG {
      int id PK
      int user_id FK
      string model
      string object_id
      string event
      text change_from
      text change_to
      datetime created_at
    }

    QUESTION ||--o{ CHOICE : "has"
    QUESTION ||--o{ USERVOTE : "has"
    CHOICE ||--o{ USERVOTE : "receives"
    AUTH_USER ||--o{ USERVOTE : "casts"
    AUTH_USER ||--o{ AUDITLOG : "writes"
```

## Mermaid :: Dataflow Diagrams for polls + auth_user Models

### 1) Vote flow sequence

```mermaid
sequenceDiagram
    participant User as USER
    participant AuthUser as AUTH_USER
    participant API as REST_API
    participant Question as QUESTION
    participant Choice as CHOICES
    participant UserVote as USERVOTE
    participant AuditLog as AUDITLOG

    User->>API: POST /api/polls/{question_id}/vote
    API->>AuthUser: validate login
    alt authenticated
        API->>Question: load question
        API->>Choice: select choice for question
        API->>UserVote: create vote row
        API->>Choice: increment votes
        API->>AuditLog: create vote audit
        API-->>User: return updated question payload
    else not authenticated
        API-->>User: 403 unauthorized
    end
```

### 2) Vote flowchart

```mermaid
flowchart LR
    A[User action: vote] --> B[AUTH_USER auth]
    B --> C[Load QUESTION]
    C --> D[Load CHOICE]
    D --> E[Create USERVOTE]
    E --> F[Increment CHOICE.votes]
    F --> G[Create AUDITLOG]
    G --> H[Return updated QUESTION detail]
```

### 3) Choice create/update/delete flowchart

```mermaid
flowchart LR
    A1[User action: choice create/update/delete] --> B1[AUTH_USER auth]
    B1 --> C1[Load QUESTION]
    C1 --> D1[Modify CHOICE]
    D1 --> E1[Create AUDITLOG]
    E1 --> F1[Return updated choice payload]
```

## Mermaid :: DRF dataflow diagram (QuestionView)

```mermaid
sequenceDiagram
    participant Client
    participant ViewSet as QuestionViewSet
    participant Manager as QuestionManager
    participant QuerySet as QuestionQuerySet
    participant DB
    participant Serializer

    Client->>ViewSet: HTTP GET /api/polls/
    ViewSet->>Manager: Question.objects.with_choice_count()
    Manager->>QuerySet: annotate(choice_count=Count("choice"))
    QuerySet->>DB: execute SQL (questions + choice_count)
    DB-->>QuerySet: Question rows
    ViewSet->>Serializer: QuestionListSerializer(list)
    Serializer-->>Client: JSON with id, question_text, pub_date, choice_count

    Client->>ViewSet: HTTP GET /api/polls/{pk}/
    ViewSet->>Manager: Question.objects.with_choice_count().with_choices()
    Manager->>QuerySet: prefetch_related("choice_set")
    QuerySet->>DB: execute SQL (questions + choice_count + choices)
    DB-->>QuerySet: Question + nested Choice rows
    ViewSet->>Serializer: QuestionDetailSerializer(detail)
    Serializer-->>Client: JSON with choices and user_choice_id

    Client->>ViewSet: POST /api/polls/{pk}/vote
    ViewSet->>Service: cast_vote(...)
    ViewSet->>Manager: _fresh_detail_payload(question)
    Manager->>QuerySet: with_choice_count().with_choices().get(pk=question.pk)
    QuerySet->>DB: execute fresh select
    ViewSet->>Serializer: QuestionDetailSerializer(fresh_question)
    Serializer-->>Client: fresh JSON payload
```

> Explanation

- QuestionViewSet.get_queryset() uses QuestionManager.with_choice_count() so every query returns choice_count via annotation.
- For retrieve/vote, it adds with_choices() so nested Choice rows are prefetched.
- get_serializer_class() selects QuestionListSerializer for list views and QuestionDetailSerializer for detail/vote views.
- _fresh_detail_payload() re-fetches the detail queryset with the same annotated manager methods to ensure the response includes the latest choice counts and nested choices.

## API URL map for DRF

Base path: `/api/polls/`

### Question endpoints

- `GET /api/polls/`
  - `QuestionViewSet.list`
- `POST /api/polls/`
  - `QuestionViewSet.create`
- `GET /api/polls/{pk}/`
  - `QuestionViewSet.retrieve`
- `PUT /api/polls/{pk}/`
  - `QuestionViewSet.update`
- `PATCH /api/polls/{pk}/`
  - `QuestionViewSet.partial_update`
- `DELETE /api/polls/{pk}/`
  - `QuestionViewSet.destroy`

### Question custom actions

- `POST /api/polls/{pk}/vote/`
  - `QuestionViewSet.vote`
- `POST /api/polls/{pk}/choices/`
  - `QuestionViewSet.add_choice`
- `PATCH /api/polls/{pk}/choices/{choice_id}/`
  - `QuestionViewSet.update_choice`
- `DELETE /api/polls/{pk}/choices/{choice_id}/`
  - `QuestionViewSet.delete_choice`

### Audit endpoints

- `GET /api/polls/audit/`
  - `AuditLogViewSet.list`
- `GET /api/polls/audit/users/`
  - `AuditLogViewSet.users`

---

## Mermaid diagram

```mermaid
flowchart TD
    A["/api/polls/"] -->|GET| B["QuestionViewSet.list"]
    A -->|POST| C["QuestionViewSet.create"]
```

--

```mermaid
flowchart TD
    D["/api/polls/{pk}/"] -->|GET| E["QuestionViewSet.retrieve"]
    D -->|PUT| F["QuestionViewSet.update"]
    D -->|PATCH| G["QuestionViewSet.partial_update"]
    D -->|DELETE| H["QuestionViewSet.destroy"] 
```

--

```mermaid
flowchart TD
    K["/api/polls/{pk}/choices/"] -->|POST| L["QuestionViewSet.add_choice"]
    M["/api/polls/{pk}/choices/{choice_id}/"] -->|PATCH| N["QuestionViewSet.update_choice"]
    M -->|DELETE| O["QuestionViewSet.delete_choice"]
```

--

```mermaid
flowchart TD
    I["/api/polls/{pk}/vote/"] -->|POST| J["QuestionViewSet.vote"]
```

--

```mermaid
flowchart TD
    P["/api/polls/audit/"] -->|GET| Q["AuditLogViewSet.list"]
    R["/api/polls/audit/users/"] -->|GET| S["AuditLogViewSet.users"]
```

That covers the complete DRF router surface defined by api_urls.py and the viewset actions in `QuestionViewSet` / `AuditLogViewSet`.
