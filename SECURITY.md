# Security Policy

## Scope and Local Prototype Boundary
ActionRail Finance MVP is a **local prototype** designed strictly for demonstration and architectural validation.
It is an educational tool emphasizing safe transaction design for AI agents.

- **No real money movement**: This application does not connect to any financial clearinghouse, payment rail, or bank.
- **Do not connect to real accounts**: Never configure this prototype to point to a production ERP, accounting software, or live banking API.
- **API Keys are local demo credentials**: The included API key generation and authentication mechanisms use local SQLite validation. They are not intended to replace a robust production API gateway.

## Environment Variables and Secrets
- **Do not put real secrets in `.env`**: Never store genuine credentials in the local environment files. Use mock data (e.g., `example.local`) exclusively.

## Data Governance and Evidence Packs
- **Evidence Packs are local exports**: Downloadable zip files (evidence packs) represent local compliance snapshots. They are not immutable compliance storage.
- **Do not upload PII or real financial data**: Uploaded invoices and contract documents reside locally and are intentionally Git-ignored. Do not expose actual sensitive corporate or personal data to this system.

## Production Requirements
If this architecture were to be scaled to a production environment, the following enterprise-grade capabilities are mandatory but currently omitted by design:
1. **Real Identity Provider (IdP)**: Integration with OAuth, SAML, or OIDC.
2. **WORM Audit Storage**: Immutable, Write-Once-Read-Many storage for the audit ledger.
3. **Encryption at Rest**: Secure key management for all stored records.
4. **Key Rotation**: Automated lifecycle management for agent API keys.
5. **Monitoring and Alerting**: Real-time integration with SIEM tools.
6. **Backup and Retention**: Compliant data retention and disaster recovery protocols.
7. **Compliance Review**: Formal regulatory, SOC2, and InfoSec reviews prior to handling real money.
