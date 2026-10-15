package com.example.security

import java.security.MessageDigest
import java.util.Base64

/** Shared constants + crypto helpers for the reference apps. */
object Cfg {
    const val ISS = "https://auth.example"
    const val API_AUD = "api"
    const val BASE_URL = "https://app.example"
    const val ACCESS_TTL = 900L
    const val MAX_PIXELS = 50_000_000L
    const val ACCOUNT_LIMIT = 5
    const val IP_LIMIT = 10
    const val OTP_LIMIT = 5
    const val UPLOAD_LIMIT = 5
    val SECURE_HEADERS = mapOf(
        "Content-Security-Policy" to "default-src 'none'; frame-ancestors 'none'",
        "X-Content-Type-Options" to "nosniff")

    fun sha256Hex(s: String): String =
        MessageDigest.getInstance("SHA-256").digest(s.toByteArray()).joinToString("") { "%02x".format(it) }

    fun s256(verifier: String): String =
        Base64.getUrlEncoder().withoutPadding()
            .encodeToString(MessageDigest.getInstance("SHA-256").digest(verifier.toByteArray()))

    fun jsonField(json: String, key: String): String? =
        Regex("\"$key\"\\s*:\\s*\"?([^\",}]+)\"?").find(json)?.groupValues?.get(1)
}

/**
 * A SECURE reference implementation of AppUnderTest. Worked example of the
 * behaviour your real app must match; swap it out for a WebTestClient adapter.
 */
open class SecureReferenceApp : AppUnderTest {
    private val keys = Jwt.rsa()
    protected val users = linkedMapOf(
        "alice" to mutableMapOf<String, Any?>("id" to 1, "pw" to "alice-pw", "role" to "user",
            "enabled" to true, "mfa" to true, "verified" to true, "balance" to 0, "email" to "alice@x.com"),
        "bob" to mutableMapOf<String, Any?>("id" to 2, "pw" to "bob-pw", "role" to "user",
            "enabled" to true, "mfa" to true, "verified" to true, "balance" to 0, "email" to "bob@x.com"),
        "admin" to mutableMapOf<String, Any?>("id" to 3, "pw" to "admin-pw", "role" to "admin",
            "enabled" to true, "mfa" to true, "verified" to true, "balance" to 0, "email" to "admin@x.com"))
    private val resources = mapOf(1 to "alice-private", 2 to "bob-private")
    private val videos = mapOf(101 to 1, 102 to 2)
    private val media = setOf("intro.mp4")
    private val accountFails = HashMap<String, Int>()
    private val ipFails = HashMap<String, Int>()
    private val otpFails = HashMap<String, Int>()
    private val uploadCounts = HashMap<String, Int>()
    protected val revokedJti = HashSet<String>()
    private val userJtis = HashMap<String, MutableSet<String>>()
    private val refreshStore = HashMap<String, MutableMap<String, Any?>>()
    private val resetTokens = HashMap<String, MutableMap<String, Any?>>()
    private val oauthClients = mapOf(
        "public-app" to mapOf("redirect" to setOf("https://app.example/cb"), "public" to true),
        "other-app" to mapOf("redirect" to setOf("https://other.example/cb"), "public" to true))
    private val oauthCodes = HashMap<String, MutableMap<String, Any?>>()

    protected fun norm(u: String) = u.trim().lowercase()
    private fun hash(pw: String) = Cfg.sha256Hex("s4lt::$pw")
    private fun now() = System.currentTimeMillis() / 1000
    private fun rand(n: Int = 8) = (1..n).joinToString("") { "%02x".format((0..255).random()) }
    protected fun resp(status: Int, body: Map<String, Any?> = emptyMap()) =
        Resp(status, HashMap(Cfg.SECURE_HEADERS), body)

