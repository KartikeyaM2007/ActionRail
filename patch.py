import sys

content = open('app/store.py', encoding='utf-8').read()
old = """    )
    conn.commit()
    seed_demo_users(conn)"""

new = """    )
    conn.commit()

    # Seed demo API client
    demo_client = conn.execute("SELECT id FROM api_clients WHERE id='client_demo'").fetchone()
    if not demo_client:
        import hashlib
        # Use a deterministic hash for the demo client so tests can predict it or we can just ignore secret.
        # "demo_secret_key"
        key_hash = hashlib.pbkdf2_hmac("sha256", b"demo_secret_key", b"actionrail", 100000).hex()
        conn.execute(
            \"\"\"
            INSERT INTO api_clients (
                id, name, client_key_hash, client_key_prefix, role,
                allowed_scopes_json, rate_limit_per_minute, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\",
            (
                "client_demo", "Local Demo Agent", key_hash, "sk_demo", "agent",
                dumps(["preflight:create", "transactions:read", "receipts:read"]),
                60, utc_now().isoformat(), utc_now().isoformat()
            )
        )
        conn.commit()

    seed_demo_users(conn)"""

if old in content:
    open('app/store.py', 'w', encoding='utf-8').write(content.replace(old, new, 1))
    print('Updated store.py successfully')
else:
    print('Old content not found in store.py')
