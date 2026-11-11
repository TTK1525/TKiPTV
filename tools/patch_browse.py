
#!/usr/bin/env python3
# TKiPTV Lite - BrowseActivity patch
# Chay qua GitHub Actions
# Chi sua BrowseActivity.kt

from pathlib import Path
import re
import sys

FILE = Path(
    "app/tvchannels/src/main/kotlin/"
    "dev/tvremote/channels/BrowseActivity.kt"
)

if not FILE.is_file():
    sys.exit(f"Khong tim thay file: {FILE}")

source = FILE.read_text(encoding="utf-8")
s = source

if "TKIPTV_LITE_PATCH_V2" in s:
    print("TKiPTV Lite da duoc ap dung.")
    sys.exit(0)


def replace_once(old, new, required=True):
    global s
    count = s.count(old)
    if count == 0 and not required:
        return
    if count != 1:
        raise RuntimeError(
            f"Khong tim thay hoac trung lap: {old[:100]!r}"
        )
    s = s.replace(old, new, 1)


def replace_between(start, end, new=""):
    global s
    if s.count(start) != 1 or s.count(end) != 1:
        raise RuntimeError(
            f"Khong tim thay moc: {start[:75]!r} / {end[:75]!r}"
        )
    a = s.index(start)
    b = s.index(end)
    if b <= a:
        raise RuntimeError("Thu tu moc khong hop le")
    s = s[:a] + new + s[b:]


# 1. Tat tim kiem kenh quoc te
replace_once(
    "if (group == SEARCH) scheduleOthers(); filter()",
    "filter()"
)

# 2. Chi su dung Viet Nam
replace_once(
    "cc = countryOf(intent) ?: Store.country(this)",
    'cc = "vn"'
)

replace_once(
    "countryOf(i)?.takeIf { it != cc }?.let { cc = it; group = ALL; homeMode = true; load(false) }",
    "",
)

# 3. Bo nut chon quoc gia trong trang loi
replace_once(
    '        state.add(TvUi.button(this, getString(R.string.country)) { countries() })\n',
    ""
)

# 4. Tat cap nhat APK tu may chu cu
replace_once(
    "        upd.check({ askUpdate(it) }, { updating(it) })",
    ""
)

replace_between(
    "    private val upd by lazy",
    "    private fun groupsFor(ch: List<Channel>)",
    ""
)

# 5. Bo giao dien chon quoc gia
replace_between(
    "    private fun countries() {",
    "    override fun onKeyDown(k: Int, e: KeyEvent): Boolean {",
    ""
)

# 6. Chi giu ngon ngu va lam moi
replace_between(
    "    private fun settings() = listOf(",
    "    /** Everything that is not",
    """    private fun settings() = listOf(
        Tool(
            R.drawable.ic_subtitle,
            getString(R.string.lang, langName(Lang.pref(this)))
        ) { languages() },
        Tool(
            R.drawable.ic_refresh,
            getString(R.string.refresh)
        ) { load(true) }
    )

"""
)

# 7. Nap kenh tu playlist TKiPTV
# Khong phu thuoc vao chu thich Unicode.
replace_between(
    "    private fun load(fresh: Boolean) {",
    "    private fun progressWords(pct: Int)",
    '''    // TKIPTV_LITE_PATCH_V2
    private fun load(fresh: Boolean) {
        cc = "vn"
        Store.setCountry(this, cc)

        if (fresh && isList(group)) {
            loadList(group.removePrefix(PL), true)
        }

        all = emptyList()
        failed = false
        loading = true
        catRes = null
        countryName = "TKiPTV"
        chrome()

        io.execute {
            var previous = -2

            val channels = Catalog.iptv(
                this,
                cc,
                fresh
            ) { got, total ->

                val pct = if (total > 0) {
                    (got * 100L / total)
                        .toInt()
                        .coerceIn(0, 100)
                } else {
                    -1
                }

                if (pct != previous) {
                    previous = pct
                    main.post {
                        if (!isDestroyed && loading) {
                            state.loading(
                                progressWords(pct),
                                pct
                            )
                        }
                    }
                }
            }

            main.post {
                if (isDestroyed) return@post

                all = channels.byChannel()
                failed = channels.isEmpty()
                loading = false
                countryName = "TKiPTV"

                if (
                    mine(group) == null &&
                    !isList(group) &&
                    group != ALL &&
                    group != SEARCH &&
                    all.none {
                        it.first().group == group
                    }
                ) {
                    group = ALL
                }

                buildRail()
                filter()

                if (!find.hasFocus()) {
                    grid.post {
                        (
                            grid.getChildAt(0)
                                ?: rail.getChildAt(0)
                        )?.requestFocus()
                    }
                }
            }
        }
    }

'''
)