    protected open fun issueAccess(username: String, role: String, uid: Int, mfa: Boolean,
                                   aud: String = Cfg.API_AUD, ttl: Long = Cfg.ACCESS_TTL): String {
        val n = now(); val jti = rand()
        userJtis.getOrPut(username) { HashSet() }.add(jti)
        val payload = """{"sub":"$username","uid":$uid,"role":"$role","mfa":$mfa,""" +
            """"iss":"${Cfg.ISS}","aud":"$aud","jti":"$jti","iat":$n,"exp":${n + ttl}}"""
        return Jwt.signRs256("{\"alg\":\"RS256\",\"typ\":\"JWT\"}", payload, keys.private)
    }

    protected open fun verify(token: String): Map<String, Any?>? {
        val json = Jwt.verifyRs256(token, keys.public) ?: return null
        if (Cfg.jsonField(json, "aud") != Cfg.API_AUD) return null
        if (Cfg.jsonField(json, "iss") != Cfg.ISS) return null
        val exp = Cfg.jsonField(json, "exp")?.toLongOrNull() ?: return null
        if (exp < now()) return null
        val jti = Cfg.jsonField(json, "jti") ?: return null
        if (jti in revokedJti) return null
        val sub = Cfg.jsonField(json, "sub") ?: return null
        val u = users[sub] ?: return null
        if (u["enabled"] != true) return null
        return mapOf("sub" to sub, "uid" to u["id"], "role" to u["role"], "jti" to jti, "mfa" to u["mfa"])
    }

    override fun login(username: String, password: String, sourceIp: String, xff: String?,
                       otpOk: Boolean, prevSession: String?): Resp {
        val key = norm(username)
        if ((ipFails[sourceIp] ?: 0) >= Cfg.IP_LIMIT) return resp(429, mapOf("error" to "too many"))
        if ((accountFails[key] ?: 0) >= Cfg.ACCOUNT_LIMIT) return resp(429, mapOf("error" to "locked"))
        val u = users[key]
        val ok = u != null && u["enabled"] == true && hash(u["pw"] as String) == hash(password)
        if (ok && u!!["mfa"] == true && !otpOk) {
            otpFails[key] = (otpFails[key] ?: 0) + 1
            if (otpFails[key]!! >= Cfg.OTP_LIMIT) return resp(429, mapOf("error" to "otp locked"))
            return resp(401, mapOf("error" to "otp required"))
        }
        if (!ok) {
            accountFails[key] = (accountFails[key] ?: 0) + 1
            ipFails[sourceIp] = (ipFails[sourceIp] ?: 0) + 1
            return resp(401, mapOf("error" to "invalid credentials"))
        }
        accountFails[key] = 0
        val tok = issueAccess(key, u!!["role"] as String, u["id"] as Int, u["mfa"] as Boolean)
        val rtok = rand(16)
        refreshStore[rtok] = mutableMapOf("family" to rand(4), "used" to false, "user" to key)
        val r = resp(200, mapOf("access_token" to tok, "refresh_token" to rtok, "sid" to tok.take(16)))
        return r.copy(headers = r.headers + ("Set-Cookie" to
            "sid=${rand()}; HttpOnly; Secure; SameSite=Lax; Path=/"))
    }

    override fun logout(token: String): Resp {
        val c = verify(token) ?: return resp(401)
        revokedJti.add(c["jti"] as String); return resp(200, mapOf("status" to "out"))
    }

    override fun refresh(refreshToken: String): Resp {
        val rec = refreshStore[refreshToken] ?: return resp(401, mapOf("error" to "invalid"))
        if (rec["used"] == true) {
            val fam = rec["family"]
            refreshStore.values.filter { it["family"] == fam }.forEach { it["used"] = true }
            userJtis[rec["user"]]?.toList()?.forEach { revokedJti.add(it) }
            return resp(401, mapOf("error" to "reuse detected; family revoked"))
        }
        rec["used"] = true
        val user = rec["user"] as String; val u = users[user]!!
        val nt = rand(16)
        refreshStore[nt] = mutableMapOf("family" to rec["family"], "used" to false, "user" to user)
        return resp(200, mapOf("access_token" to issueAccess(user, u["role"] as String, u["id"] as Int, true),
            "refresh_token" to nt))
    }

