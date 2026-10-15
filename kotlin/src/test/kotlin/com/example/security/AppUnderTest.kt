package com.example.security

/**
 * THE SEAM. Implement this against YOUR app — ideally by backing each method with
 * a Spring `WebTestClient` call through your real security filter chain, so the
 * harness exercises your actual filters, converters and @PreAuthorize rules.
 *
 * Every method returns a [Resp] (status + headers + body) so the catalogue can
 * assert on status codes, security headers and returned data uniformly — exactly
 * what you'd read off an HTTP response.
 *
 * A reference implementation (SecureReferenceApp) is provided so the suite runs
 * out of the box and documents the behaviour your app must match. Replace
 * `newApp()` in AppSecurityHarnessTest with an adapter over your app.
 */
interface AppUnderTest {
    // --- auth ---
    fun login(username: String, password: String,
              sourceIp: String = "203.0.113.9", xff: String? = null,
              otpOk: Boolean = true, prevSession: String? = null): Resp
    fun logout(token: String): Resp
    fun refresh(refreshToken: String): Resp
    fun register(username: String, password: String,
                 requestedRole: String? = null, extra: Map<String, Any?> = emptyMap()): Resp

    // --- protected resources ---
    fun getResource(token: String, ownerId: Int): Resp
    fun getObject(token: String, kind: String, objId: Int): Resp
    fun adminUsers(token: String): Resp
    fun adminDeleteUser(token: String, target: String, method: String = "DELETE"): Resp

    // --- state-changing ---
    fun changePassword(token: String, old: String, new: String,
                       reauthed: Boolean = false, csrfOk: Boolean = true,
                       crossSite: Boolean = false): Resp
    fun sensitiveAction(token: String, reauthed: Boolean = false,
                        csrfOk: Boolean = true, crossSite: Boolean = false): Resp
    fun changeEmail(token: String, newEmail: String, reverified: Boolean = false): Resp

    // --- media / upload ---
    fun getMedia(path: String): Resp
    fun upload(token: String, fetchUrl: String? = null, width: Int? = null,
               height: Int? = null, filename: String = "v.mp4"): Resp

    // --- password reset ---
    fun resetRequest(email: String, hostHeader: String = "app.example"): Resp
    fun resetConfirm(token: String, newPw: String): Resp

    // --- OAuth2 / PKCE ---
    fun oauthAuthorize(clientId: String, redirectUri: String,
                       codeChallenge: String? = null, state: String? = null): Resp
    fun oauthToken(code: String, codeVerifier: String?, clientId: String, redirectUri: String): Resp

    // --- misc ---
    fun buggyEndpoint(payload: String): Resp

    // --- test hooks ---
    fun issueAccessToken(username: String, aud: String = "api"): String
    fun setEnabled(username: String, enabled: Boolean)
    fun userField(username: String, field: String): Any?
    fun publicKey(): ByteArray
}

data class Resp(
    val status: Int,
    val headers: Map<String, String> = emptyMap(),
    val body: Map<String, Any?> = emptyMap(),
) {
    val ok: Boolean get() = status in 200..299
}
