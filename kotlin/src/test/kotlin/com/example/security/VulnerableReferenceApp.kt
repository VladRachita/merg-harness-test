package com.example.security

/**
 * NEGATIVE CONTROL ONLY — a deliberately broken build so the harness can prove it
 * detects real breaks in every category. NEVER ship anything like this.
 */
class VulnerableReferenceApp : SecureReferenceApp() {

    // VULN: no signature verification; trusts role/sub from the raw claim.
    override fun verify(token: String): Map<String, Any?>? {
        val json = try { Jwt.payloadUnverified(token) } catch (e: Exception) { return null }
        return mapOf("sub" to (Cfg.jsonField(json, "sub") ?: "?"),
            "uid" to (Cfg.jsonField(json, "uid")?.toIntOrNull() ?: -1),
            "role" to (Cfg.jsonField(json, "role") ?: "user"),
            "jti" to (Cfg.jsonField(json, "jti") ?: ""),
            "mfa" to (Cfg.jsonField(json, "mfa") == "true"))
    }

    // VULN: no rate limiting; user-enumeration; session fixation.
    override fun login(username: String, password: String, sourceIp: String, xff: String?,
                       otpOk: Boolean, prevSession: String?): Resp {
        val key = norm(username)
        val u = users[key] ?: return resp(404, mapOf("error" to "unknown user"))
        if (Cfg.sha256Hex("s4lt::" + (u["pw"] as String)) != Cfg.sha256Hex("s4lt::$password"))
            return resp(401, mapOf("error" to "wrong password"))
        val tok = issueAccess(key, u["role"] as String, u["id"] as Int, u["mfa"] as Boolean)
        return Resp(200, mapOf("Set-Cookie" to "sid=static-123"),
            mapOf("access_token" to tok, "sid" to (prevSession ?: tok.take(16))))
    }

    override fun logout(token: String): Resp = resp(200, mapOf("status" to "out"))  // VULN: noop

    override fun refresh(refreshToken: String): Resp =  // VULN: no rotation/reuse detect
        resp(200, mapOf("access_token" to issueAccessToken("alice"), "refresh_token" to refreshToken))

    // VULN: honours attacker-supplied privilege fields (mass assignment).
    override fun register(username: String, password: String, requestedRole: String?,
                          extra: Map<String, Any?>): Resp {
        val key = norm(username)
        if (users.containsKey(key)) return resp(409, mapOf("error" to "exists"))
        users[key] = mutableMapOf("id" to 99, "pw" to password,
            "role" to (requestedRole ?: extra["role"] ?: "user"), "enabled" to true, "mfa" to false,
            "verified" to (extra["isVerified"] ?: false), "balance" to (extra["balance"] ?: 0),
            "email" to "$key@x.com")
        return resp(201, mapOf("role" to users[key]!!["role"], "verified" to users[key]!!["verified"],
            "balance" to users[key]!!["balance"]))
    }

    override fun getResource(token: String, ownerId: Int): Resp =
        resp(200, mapOf("secret" to if (ownerId == 2) "bob-private" else "alice-private"))  // VULN: IDOR
    override fun getObject(token: String, kind: String, objId: Int): Resp =
        resp(200, mapOf("video" to objId))  // VULN: BOLA
    override fun adminUsers(token: String): Resp = resp(200, mapOf("pii" to "ALL_USERS_PII"))  // VULN
    override fun adminDeleteUser(token: String, target: String, method: String): Resp {
        if (method != "DELETE") return resp(200, mapOf("deleted" to target))  // VULN: method confusion
        val c = verify(token)
        return if (c != null && c["role"] == "admin") resp(200, mapOf("deleted" to target))
        else resp(403, mapOf("error" to "admin only"))
    }
    override fun changePassword(token: String, old: String, new: String, reauthed: Boolean,
                                csrfOk: Boolean, crossSite: Boolean): Resp = resp(200)  // VULN
    override fun sensitiveAction(token: String, reauthed: Boolean, csrfOk: Boolean, crossSite: Boolean): Resp =
        resp(200)  // VULN: no csrf/step-up
    override fun changeEmail(token: String, newEmail: String, reverified: Boolean): Resp = resp(200)  // VULN
    override fun getMedia(path: String): Resp = resp(200, mapOf("served" to path))  // VULN: traversal
    override fun upload(token: String, fetchUrl: String?, width: Int?, height: Int?, filename: String): Resp =
        resp(201, mapOf("stored" to filename, "fetched" to fetchUrl))  // VULN: SSRF, no limits

    override fun resetRequest(email: String, hostHeader: String): Resp {
        val user = users.entries.firstOrNull { it.value["email"] == email }?.key
            ?: return resp(404, mapOf("error" to "no such user", "message" to "no such user"))  // VULN
        val tok = "static-reset-tok"
        return resp(200, mapOf("message" to "sent",
            "_link_for_test" to "https://$hostHeader/reset?token=$tok"))  // VULN: host header
    }
    override fun resetConfirm(token: String, newPw: String): Resp = resp(200, mapOf("status" to "reset"))  // VULN
    override fun oauthAuthorize(clientId: String, redirectUri: String, codeChallenge: String?, state: String?): Resp =
        resp(200, mapOf("code" to "static-code", "state" to state))  // VULN: no checks
    override fun oauthToken(code: String, codeVerifier: String?, clientId: String, redirectUri: String): Resp =
        resp(200, mapOf("access_token" to issueAccessToken("alice")))  // VULN
    override fun buggyEndpoint(payload: String): Resp =
        payload.toIntOrNull()?.let { resp(200, mapOf("parsed" to it)) }
            ?: resp(500, mapOf("trace" to "java.lang.NumberFormatException at Parser.parse($payload)"))
}