    override fun register(username: String, password: String, requestedRole: String?,
                          extra: Map<String, Any?>): Resp {
        val key = norm(username)
        if (users.containsKey(key)) return resp(409, mapOf("error" to "exists"))
        users[key] = mutableMapOf("id" to (users.values.maxOf { it["id"] as Int } + 1), "pw" to password,
            "role" to "user", "enabled" to true, "mfa" to false, "verified" to false,
            "balance" to 0, "email" to "$key@x.com")  // privilege fields server-set, input ignored
        return resp(201, mapOf("role" to "user", "verified" to false, "balance" to 0))
    }

    override fun getResource(token: String, ownerId: Int): Resp {
        val c = verify(token) ?: return resp(401)
        if (c["role"] != "admin" && c["uid"] != ownerId) return resp(403, mapOf("error" to "forbidden"))
        return resp(200, mapOf("secret" to resources[ownerId]))
    }

    override fun getObject(token: String, kind: String, objId: Int): Resp {
        val c = verify(token) ?: return resp(401)
        val owner = if (kind == "video") videos[objId] else null
        owner ?: return resp(404)
        if (c["role"] != "admin" && c["uid"] != owner) return resp(403, mapOf("error" to "forbidden"))
        return resp(200, mapOf("video" to objId, "owner" to owner))
    }

    override fun adminUsers(token: String): Resp {
        val c = verify(token) ?: return resp(401)
        if (c["role"] != "admin") return resp(403, mapOf("error" to "admin only"))
        return resp(200, mapOf("pii" to "ALL_USERS_PII"))
    }

    override fun adminDeleteUser(token: String, target: String, method: String): Resp {
        val c = verify(token) ?: return resp(401)  // enforced for EVERY method
        if (c["role"] != "admin") return resp(403, mapOf("error" to "admin only"))
        return resp(200, mapOf("deleted" to target))
    }

    override fun changePassword(token: String, old: String, new: String, reauthed: Boolean,
                                csrfOk: Boolean, crossSite: Boolean): Resp {
        val c = verify(token) ?: return resp(401)
        if (crossSite || !csrfOk) return resp(403, mapOf("error" to "csrf"))
        if (!reauthed) return resp(401, mapOf("error" to "re-auth required"))
        users[c["sub"]]!!["pw"] = new
        userJtis[c["sub"]]?.toList()?.forEach { revokedJti.add(it) }
        return resp(200, mapOf("status" to "changed"))
    }

    override fun sensitiveAction(token: String, reauthed: Boolean, csrfOk: Boolean, crossSite: Boolean): Resp {
        val c = verify(token) ?: return resp(401)
        if (crossSite || !csrfOk) return resp(403, mapOf("error" to "csrf"))
        if (c["mfa"] != true) return resp(403, mapOf("error" to "mfa required"))
        if (!reauthed) return resp(401, mapOf("error" to "step-up required"))
        return resp(200, mapOf("status" to "done"))
    }

    override fun changeEmail(token: String, newEmail: String, reverified: Boolean): Resp {
        val c = verify(token) ?: return resp(401)
        if (!reverified) return resp(401, mapOf("error" to "verify new email first"))
        users[c["sub"]]!!["email"] = newEmail
        return resp(200, mapOf("status" to "pending"))
    }

    override fun getMedia(path: String): Resp {
        if (path.contains("/") || path.contains("\\") || path.contains("..") || path !in media)
            return resp(404, mapOf("error" to "not found"))
        val r = resp(200, mapOf("bytes" to 24))
        return r.copy(headers = r.headers + mapOf("Content-Type" to "video/mp4",
            "Content-Disposition" to "attachment"))
    }

    override fun upload(token: String, fetchUrl: String?, width: Int?, height: Int?, filename: String): Resp {
        val c = verify(token) ?: return resp(401)
        val u = c["sub"] as String
        uploadCounts[u] = (uploadCounts[u] ?: 0) + 1
        if (uploadCounts[u]!! > Cfg.UPLOAD_LIMIT) return resp(429, mapOf("error" to "rate limit"))
        if (fetchUrl != null && isInternal(fetchUrl)) return resp(400, mapOf("error" to "ssrf blocked"))
        if (width != null && height != null && width.toLong() * height > Cfg.MAX_PIXELS)
            return resp(400, mapOf("error" to "too large"))
        val r = resp(201, mapOf("stored" to filename))
        return r.copy(headers = r.headers + ("Content-Disposition" to "attachment"))
    }

