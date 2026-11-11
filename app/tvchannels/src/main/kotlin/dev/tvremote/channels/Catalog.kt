
package dev.tvremote.channels

import android.content.Context
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.Locale

/**
 * TKiPTV - Quan ly danh sach kenh IPTV.
 * Nguon kenh chinh: playlist GitHub cua TKiPTV.
 */
object Catalog {
    const val BASE = "https://iptv-org.github.io"

    const val TKIPTV_M3U =
        "https://raw.githubusercontent.com/TTK1525/KenhTV/main/alltv.m3u"

    const val BROWSER =
        "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

    private const val DAY = 24 * 3600_000L

    class Country(
        val code: String,
        val name: String,
        val flag: String
    )

    /**
     * Chi su dung playlist TKiPTV.
     * Khong gop nguon tu Providers va Categories.
     */
    fun channels(
        c: Context,
        cc: String,
        fresh: Boolean = false
    ): List<Channel> = iptv(c, cc, fresh)

    /**
     * Tai playlist TKiPTV.
     * Cache 24 gio, ho tro lam moi thu cong.
     */
    fun iptv(
        c: Context,
        cc: String,
        fresh: Boolean = false,
        progress: ((Long, Long) -> Unit)? = null
    ): List<Channel> =
        cached(
            c,
            "tkiptv-playlist.m3u",
            TKIPTV_M3U,
            fresh,
            progress,
            valid = {
                it.trimStart('\uFEFF', ' ', '\r', '\n')
                    .startsWith("#EXTM3U")
            }
        )?.let { M3u.parse(it) }.orEmpty()

    /**
     * Giu ham countries de tuong thich giao dien cu.
     */
    fun countries(c: Context): List<Country> {
        val text = cached(
            c,
            "countries.json",
            "$BASE/api/countries.json",
            false,
            valid = { it.trimStart().startsWith("[") }
        ) ?: return emptyList()

        val a = try {
            org.json.JSONArray(text)
        } catch (e: org.json.JSONException) {
            return emptyList()
        }

        val lang = Lang.locale()

        return (0 until a.length())
            .map { a.getJSONObject(it) }
            .map { o ->
                val code = o.optString("code")
                val local = Locale("", code)
                    .getDisplayCountry(lang)
                    .takeIf {
                        it.isNotEmpty() && it != code
                    }

                Country(
                    code.lowercase(),
                    local ?: o.optString("name"),
                    o.optString("flag")
                )
            }
            .sortedBy { it.name }
    }

    /**
     * Quoc gia mac dinh: Viet Nam.
     */
    fun home(): String = "vn"

    /**
     * Kiem tra cache con han.
     */
    fun young(
        c: Context,
        name: String
    ): Boolean =
        File(c.filesDir, name).let {
            it.exists() &&
                dev.tvremote.guard.Age.fresh(
                    it.lastModified(),
                    DAY
                )
        }

    /**
     * Tai du lieu va luu cache.
     * Neu mat mang, su dung ban da luu.
     */
    fun cached(
        c: Context,
        name: String,
        url: String,
        fresh: Boolean,
        progress: ((Long, Long) -> Unit)? = null,
        valid: (String) -> Boolean = { true },
        load: (() -> String?)? = null
    ): String? {
        val f = File(c.filesDir, name)

        if (!fresh && young(c, name)) {
            return f.readText()
        }

        val got = try {
            load?.invoke()
                ?: if (load == null) {
                    get(url, progress)
                } else {
                    null
                }
        } catch (e: Exception) {
            null
        }?.takeIf(valid)

        if (got != null) {
            val tmp = File(c.filesDir, "$name.tmp")

            try {
                tmp.writeText(got)
                tmp.renameTo(f)
            } catch (e: java.io.IOException) {
                tmp.delete()
            }

            return got
        }

        return if (f.exists()) {
            f.readText()
        } else {
            null
        }
    }

    /**
     * HTTP GET.
     */
    fun get(
        url: String,
        progress: ((Long, Long) -> Unit)? = null
    ): String? {
        val k = URL(url).openConnection() as HttpURLConnection

        k.connectTimeout = 8000
        k.readTimeout = 15000

        k.setRequestProperty(
            "User-Agent",
            BROWSER
        )

        if (progress != null) {
            k.setRequestProperty(
                "Accept-Encoding",
                "identity"
            )
        }

        return try {
            when (k.responseCode) {
                200 -> {
                    if (progress == null) {
                        k.inputStream
                            .bufferedReader()
                            .readText()
                    } else {
                        val total = k.getHeaderField(
                            "content-length"
                        )?.toLongOrNull() ?: -1L

                        val out =
                            java.io.ByteArrayOutputStream(
                                if (total in 1..8_000_000) {
                                    total.toInt()
                                } else {
                                    64 * 1024
                                }
                            )

                        val buf = ByteArray(16 * 1024)

                        k.inputStream.use { input ->
                            while (true) {
                                val n = input.read(buf)

                                if (n < 0) break

                                out.write(buf, 0, n)

                                progress(
                                    out.size().toLong(),
                                    total
                                )
                            }
                        }

                        out.toString("UTF-8")
                    }
                }

                404 -> ""
                else -> null
            }
        } finally {
            k.disconnect()
        }
    }
}
