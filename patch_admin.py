import sys

content = open('app/admin_routes.py', encoding='utf-8').read()

imports = """
    update_contract,
    update_policy_settings,
    update_vendor,
    list_api_clients,
    create_api_client,
    update_api_client_status,
)
from app.api_security import generate_api_key
"""
content = content.replace("""    update_contract,
    update_policy_settings,
    update_vendor,
)""", imports)

api_clients_routes = """
    @app.get("/dashboard/admin/api-clients", response_class=HTMLResponse)
    def admin_api_clients_list(request: Request, error: str | None = None, success: str | None = None, new_key: str | None = None):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        return templates.TemplateResponse(
            request,
            "admin_api_clients.html",
            dash_ctx(request, api_clients=list_api_clients(get_conn()), error=error, success=success, new_key=new_key),
        )

    @app.post("/dashboard/admin/api-clients/create")
    def admin_api_clients_create(
        request: Request,
        name: str = Form(...),
        role: str = Form(default="agent"),
        scopes: str = Form(...),
        rate_limit: int = Form(default=60),
        csrf_token: str = Form(default=""),
    ):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        csrf_resp = dash_csrf(request, user, csrf_token, "api_client", None)
        if csrf_resp:
            return csrf_resp
        client_id = f"client_{uuid.uuid4().hex[:10]}"
        raw_key, hashed_key = generate_api_key()
        prefix = raw_key.split("_")[0] + "_" + raw_key.split("_")[1]
        
        scope_list = [s.strip() for s in scopes.split(",") if s.strip()]
        
        create_api_client(
            get_conn(),
            client_id=client_id,
            name=name.strip(),
            client_key_hash=hashed_key,
            client_key_prefix=prefix,
            role=role.strip(),
            allowed_scopes=scope_list,
            rate_limit_per_minute=rate_limit
        )
        control.write_audit_event(
            get_conn(), request, action="api_client_created", target_type="api_client",
            target_id=client_id, event={"name": name.strip(), "role": role.strip(), "scopes": scope_list},
            actor=user
        )
        url = f"/dashboard/admin/api-clients?success=API+Client+created&new_key={raw_key}"
        return RedirectResponse(url=url, status_code=303)

    @app.post("/dashboard/admin/api-clients/{client_id}/disable")
    def admin_api_clients_disable(
        request: Request,
        client_id: str,
        csrf_token: str = Form(default=""),
    ):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        csrf_resp = dash_csrf(request, user, csrf_token, "api_client", client_id)
        if csrf_resp:
            return csrf_resp
        
        update_api_client_status(get_conn(), client_id, is_active=False)
        control.write_audit_event(
            get_conn(), request, action="api_client_disabled", target_type="api_client",
            target_id=client_id, event={}, actor=user
        )
        return RedirectResponse(url="/dashboard/admin/api-clients?success=Client+disabled", status_code=303)

    @app.post("/dashboard/admin/api-clients/{client_id}/enable")
    def admin_api_clients_enable(
        request: Request,
        client_id: str,
        csrf_token: str = Form(default=""),
    ):
        user, blocked = _admin_guard(request)
        if blocked:
            return blocked
        csrf_resp = dash_csrf(request, user, csrf_token, "api_client", client_id)
        if csrf_resp:
            return csrf_resp
            
        update_api_client_status(get_conn(), client_id, is_active=True)
        control.write_audit_event(
            get_conn(), request, action="api_client_enabled", target_type="api_client",
            target_id=client_id, event={}, actor=user
        )
        return RedirectResponse(url="/dashboard/admin/api-clients?success=Client+enabled", status_code=303)
"""

if "admin_api_clients_list" not in content:
    content += api_clients_routes

open('app/admin_routes.py', 'w', encoding='utf-8').write(content)
print('Updated admin_routes.py successfully')
