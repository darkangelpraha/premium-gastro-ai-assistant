# Missive Depoto Email Thread Findings (Sanitized)

## Purpose

Capture the actionable facts about the Depoto thread that exists locally on this Mac, without copying any credentials or private content into git.

## Where It Was Found (Local Only)

Source application: Missive

Local storage (IndexedDB LevelDB log):
- `/Users/premiumgastro/Library/Application Support/Missive/Partitions/missive/IndexedDB/https_mail.missiveapp.com_0.indexeddb.leveldb/005451.log`

Important: this file can contain cleartext credentials and private message content. Do not share it. Do not commit it.

## Verified Thread Metadata

Conversation ID:
- `eae6c11b-e8d2-4773-aeff-a977e32fce07`

Subject string observed in cache:
- `Re: Premium Gastro - Aktivace doplnku Depoto a dalsi postup`

Participants observed in cache:
- `tomas.libich@depoto.cz`
- `vlaciha@olicon.cz`
- `vavra@v2logistics.cz`
- `info@premium-gastro.com`
- `ps@premium-gastro.com`

## Key Operational Facts Mentioned

- Depoto carrier mapping matters (TopTrans and others).
- BlueJet does not provide Depoto integration out of the box for this use case, custom integration is required.
- Depoto API client reference was shared (public GitHub).
- A demo tenant link and demo credentials were present in the cache. These were treated as sensitive and were not copied into this repo.

## Immediate Actions

- Use `ops/DEPOTO_SUPPORT_EMAIL_DRAFT.md` to confirm exact production base URL, test environment, checkout IDs, depot IDs, carrier IDs, and webhook expectations with Depoto.
- Implement lean integration with safe gates (`isPaid=false` planning mode, then flip to paid only when ready).
- Prioritize TopTrans automation via API (not browser automation) for immediate time savings.
