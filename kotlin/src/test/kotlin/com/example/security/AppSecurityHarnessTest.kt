package com.example.security

import org.junit.jupiter.api.*
import org.junit.jupiter.api.Assertions.*

/**
 * APPLICATION-SECURITY HARNESS — attacks that try to gain access to / control
 * data, across 11 categories. Every attack must be blocked by the system under
 * test; a negative control proves the suite detects real breaks.
 *
 * Wire YOUR app in by replacing newApp() with an adapter over your Spring
 * Security filter chain (WebTestClient). See README for an adapter sketch.
 */
class AppSecurityHarnessTest {

    private fun newApp(): AppUnderTest = SecureReferenceApp()

    private data class Attack(val id: String, val category: String, val desc: String,
                              val safe: (AppUnderTest) -> Boolean)

    private fun userToken(a: AppUnderTest): String =
        a.login("alice", "alice-pw").body["access_token"] as? String ?: ""

    private fun adminClaims(sub: String = "alice"): String {
        val now = System.currentTimeMillis() / 1000
        return """{"sub":"$sub","uid":1,"role":"admin","mfa":true,"iss":"${Cfg.ISS}",""" +
               """"aud":"${Cfg.API_AUD}","jti":"x","iat":$now,"exp":${now + 900}}"""
    }

