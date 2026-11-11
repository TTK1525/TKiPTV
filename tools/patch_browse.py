
#!/usr/bin/env python3
"""TKiPTV Lite: safely simplify BrowseActivity without touching other files."""
from pathlib import Path
import sys

FILE = Path('app/tvchannels/src/main/kotlin/dev/tvremote/channels/BrowseActivity.kt')
if not FILE.is_file():
    sys.exit(f'Không tìm thấy {FILE}')
s = FILE.read_text(encoding='utf-8')
if 'TKIPTV_LITE_PATCH_V3' in s:
    print('Bản vá V3 đã được áp dụng; không cần chạy lại.')
    sys.exit(0)

def one(old, new='', optional=False):
    global s
    n = s.count(old)
    if optional and n == 0:
        return
    if n != 1:
        raise RuntimeError(f'Mốc không duy nhất ({n}): {old[:100]!r}')
    s = s.replace(old, new, 1)

def between(start, end, replacement=''):
    global s
    a = s.find(start)
    if a < 0 or s.find(start, a + len(start)) >= 0:
        raise RuntimeError(f'Mốc bắt đầu không duy nhất: {start!r}')
    b = s.find(end, a + len(start))
    if b < 0:
        raise RuntimeError(f'Không tìm thấy mốc kết thúc sau mốc bắt đầu: {end!r}')
    s = s[:a] + replacement + s[b:]

# Disable legacy update checks and country selection.
one('        upd.check({ askUpdate(it) }, { updating(it) })\n')
one('        state.add(TvUi.button(this, getString(R.string.country)) { countries() })\n')
one('        cc = countryOf(intent) ?: Store.country(this)', '        cc = "vn"')
one('        countryOf(i)?.takeIf { it != cc }?.let { cc = it; group = ALL; homeMode = true; load(false) }\n')
one('        i.getStringExtra(QUERY)?.let { group = SEARCH; homeMode = false; others = emptyList(); otherState = IDLE; find.setText(it); buildRail(); filter() }', '        i.getStringExtra(QUERY)?.let { group = SEARCH; homeMode = false; find.setText(it); buildRail(); filter() }')
one('override fun afterTextChanged(s: Editable?) { if (group == SEARCH) scheduleOthers(); filter() }', 'override fun afterTextChanged(s: Editable?) { filter() }')

# Drop network-backed international search state and functions.
between('    private var others: List<List<Channel>>', '    override fun onCreate(b: Bundle?) {')
between('    private fun countryOf(i: Intent?)', '    private fun columns()')
between('    private fun scheduleOthers() {', '    private fun say(s: String, again: Boolean)')
one('        homeMode = false; group = SEARCH; others = emptyList(); otherState = IDLE', '        homeMode = false; group = SEARCH')
one('            GlobalIndex.release(); main.removeCallbacks(globalRun); gseq++', '            // Tìm kiếm chỉ trong playlist TKiPTV')
one('searching && otherState == DONE && shown.isEmpty()', 'searching && q.isNotEmpty() && shown.isEmpty()')
one('    override fun onStop() { GlobalIndex.release(); super.onStop() }', '    override fun onStop() { super.onStop() }')
one('main.removeCallbacks(globalRun); searcher.shutdownNow(); GlobalIndex.release(); ', '')

# Load only the default TKiPTV M3U, retaining manually added lists.
between('    private fun load(fresh: Boolean) {', '    private fun progressWords(pct: Int)', '''    // TKIPTV_LITE_PATCH_V3
    private fun load(fresh: Boolean) {
        cc = "vn"
        Store.setCountry(this, cc)
        if (fresh && isList(group)) loadList(group.removePrefix(PL), true)
        all = emptyList()
        failed = false
        loading = true
        catRes = null
        countryName = "TKiPTV"
        chrome()
        io.execute {
            var previous = -2
            val channels = Catalog.iptv(this, cc, fresh) { got, total ->
                val pct = if (total > 0) (got * 100L / total).toInt().coerceIn(0, 100) else -1
                if (pct != previous) {
                    previous = pct
                    main.post {
                        if (!isDestroyed && loading) state.loading(progressWords(pct), pct)
                    }
                }
            }
            main.post {
                if (isDestroyed) return@post
                all = channels.byChannel()
                failed = channels.isEmpty()
                loading = false
                countryName = "TKiPTV"
                if (mine(group) == null && !isList(group) && group != ALL &&
                    group != SEARCH && all.none { it.first().group == group }) group = ALL
                buildRail()
                filter()
                if (!find.hasFocus()) grid.post {
                    (grid.getChildAt(0) ?: rail.getChildAt(0))?.requestFocus()
                }
            }
        }
    }

''')

# Replace only the search branch in filter; the end marker is searched AFTER the start.
between('            searching -> {', '            gid != null -> live(Store.channels(this, gid).byChannel())', '''            searching -> {
                if (q.isEmpty()) emptyList() else all.mapNotNull { ch ->
                    GlobalIndex.rank(Find.fold(ch.first().name), q)?.let { it to ch }
                }.sortedBy { it.first }.map { it.second }
            }
''')

# Keep language and refresh in Settings; no country chooser.
between('    private fun settings() = listOf(', '    /** Everything that is not "watch a channel"', '''    private fun settings() = listOf(
        Tool(R.drawable.ic_subtitle, getString(R.string.lang, langName(Lang.pref(this)))) { languages() },
        Tool(R.drawable.ic_refresh, getString(R.string.refresh)) { load(true) }
    )

''')
between('    private fun countries() {', '    override fun onKeyDown(k: Int, e: KeyEvent): Boolean {')
between('    private val upd by lazy', '    private fun groupsFor(ch: List<Channel>)')

# Remove reminder menu entries and dialog, retaining the EPG guide itself.
between('        val rem = Reminders.all(this).size', '        for (g in Store.groups(this))')
between('        val rem = Reminders.all(this).size', '        for (t in listOfNotNull(newGroup(), addLink()))')
between('    private fun remindList() {', '    private fun groupMenu(gid: String)')

# Strip imports that would otherwise refer to deleted code.
for line in ('import dev.tvremote.update.Release\n', 'import dev.tvremote.update.SelfUpdate\n'):
    one(line, optional=True)

# Check that no removed function is still called.
for forbidden in ('Providers.merge(', 'Providers.warm(', 'Categories.refresh(',
                  'upd.check(', 'countries()', 'scheduleOthers()',
                  'searchOthers()', 'remindList()', 'otherState', 'globalRun'):
    if forbidden in s:
        raise RuntimeError(f'Còn tham chiếu cần kiểm tra: {forbidden}')

FILE.write_text(s, encoding='utf-8')
print('Đã áp dụng bản vá TKiPTV Lite V3 cho BrowseActivity.kt.')
print('Chưa xác nhận Gradle build; hãy chạy workflow build APK tiếp theo.')
