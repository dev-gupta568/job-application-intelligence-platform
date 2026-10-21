# Portfolio presentation

## Short project description

**Application Atlas** is a full-stack job-search management platform built with React, FastAPI, and PostgreSQL. It helps a job seeker organize applications, interview rounds, follow-up tasks, and recruiter communications. A database-backed dashboard presents application activity and conversion metrics; a transparent rule-based skill matcher compares job requirements with user-entered skills.

## Resume-ready entry

**Application Atlas — Job Application Intelligence Platform** | React, JavaScript, FastAPI, Python, SQLAlchemy, PostgreSQL, Alembic

- Built a responsive React workspace and authenticated REST API for managing user-owned job applications, interviews, follow-ups, and application activity.
- Implemented JWT authentication with Argon2 password hashing, request validation, and ownership-scoped database queries.
- Created PostgreSQL-backed dashboard analytics and a versioned rule-based skill matcher with explainable percentages, skill gaps, and saved opportunity comparisons.
- Added Alembic migrations and automated backend/frontend tests; verified dependency audits and production builds.

Only claim work you can explain and demonstrate. Do not describe the rule-based matcher as AI, and do not claim deployment until you have actually deployed and tested it.

## GitHub repository description

> A full-stack job application tracker with React, FastAPI, and PostgreSQL: applications, interview/follow-up tracking, analytics, and explainable rule-based skill matching.

## Suggested demo walkthrough

1. Create an account and explain that account records are private to the authenticated user.
2. Add a job application with a job description and required skills.
3. Open the dashboard and show that its totals and charts come from the API/database.
4. Schedule an interview, record feedback, and add/complete a follow-up reminder.
5. Open the application timeline and show automatic events alongside a recruiter note.
6. Analyze the job description using a sample skill list; explain the score denominator and show missing terms.
7. Select two saved skill comparisons and discuss how using the same skill list makes the comparison fair.
8. Show the API documentation and tests. Explicitly state that the matcher is rule-based and that the application has not been deployed unless you have completed the deployment guide.

## Interview questions to practice

### Architecture and API

1. **How does a React page communicate with FastAPI?**  
   UI pages use functions in `src/services/`. The shared fetch client sets JSON headers, sends the bearer token from in-memory auth state, and turns non-success responses into a typed API error. The backend validates payloads with Pydantic schemas before using SQLAlchemy.

2. **How do you stop one user from reading another user's applications?**  
   The token is validated to resolve the active user. Every private query is scoped by that user's ID or joins through an application owned by that user. A missing or foreign-owned resource returns `404`, avoiding disclosure that another account's resource exists.

3. **Why does a refresh sign the user out? What are the trade-offs?**  
   The access token is stored in React memory rather than browser persistent storage. This avoids leaving a bearer token in local storage, but refresh requires another sign-in. A production session design could use short-lived access tokens with carefully protected, rotated refresh sessions, often using secure HttpOnly cookies and CSRF protections.

### Data and analytics

4. **How is interview conversion calculated?**  
   Count distinct submitted applications with at least one non-cancelled interview, divide by submitted applications, multiply by 100, and round to two decimal places. Multiple rounds for one application count once.

5. **How do you change the database schema safely?**  
   Edit the SQLAlchemy model, generate/review an Alembic migration, apply it to a test database, verify `alembic check`, then run the migration as a controlled deployment release step before serving code that depends on the new field.

6. **Why use PostgreSQL instead of keeping records in the browser?**  
   PostgreSQL provides durable shared data, relational constraints, indexing, and ownership-aware queries. It also lets dashboard metrics be calculated from saved records rather than fabricated client state.

### Security and quality

7. **How are passwords protected?**  
   The API hashes passwords with Argon2 before storage. It never returns the hash, normalizes email addresses, and uses a dummy Argon2 verification for unknown emails to reduce login timing differences.

8. **What does the skill-match percentage mean—and not mean?**  
   It is the percentage of recognized, distinct requirement terms also present in the user's skill list. It is a deterministic keyword overlap calculation, not semantic understanding, an ATS score, an AI result, or a probability of being hired.

9. **What checks run before a release?**  
   Frontend tests, lint, production build, and npm audit; backend pytest, pip check, Alembic schema check, and—when the audit service is reachable—a Python dependency audit. Then deploy and manually test account, CRUD, analytics, interview, and skill-matching workflows.

## Honest project status

- Implemented locally: authentication, application CRUD, dashboard analytics, interview/follow-up management, activity timeline, rule-based skill matching, migrations, and automated tests.
- Hosting setup: follow [DEPLOYMENT.md](./DEPLOYMENT.md); deployment is not claimed until completed and smoke-tested on the chosen provider.
- Not implemented: live job-board provider, AI integration, resume-file storage, password reset, email verification, and production-grade token revocation/rate limiting.
