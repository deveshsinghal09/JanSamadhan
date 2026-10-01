# Neon database and review demonstration

This computer is connected to the JanSamadhan Neon project in AWS Singapore, using PostgreSQL 18. Dashboard: https://console.neon.tech/app/projects/floral-hat-42967010

The connection string is stored only in the project's ignored `.env` file as `DATABASE_URL`. The review ZIP includes `.env.example`, not your password. On another computer, configure your own connection string before starting. Neon mode requires Internet access. Without DATABASE_URL, the app uses local persistent JSON storage.

## Start and demonstrate

```powershell
cd E:\OneDrive\Documents\ChatGPT\JANSAMADHAN
.\START_DEMO.cmd
```

Open http://127.0.0.1:3001 and sign in as Citizen with the supplied review account. Describe an issue, select its locality, optionally attach a photo, and click Analyze & preview routing. Review the proposed department and click Submit report. The saved report opens immediately and appears in tracking. Sign in as the appropriate officer to update its progress. After restarting the server, sign in again: reports persist, but login sessions are kept in memory.

The 24 synthetic complaint seeds were removed, and automatic complaint seeding is disabled. Your existing submitted report was preserved. Demo login accounts remain available. New registrations and submitted reports are stored in the database.

## What the database stores

Within the `jansamadhan` schema, `users` stores accounts and password hashes; `complaints` stores ownership, department, status and timestamps, plus the full report and its history in a JSONB column; `photos` stores the uploaded image bytes linked to its complaint. Parameterized queries and transactions keep report and photo saves consistent. A failed database save is reported as an error rather than displayed as successful.

In the Neon SQL editor, inspect submitted complaints with:

```sql
SELECT id, data->>'description' AS description,
       department, status, created_at
FROM jansamadhan.complaints
ORDER BY created_at DESC;
```

The local project can run `node scripts/check-neon.mjs` to check counts and API health without printing credentials. Local backups created before seed removal are in `data/runtime/backups` and are excluded from the shared ZIP.

This is an academic application designed for one running API instance. It loads database state into memory and saves changes transactionally. Multiple independently running API instances would need additional synchronization. Department assignments are internal review queues; submitting a report does not send it to government.