# 8. Tim kiem trong danh sach TKiPTV
# Khong truy van GlobalIndex.
replace_between(
    "            searching -> {",
    "            gid != null ->",
    """            searching -> {
                if (q.isEmpty()) {
                    emptyList()
                } else {
                    all.mapNotNull { ch ->
                        GlobalIndex.rank(
                            Find.fold(ch.first().name),
                            q
                        )?.let { rank ->
                            rank to ch
                        }
                    }
                    .sortedBy { it.first }
                    .map { it.second }
                }
            }
"""
)

# 9. Tat tim kiem kenh quoc te trong giao dien
replace_once(
    "        homeMode = false; group = SEARCH; others = emptyList(); otherState = IDLE",
    "        homeMode = false; group = SEARCH"
)

replace_once(
    "group = SEARCH; homeMode = false; others = emptyList(); otherState = IDLE; find.setText(it); buildRail(); filter()",
    "group = SEARCH; homeMode = false; find.setText(it); buildRail(); filter()"
)

replace_once(
    "            GlobalIndex.release(); main.removeCallbacks(globalRun); gseq++",
    "            // Tim kiem noi bo"
)

# 10. Bo nhac lich trong menu
replace_between(
    "        val rem = Reminders.all(this).size",
    "        for (g in Store.groups(this))",
    ""
)

replace_between(
    "        val rem = Reminders.all(this).size",
    "        for (t in listOfNotNull(newGroup(), addLink()))",
    ""
)

replace_between(
    "    private fun remindList() {",
    "    private fun groupMenu(gid: String)",
    ""
)

# 11. Khong chay tim kiem quoc te ngam
replace_between(
    "    private fun scheduleOthers() {",
    "    private fun say(s: String, again: Boolean)",
    ""
)

# 12. Don cac bien tim kiem quoc te
replace_between(
    "    private var others: List<List<Channel>>",
    "    override fun onCreate(b: Bundle?) {",
    ""
)

# 13. Sua dieu kien thong bao khong tim thay
replace_once(
    "searching && otherState == DONE && shown.isEmpty()",
    "searching && q.isNotEmpty() && shown.isEmpty()"
)

# 14. Don callback khong con su dung
replace_once(
    "    override fun onStop() { GlobalIndex.release(); super.onStop() }",
    "    override fun onStop() { super.onStop() }"
)

replace_once(
    "main.removeCallbacks(globalRun); searcher.shutdownNow(); GlobalIndex.release(); ",
    ""
)

# 15. Giu cac thanh phan khac de tranh loi tham chieu.
# Xoa import khong su dung khong bat buoc voi Kotlin.

# Kiem tra cac ham cu khong con duoc goi.
for forbidden in [
    "Providers.merge(",
    "Providers.warm(",
    "Categories.refresh(",
    "upd.check(",
    "countries()",
    "scheduleOthers()",
    "searchOthers()",
    "remindList()",
]:
    if forbidden in s:
        raise RuntimeError(
            f"Con tham chieu can xu ly: {forbidden}"
        )

# Chi ghi file sau khi moi buoc thanh cong.
FILE.write_text(s, encoding="utf-8")

print("================================")
print("TKiPTV Lite Browse patch V2")
print("Trang thai: THANH CONG")
print("Da tat nguon IPTV-org tren BrowseActivity")
print("Da tat giao dien chon quoc gia")
print("Da tat cap nhat APK cu")
print("Da tat tim kiem quoc te")
print("Da bo nhac lich khoi BrowseActivity")
print("Giu yeu thich, EPG va M3U thu cong")
print("================================")
