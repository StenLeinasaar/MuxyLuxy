# Security

This repo is **early-stage local tooling**. The notes below are scoped to what we run in Compose today, not a full production threat model.

## Threat model

_TBD_ for production deployment (ingress, identity, data classification).

## Local SSH targets (`target1` / `target2`)

- **Purpose:** lab containers on your machine only. They exist so we can iterate on SSH and Ansible-style flows.
- **Credentials:** the `ansible` user has a **known weak password** set in the image build (`ansible` / `ansible` unless you change the Dockerfile). **Do not expose** these ports to untrusted networks or reuse this image as-is in production.
- **SSH config:** `targets/sshd_config` allows password auth for convenience in dev. Production targets should prefer **keys**, disable password auth where policy requires it, and use proper account provisioning.

## Secrets and credentials

- Use **`.env`** (gitignored) for overrides; **`.env.example`** documents variables without real secrets.
- API and DB defaults in Compose are for **local development only**.

## Hardening checklist

_TBD_ when we add hosted environments (TLS, authn/z for the API, secret storage, network policies).