    private fun catalogue(pub: ByteArray): List<Attack> {
        val a = ArrayList<Attack>()
        fun add(id: String, cat: String, d: String, f: (AppUnderTest) -> Boolean) = a.add(Attack(id, cat, d, f))

        // 1. brute force
        add("BF1", "brute-force", "lockout holds even with correct password") { s ->
            repeat(Cfg.ACCOUNT_LIMIT) { s.login("alice", "wrong") }
            s.login("alice", "alice-pw").status == 429 }
        add("BF2", "brute-force", "password spraying throttled per source IP") { s ->
            (0 until Cfg.IP_LIMIT + 3).map { s.login("user$it", "Password1", sourceIp = "9.9.9.9").status }.contains(429) }
        add("BF3", "brute-force", "lockout counter shared across username casing/space") { s ->
            listOf("alice", "Alice", " alice ", "ALICE", "alice ").forEach { s.login(it, "wrong") }
            s.login("alice", "alice-pw").status == 429 }
        add("BF4", "brute-force", "spoofed X-Forwarded-For can't bypass IP limit") { s ->
            (0 until Cfg.IP_LIMIT + 3).forEach { s.login("bob", "wrong", sourceIp = "7.7.7.7", xff = "1.2.3.$it") }
            s.login("bob", "wrong", sourceIp = "7.7.7.7").status == 429 }
        add("BF5", "brute-force", "OTP / second-factor attempts rate-limited") { s ->
            repeat(Cfg.OTP_LIMIT) { s.login("alice", "alice-pw", otpOk = false) }
            s.login("alice", "alice-pw", otpOk = false).status == 429 }
        add("BF6", "brute-force", "no user-enumeration signal on login") { s ->
            val r1 = s.login("nosuchuser", "x"); val r2 = s.login("alice", "wrongpw")
            r1.status == r2.status && r1.body == r2.body }

        // 2. injection
        add("INJ1", "injection", "SQLi in username does not authenticate") { !it.login("' OR '1'='1' --", "x").ok }
        add("INJ5", "injection", "path traversal in media path rejected") { !it.getMedia("../../etc/passwd").ok }
        add("INJ6", "injection", "SSRF to cloud-metadata IP blocked") { s ->
            !s.upload(userToken(s), fetchUrl = "http://169.254.169.254/latest/meta-data/").ok }

        // 3. output / headers
        add("OUT1", "output", "X-Content-Type-Options: nosniff present") {
            it.buggyEndpoint("1").headers["X-Content-Type-Options"] == "nosniff" }
        add("OUT3", "output", "Content-Security-Policy present") {
            it.buggyEndpoint("1").headers.containsKey("Content-Security-Policy") }
        add("OUT5", "output", "uploads served as attachments, never inline") { s ->
            s.upload(userToken(s), filename = "evil.svg").headers["Content-Disposition"] == "attachment" }

        // 4. jwt / session
        add("C1", "jwt", "alg:none admin token rejected") { !it.adminUsers(Jwt.forgeNone(adminClaims())).ok }
        add("C2", "jwt", "RS256->HS256 confusion rejected") { !it.adminUsers(Jwt.forgeHs256(adminClaims(), pub)).ok }
        add("C3", "jwt", "attacker-secret-signed token rejected") {
            !it.adminUsers(Jwt.forgeHs256(adminClaims(), "attacker".toByteArray())).ok }
        add("C5", "jwt", "expired token rejected") { s ->
            val now = System.currentTimeMillis() / 1000
            val c = """{"sub":"alice","uid":1,"role":"admin","iss":"${Cfg.ISS}","aud":"${Cfg.API_AUD}",""" +
                    """"jti":"x","iat":${now - 900},"exp":${now - 10}}"""
            !s.getResource(Jwt.forgeNone(c), 1).ok }
        add("SES1", "session", "session id rotates on login (no fixation)") { s ->
            s.login("alice", "alice-pw", prevSession = "attacker-id").body["sid"] != "attacker-id" }
        add("SES2", "session", "token revoked after logout") { s ->
            val t = userToken(s); s.logout(t); !s.getResource(t, 1).ok }
        add("SES3", "session", "tokens revoked after password change") { s ->
            val t = userToken(s); s.changePassword(t, "alice-pw", "new", reauthed = true); !s.getResource(t, 1).ok }
        add("SES4", "session", "refresh-token reuse detected, family killed") { s ->
            val rt = s.login("alice", "alice-pw").body["refresh_token"] as String
            s.refresh(rt); !s.refresh(rt).ok }
        add("SES5", "session", "cookie sets HttpOnly/Secure/SameSite") { s ->
            val sc = s.login("alice", "alice-pw").headers["Set-Cookie"] ?: ""
            listOf("HttpOnly", "Secure", "SameSite").all { sc.contains(it) } }
        add("SES6", "session", "cross-site state change rejected (CSRF)") { s ->
            !s.changePassword(userToken(s), "alice-pw", "x", reauthed = true, crossSite = true).ok }
        add("SES7", "session", "wrong-audience token rejected (no substitution)") { s ->
            val idt = s.issueAccessToken("alice", aud = "client"); !s.adminUsers(idt).ok && !s.getResource(idt, 1).ok }

        // 5. authz
        add("AZ1", "authz", "user token on admin endpoint forbidden") { !it.adminUsers(userToken(it)).ok }
        add("AZ2", "authz", "IDOR: user reads another user's resource") { !it.getResource(userToken(it), 2).ok }
        add("AZ3", "authz", "BOLA: user reads another user's video") { !it.getObject(userToken(it), "video", 102).ok }
        add("AZ4", "authz", "function-level authz holds across HTTP methods") {
            !it.adminDeleteUser(userToken(it), "bob", method = "PUT").ok }
        add("AZ5", "authz", "mass assignment of role/verified/balance ignored") { s ->
            s.register("mallory", "pw", requestedRole = "admin",
                extra = mapOf("isVerified" to true, "balance" to 999999, "role" to "admin"))
            s.userField("mallory", "role") == "user" && s.userField("mallory", "verified") == false &&
                s.userField("mallory", "balance") == 0 }
        add("AZ6", "authz", "token for disabled account rejected") { s ->
            val t = userToken(s); s.setEnabled("alice", false); !s.getResource(t, 1).ok }

        // 6. oauth
        add("OA1", "oauth", "PKCE mandatory for public clients") {
            !it.oauthAuthorize("public-app", "https://app.example/cb", codeChallenge = null, state = "s").ok }
        add("OA3", "oauth", "redirect_uri must exactly match registered") {
            !it.oauthAuthorize("public-app", "https://attacker.example/cb", Cfg.s256("v"), "s").ok }
        add("OA4", "oauth", "state required (callback CSRF)") {
            !it.oauthAuthorize("public-app", "https://app.example/cb", Cfg.s256("v"), null).ok }
        add("OA2", "oauth", "authorization code is single-use") { s ->
            val r = s.oauthAuthorize("public-app", "https://app.example/cb", Cfg.s256("v"), "s")
            if (!r.ok) return@add false
            val code = r.body["code"] as String
            s.oauthToken(code, "v", "public-app", "https://app.example/cb")
            !s.oauthToken(code, "v", "public-app", "https://app.example/cb").ok }
        add("OA5", "oauth", "code bound to its client") { s ->
            val code = s.oauthAuthorize("public-app", "https://app.example/cb", Cfg.s256("v"), "s").body["code"] as String
            !s.oauthToken(code, "v", "other-app", "https://other.example/cb").ok }

        // 7. account takeover
        add("AT1", "takeover", "reset token single-use") { s ->
            val tok = (s.resetRequest("alice@x.com").body["_link_for_test"] as String).substringAfter("token=")
            s.resetConfirm(tok, "new1"); !s.resetConfirm(tok, "new2").ok }
        add("AT3", "takeover", "reset invalidates existing sessions") { s ->
            val t = userToken(s)
            val tok = (s.resetRequest("alice@x.com").body["_link_for_test"] as String).substringAfter("token=")
            s.resetConfirm(tok, "new"); !s.getResource(t, 1).ok }
        add("AT4", "takeover", "email change requires re-verification") {
            !it.changeEmail(userToken(it), "attacker@evil.com", reverified = false).ok }

        // 8. upload
        add("UP2", "upload", "pixel-flood / oversized image rejected") { s ->
            !s.upload(userToken(s), width = 60000, height = 60000).ok }
        add("UP3", "upload", "upload endpoint rate-limited") { s ->
            val t = userToken(s)
            (0 until Cfg.UPLOAD_LIMIT + 3).map { s.upload(t, filename = "$it.mp4").status }.contains(429) }

        // 9. credential-theft mitigations
        add("CT1", "cred-theft", "sensitive action requires step-up re-auth") {
            !it.sensitiveAction(userToken(it), reauthed = false).ok }
        add("CT3", "cred-theft", "access tokens are short-lived") { s ->
            val t = s.login("alice", "alice-pw").body["access_token"] as String
            val json = Jwt.payloadUnverified(t)
            val iat = Cfg.jsonField(json, "iat")!!.toLong(); val exp = Cfg.jsonField(json, "exp")!!.toLong()
            (exp - iat) <= Cfg.ACCESS_TTL }

        // 10. info disclosure
        add("ID1", "info-leak", "errors don't leak stack traces") {
            !it.buggyEndpoint("not-an-int").body.toString().lowercase().contains("trace") }
        add("ID2", "info-leak", "reset-request response uniform (no enumeration)") { s ->
            val r1 = s.resetRequest("alice@x.com"); val r2 = s.resetRequest("ghost@x.com")
            r1.status == r2.status && r1.body["message"] == r2.body["message"] }
        add("ID3", "info-leak", "reset link ignores spoofed Host header") { s ->
            (s.resetRequest("alice@x.com", hostHeader = "attacker.com").body["_link_for_test"] as String)
                .startsWith(Cfg.BASE_URL) }

        return a
    }

    @TestFactory
    fun `secure app blocks every attack`(): List<DynamicTest> {
        val pub = newApp().publicKey()
        return catalogue(pub).map { atk ->
            DynamicTest.dynamicTest("${atk.id} [${atk.category}] ${atk.desc}") {
                assertTrue(atk.safe(newApp()), "ATTACK NOT BLOCKED: ${atk.id} — ${atk.desc}")
            }
        }
    }

    @Test
    fun `negative control — the broken build is demonstrably breakable`() {
        val pub = SecureReferenceApp().publicKey()
        val breaks = catalogue(pub).count { atk ->
            !try { atk.safe(VulnerableReferenceApp()) } catch (e: Exception) { false } }
        assertTrue(breaks > 0, "Negative control failed: broken build blocked everything.")
    }
}
