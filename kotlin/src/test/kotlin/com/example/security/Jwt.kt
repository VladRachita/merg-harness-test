package com.example.security

import java.security.KeyPair
import java.security.KeyPairGenerator
import java.security.PrivateKey
import java.security.PublicKey
import java.security.Signature
import java.util.Base64
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec

/** JDK-only JWT helpers (no Nimbus/Maven dep needed to compile). Your real app
 *  uses Spring Security's JwtDecoder; this backs the reference app and lets the
 *  catalogue hand-roll attacker tokens the way a real attacker would. */
object Jwt {
    private val enc = Base64.getUrlEncoder().withoutPadding()
    private val dec = Base64.getUrlDecoder()

    fun rsa(): KeyPair = KeyPairGenerator.getInstance("RSA").apply { initialize(2048) }.genKeyPair()

    private fun seg(headerJson: String, payloadJson: String) =
        "${enc.encodeToString(headerJson.toByteArray())}.${enc.encodeToString(payloadJson.toByteArray())}"

    fun signRs256(headerJson: String, payloadJson: String, priv: PrivateKey): String {
        val s = seg(headerJson, payloadJson)
        val sig = Signature.getInstance("SHA256withRSA").run { initSign(priv); update(s.toByteArray()); sign() }
        return "$s.${enc.encodeToString(sig)}"
    }

    /** RS256 only. Returns payload JSON if the signature verifies, else null. */
    fun verifyRs256(token: String, pub: PublicKey): String? {
        val p = token.split(".")
        if (p.size != 3 || p[2].isEmpty()) return null
        val header = String(dec.decode(p[0]))
        if (!Regex("\"alg\"\\s*:\\s*\"RS256\"").containsMatchIn(header)) return null  // PIN alg
        val ok = try {
            Signature.getInstance("SHA256withRSA").run {
                initVerify(pub); update("${p[0]}.${p[1]}".toByteArray()); verify(dec.decode(p[2]))
            }
        } catch (e: Exception) { false }
        return if (ok) String(dec.decode(p[1])) else null
    }

    fun payloadUnverified(token: String): String =
        String(dec.decode(token.split(".").getOrElse(1) { "" }.padBase64()))

    // attacker tooling (bypasses library guard rails)
    fun forgeNone(payloadJson: String) = seg("{\"alg\":\"none\",\"typ\":\"JWT\"}", payloadJson) + "."
    fun forgeHs256(payloadJson: String, secret: ByteArray): String {
        val s = seg("{\"alg\":\"HS256\",\"typ\":\"JWT\"}", payloadJson)
        val mac = Mac.getInstance("HmacSHA256").apply { init(SecretKeySpec(secret, "HmacSHA256")) }
        return "$s.${enc.encodeToString(mac.doFinal(s.toByteArray()))}"
    }

    private fun String.padBase64(): ByteArray {
        val s = this + "=".repeat((4 - length % 4) % 4)
        return Base64.getUrlDecoder().decode(s)
    }
}