    private fun isInternal(url: String): Boolean {
        val host = url.substringAfter("//").substringBefore("/").lowercase()
        return listOf("169.254.169.254", "localhost", "127.0.0.1", "0.0.0.0",
            "10.", "192.168.", "172.16.", "::1", "metadata").any { host.contains(it) }
    }

    override fun resetRequest(email: String, hostHeader: String): Resp {
        val user = users.entries.firstOrNull { it.value["email"] == email }?.key
        var link: String? = null
        if (user != null) {
            val tok = rand(24)
            resetTokens[tok] = mutableMapOf("user" to user, "exp" to now() + 900, "used" to false)
            link = "${Cfg.BASE_URL}/reset?token=$tok"  // from trusted config, never Host
        }
        return resp(200, mapOf("message" to "If the account exists, an email was sent.",
            "_link_for_test" to link))
    }

    override fun resetConfirm(token: String, newPw: String): Resp {
        val rec = resetTokens[token] ?: return resp(400, mapOf("error" to "invalid"))
        if (rec["used"] == true || (rec["exp"] as Long) < now()) return resp(400, mapOf("error" to "expired"))
        rec["used"] = true
        users[rec["user"]]!!["pw"] = newPw
        userJtis[rec["user"]]?.toList()?.forEach { revokedJti.add(it) }
        return resp(200, mapOf("status" to "reset"))
    }

    override fun oauthAuthorize(clientId: String, redirectUri: String, codeChallenge: String?, state: String?): Resp {
        val cl = oauthClients[clientId] ?: return resp(400, mapOf("error" to "unknown client"))
        @Suppress("UNCHECKED_CAST")
        if (redirectUri !in (cl["redirect"] as Set<String>)) return resp(400, mapOf("error" to "bad redirect_uri"))
        if (cl["public"] == true && codeChallenge == null) return resp(400, mapOf("error" to "pkce required"))
        if (state == null) return resp(400, mapOf("error" to "state required"))
        val code = rand()
        oauthCodes[code] = mutableMapOf("client" to clientId, "redirect" to redirectUri,
            "challenge" to codeChallenge, "used" to false)
        return resp(200, mapOf("code" to code, "state" to state))
    }

    override fun oauthToken(code: String, codeVerifier: String?, clientId: String, redirectUri: String): Resp {
        val rec = oauthCodes[code] ?: return resp(400, mapOf("error" to "invalid code"))
        if (rec["used"] == true) return resp(400, mapOf("error" to "used"))
        if (rec["client"] != clientId || rec["redirect"] != redirectUri)
            return resp(400, mapOf("error" to "client/redirect mismatch"))
        val ch = rec["challenge"] as String?
        if (ch != null && Cfg.s256(codeVerifier ?: "") != ch) return resp(400, mapOf("error" to "pkce failed"))
        rec["used"] = true
        return resp(200, mapOf("access_token" to issueAccess("alice", "user", 1, true)))
    }

    override fun buggyEndpoint(payload: String): Resp =
        payload.toIntOrNull()?.let { resp(200, mapOf("parsed" to it)) }
            ?: resp(400, mapOf("error" to "bad request"))  // no stack trace

    // --- test hooks ---
    override fun issueAccessToken(username: String, aud: String): String {
        val u = users[username]!!
        return issueAccess(username, u["role"] as String, u["id"] as Int, u["mfa"] as Boolean, aud)
    }
    override fun setEnabled(username: String, enabled: Boolean) { users[username]!!["enabled"] = enabled }
    override fun userField(username: String, field: String): Any? = users[username]?.get(field)
    override fun publicKey(): ByteArray = keys.public.encoded
}
