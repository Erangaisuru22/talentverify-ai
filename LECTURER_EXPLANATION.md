# TalentVerifyAI Database Integration — Lecturer Explanation

## System overview

MongoDB is a NoSQL document database. A collection contains BSON documents, which resemble
JSON objects. It suits TalentVerifyAI because profiles, job skills, CV results, and candidate
snapshots contain flexible and nested data.

The browser does not connect to MongoDB. Doing that would reveal credentials and allow users to
bypass authorization. FastAPI is the trusted backend boundary. PyMongo is MongoDB's official
Python driver; it performs the role that Mongoose would perform in a Node.js project.

The current implementation also includes a multi-source technical skills matrix. It combines
saved technical skills with CV, experience, project, GitHub, portfolio, and LinkedIn source data.
GitHub provides repository-level verification. Portfolio and LinkedIn links are validated and
shown as available evidence links; LinkedIn URL verification does not scan post content.

```text
User -> React -> HTTP request -> FastAPI route -> PyMongo -> MongoDB
User <- React <- JSON response <- FastAPI <- PyMongo <- MongoDB
```

A collection is comparable to a table, a document to a row, and a field to a column. Unlike a
strict relational table, documents can contain nested objects and arrays. A schema is the agreed
structure and validation rules for data. This project validates API input in FastAPI/Pydantic
and controls permitted database fields in each route. MongoDB `_id` exists internally, while
the application uses UUID string `id` values as stable public identifiers.

## Real example: candidate applies for a job

1. The candidate logs in and receives a random opaque session token.
2. React sends the application and token to `POST /api/applications`.
3. FastAPI resolves the session and identifies the candidate.
4. It checks for an existing application with the same candidate and job.
5. PyMongo inserts the application with status, timestamp, score, and analysis snapshot.
6. FastAPI removes internal fields and returns JSON.
7. React adds the returned application to the dashboard.
8. When the recruiter loads data, FastAPI returns applications only for jobs that recruiter owns.

CRUD means Create, Read, Update, and Delete. Jobs support all four operations through POST, GET,
PATCH, and DELETE. Authentication proves identity; authorization checks whether that identity is
allowed to perform a specific action.

## Security controls

- MongoDB and Gemini secrets exist only in `backend/.env`.
- Passwords are salted and hashed using PBKDF2-HMAC-SHA256, never stored as plain text.
- Session tokens are random and only their opaque value is stored in the browser.
- FastAPI validates roles and resource ownership.
- Unique indexes prevent duplicate emails and duplicate applications.
- CORS permits configured frontend origins instead of every website.
- API responses omit MongoDB `_id` and `passwordHash`.

## Likely viva questions and answers

1. **What is MongoDB?** A NoSQL database that stores BSON documents in collections.
2. **Why choose MongoDB here?** It naturally stores flexible profiles and nested AI-analysis data.
3. **Why not MySQL?** MySQL could work, but nested evolving analysis data requires more relational tables or JSON columns; MongoDB is simpler for this design.
4. **Why can React not connect directly?** Browser code is public and would expose database credentials and bypass backend authorization.
5. **What is FastAPI's role?** It validates HTTP requests, authenticates users, enforces permissions, runs business rules, and accesses MongoDB.
6. **What is PyMongo?** MongoDB's official Python driver used by FastAPI to query and update the database.
7. **What is Mongoose?** A Node.js MongoDB ODM; this Python project correctly uses PyMongo instead.
8. **What is a collection?** A named group of related documents, such as `jobs`.
9. **What is a document?** One BSON record, such as one candidate or one job.
10. **What is a schema?** The expected fields, types, constraints, and relationships of stored data.
11. **What is ObjectId?** MongoDB's default unique `_id` type; this API hides it and exposes UUID string IDs.
12. **How are credentials secured?** They are stored in ignored backend environment files and never sent to Vite or React.
13. **How are passwords secured?** A random salt and slow PBKDF2 hash are stored, not the password.
14. **What happens when MongoDB is unavailable?** Startup/health checks fail clearly and database routes return HTTP 503 rather than fake data.
15. **How does the frontend communicate with MongoDB?** Indirectly through HTTP requests to FastAPI.
16. **How are duplicates prevented?** Unique indexes protect email and candidate/job application pairs.
17. **How is authorization implemented?** Routes derive the current user from a session and filter updates by user or recruiter ownership.
18. **What is CORS?** A browser security policy controlling which frontend origins may call the backend.
19. **Why store an application snapshot?** It preserves the evidence and score reviewed when the candidate applied, even if the profile later changes.
20. **How can database health be checked?** Call `GET /api/health`; it pings MongoDB and returns the connection state.
21. **What does the skills matrix do?** It shows the evidence sources attached to each saved technical skill and lets recruiters inspect GitHub evidence.
22. **Is LinkedIn verified like GitHub?** The current feature validates and timestamps a LinkedIn profile/post URL. It does not independently verify identity or post content without official LinkedIn API access.
